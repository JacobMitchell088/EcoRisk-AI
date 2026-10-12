import { useEffect, useId, useRef, useState } from "react";
import { InfoIcon } from "./Icons";

// Inline "i" button that explains a nearby control. The popover anchors to the
// nearest positioned ancestor (give it the `tip-anchor` class) so it spans that
// row instead of overflowing a narrow panel.
export default function InfoTip({ title, children }) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);
  const buttonRef = useRef(null);
  const popoverId = useId();

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <span className="infotip" ref={wrapperRef}>
      <button
        ref={buttonRef}
        type="button"
        className="infotip-btn"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={`About ${title.toLowerCase()}`}
        aria-expanded={open}
        aria-controls={popoverId}
      >
        <InfoIcon size={17} />
      </button>

      <span className="infotip-pop" id={popoverId} role="note" hidden={!open}>
        <span className="infotip-title">{title}</span>
        <span className="infotip-body">{children}</span>
      </span>
    </span>
  );
}
