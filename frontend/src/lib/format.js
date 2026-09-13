export const GUIDANCE_SECTIONS = [
  { key: "overview", label: "About this species" },
  { key: "seasonal_concerns", label: "When it's most sensitive" },
  { key: "disruptive_activities", label: "Activities that disturb it" },
  { key: "recommendation", label: "Suggested timing" },
];

export function formatCooldown(seconds) {
  if (seconds >= 3600) {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }

  if (seconds >= 60) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }

  return `${seconds}s`;
}

export function formatCoords(lat, lon) {
  const latNum = Number(lat);
  const lonNum = Number(lon);
  if (lat === "" || lon === "" || !Number.isFinite(latNum) || !Number.isFinite(lonNum)) return "";
  const ns = latNum >= 0 ? "N" : "S";
  const ew = lonNum >= 0 ? "E" : "W";
  return `${Math.abs(latNum).toFixed(3)}° ${ns}, ${Math.abs(lonNum).toFixed(3)}° ${ew}`;
}

export function formatClock(unixSeconds) {
  if (!unixSeconds) return "";
  return new Date(unixSeconds * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function milesLabel(radius) {
  const n = Number(radius);
  return `${n} ${n === 1 ? "mile" : "miles"}`;
}

export function verdictCopy(count, radius, yearStart) {
  const area = `within ${milesLabel(radius)} of this site since ${yearStart}`;
  if (count === 0) {
    return {
      title: "No protected species recorded nearby",
      text: `No species on the Illinois endangered and threatened list have sightings on record ${area}.`,
    };
  }
  if (count === 1) {
    return {
      title: "1 protected species recorded nearby",
      text: `This species is on the Illinois endangered and threatened list and has sightings on record ${area}. Review it before planning site work.`,
    };
  }
  return {
    title: `${count} protected species recorded nearby`,
    text: `These species are on the Illinois endangered and threatened list and have sightings on record ${area}. Review each one before planning site work.`,
  };
}
