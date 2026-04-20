"""
MSPgen.py:

Generates a Project Planner (like Microsoft Project or ProjectLibre) .xml file from the OpenAI species context module.

1. Parses species context for dates/seasons (needs to be checked to see it works with OpenAI)
2. Writes these restricted times into a .xml file
3. Can use .XML file in ProjectLibre or MicrosoftProject to schedule construction times around endangered species constraints

"""

import io
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Dict, List, Optional
import calendar

# temporary critical windows until parsing part is finished
CRITICAL_WINDOWS = [
    {"name": "Little Blue Heron", "start_month": 4, "start_day": 1, "end_month": 8, "end_day": 31},
    {"name": "Black-crowned Night Heron", "start_month": 6, "start_day": 1, "end_month": 6, "end_day": 31},
    {"name": "Snowy Egret", "start_month": 1, "start_day": 8, "end_month": 10, "end_day": 31},
]

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# Function that creates an XML child element under the parent,
# sets its text content, and returns it. Used to avoid repeating
# ET.SubElement() + .text = ... throughout the code
def sub(parent, tag, text=""):
    el = ET.SubElement(parent, tag)
    el.text = str(text)
    return el

# Converts the XML element tree into a properly formatted XML string.
# ET normally can't add the Microsoft Project namespace to <Project>,
# so this function handles that manually with a string replacement
def serialize(root):
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    buf = io.BytesIO()
    tree.write(buf, xml_declaration=True, encoding="utf-8")
    s = buf.getvalue().decode("utf-8")
    s = s.replace("<Project>", '<Project xmlns="http://schemas.microsoft.com/project">', 1)
    return s

# change the duration between start and finish to working days as ProjectLibre uses working days rather than calendar days
def working_days(start, finish):
    count = 0
    current = start
    while current <= finish:
        if current.weekday() < 5:  # Mon-Fri
            count += 1
        current += timedelta(days=1)
    return count


# Builds a single <Task> XML element and appends it to the <Tasks> block
# Each task represents one species' critical window on the Gantt chart
def buildTask(tasks, uid, name, start, finish, notes="", summary=False):
    t = ET.SubElement(tasks, "Task")

    duration_days = working_days(start, finish)

    for tag, val in [
        ("UID", str(uid)),  # Unique numeric ID for this task (used internally by ProjectLibre)
        ("ID", str(uid)),   # Display row number in the task list
        ("Name", name),     # Task name shown in the Name column

        # Task dates in ISO format
        ("Start", start.strftime("%Y-%m-%dT00:00:00")),     
        ("Finish", finish.strftime("%Y-%m-%dT17:00:00")),

        # How long a task takes
        ("Duration", f"P{duration_days}DT0H0M0S"),
        ("DurationFormat", "39"),       # 39 = working days unit in MS Project XML

        ("ConstraintType", "2"),  # Must Start On
        ("ConstraintDate", start.strftime("%Y-%m-%dT08:00:00")),

        ("Manual", "1"),    # 1 = Manually scheduled (ProjectLibre won't auto-move this task)

        ("Summary", "1" if summary else "0"),   # 1 = render as a summary/parent bar, 0 = regular task
    ]:
        sub(t, tag, val)


    if notes:
        sub(t, "Notes", notes)

    return t

def generateXML(
    critical_windows: List[Dict],
    project_name: str = "Environmental Constraints",
    project_start: Optional[str] = None,
    ) -> str:

    start_date = date.fromisoformat(project_start) 
    year = start_date.year

    # Compute finish date = latest window end
    project_finish = max(
        date(year, w["end_month"], min(w["end_day"], calendar.monthrange(year, w["end_month"])[1]))
        for w in critical_windows
    )

    root = ET.Element("Project")

    for tag, val in [
        ("SaveVersion", "14"),
        ("Name", project_name),
        ("StartDate", start_date.strftime("%Y-%m-%dT08:00:00")),
        ("FinishDate", project_finish.strftime("%Y-%m-%dT17:00:00")),
        ("MinutesPerDay", "480"),
        ("MinutesPerWeek", "2400"),
    ]:
        sub(root, tag, val)

    tasks = ET.SubElement(root, "Tasks")
    uid=1

    for w in critical_windows:
        s = date(year, w["start_month"], w["start_day"])

        last_day = calendar.monthrange(year, w["end_month"])[1]
        e = date(year, w["end_month"], min(w["end_day"], last_day))

        if e < s:
            e = date(year + 1, w["end_month"], min(w["end_day"], last_day))

        species = w["name"].split("(")[0].strip()

        buildTask(
            tasks,
            uid=uid,
            name=f"[INFO] {species}",
            start=s,
            finish=e,
            notes=(
                f"Species: {species}\n"
                f"Restricted Period:\n"
                f"{MONTH_NAMES[w['start_month']]} {w['start_day']} "
                f"to {MONTH_NAMES[w['end_month']]} {w['end_day']}\n\n"
                f"Seasonal Conerns:\n{w.get('seasonal_concerns', '')}\n"
            ),
        )

        uid += 1

    ET.SubElement(root, "Resources")
    ET.SubElement(root, "Assignments")

    return serialize(root)

def saveXML(critical_windows: List[Dict], output_path: str):
    today = str(date.today())
    xml = generateXML(critical_windows, project_start=today)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml)

    return output_path