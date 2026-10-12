import { useEffect, useRef, useState } from "react";

const STORAGE_KEY = "ecorisk.panelWidths";
const DEFAULT_WIDTHS = { steps: 420, report: 540 };
const MIN_WIDTH = 340;
const MIN_MAP_WIDTH = 360;
const KEY_STEP = 24;

function readStoredWidths() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

// Width of the left panel, adjustable by dragging its edge or with the arrow keys.
// The steps and the report remember their own widths, so a report can be read
// wide without leaving the step form stretched.
export default function usePanelWidth(view) {
  const layout = view === "report" ? "report" : "steps";
  const [customWidths, setCustomWidths] = useState(readStoredWidths);
  const [viewportWidth, setViewportWidth] = useState(() => window.innerWidth);
  const [resizing, setResizing] = useState(false);
  const dragRef = useRef(null);

  useEffect(() => {
    const handleResize = () => setViewportWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Save once a drag ends rather than on every pointer move.
  useEffect(() => {
    if (resizing) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(customWidths));
    } catch {
      /* Storage unavailable (private window); widths reset next visit. */
    }
  }, [customWidths, resizing]);

  const maxWidth = Math.max(MIN_WIDTH, viewportWidth - MIN_MAP_WIDTH);
  const clamp = (value) => Math.round(Math.min(maxWidth, Math.max(MIN_WIDTH, value)));

  const stepsWidth = clamp(customWidths.steps ?? DEFAULT_WIDTHS.steps);
  const width =
    layout === "report"
      ? clamp(customWidths.report ?? Math.max(DEFAULT_WIDTHS.report, stepsWidth))
      : stepsWidth;

  function setWidth(value) {
    setCustomWidths((prev) => ({ ...prev, [layout]: clamp(value) }));
  }

  function handlePointerDown(event) {
    if (event.button !== 0) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { startX: event.clientX, startWidth: width };
    setResizing(true);
  }

  function handlePointerMove(event) {
    if (!dragRef.current) return;
    setWidth(dragRef.current.startWidth + event.clientX - dragRef.current.startX);
  }

  function handlePointerEnd(event) {
    if (!dragRef.current) return;
    dragRef.current = null;
    setResizing(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function handleKeyDown(event) {
    const step = event.shiftKey ? KEY_STEP * 4 : KEY_STEP;
    const next = {
      ArrowLeft: width - step,
      ArrowRight: width + step,
      Home: MIN_WIDTH,
      End: maxWidth,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    setWidth(next);
  }

  function reset() {
    setCustomWidths((prev) => {
      const next = { ...prev };
      delete next[layout];
      return next;
    });
  }

  return {
    width,
    resizing,
    handleProps: {
      role: "separator",
      tabIndex: 0,
      "aria-orientation": "vertical",
      "aria-label": "Resize panel",
      "aria-valuemin": MIN_WIDTH,
      "aria-valuemax": maxWidth,
      "aria-valuenow": width,
      "aria-valuetext": `${width} pixels wide`,
      title: "Drag to resize. Double-click to reset.",
      onPointerDown: handlePointerDown,
      onPointerMove: handlePointerMove,
      onPointerUp: handlePointerEnd,
      onPointerCancel: handlePointerEnd,
      onKeyDown: handleKeyDown,
      onDoubleClick: reset,
    },
  };
}
