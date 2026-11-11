import { useEffect, useRef } from "react";
import { CloseIcon, GitHubIcon, LinkedInIcon } from "./components/Icons";
import { PROJECT_BLURB, REPO_URL, TEAM } from "./lib/team";

const FOCUSABLE = 'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])';

export default function AboutDialog({ open, onClose }) {
  const sheetRef = useRef(null);
  const closeRef = useRef(null);

  // Open: move focus in, trap Tab, close on Escape. Close: hand focus back.
  useEffect(() => {
    if (!open) return;

    const returnFocusTo = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusTimer = setTimeout(() => closeRef.current?.focus(), 80);

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !sheetRef.current) return;
      const focusable = [...sheetRef.current.querySelectorAll(FOCUSABLE)];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      clearTimeout(focusTimer);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      returnFocusTo?.focus?.();
    };
  }, [open, onClose]);

  return (
    <div className="feedback" data-open={open} inert={!open}>
      <div className="sheet-scrim" onClick={onClose} aria-hidden="true" />

      <aside ref={sheetRef} className="sheet" role="dialog" aria-modal="true" aria-labelledby="about-title">
        <header className="sheet-head">
          <div>
            <h2 id="about-title" className="sheet-title">
              About EcoRisk AI
            </h2>
            <p className="sheet-lede">{PROJECT_BLURB}</p>
          </div>
          <button ref={closeRef} type="button" className="icon-btn" onClick={onClose} aria-label="Close about">
            <CloseIcon size={20} />
          </button>
        </header>

        <div className="sheet-body">
          <h3 className="about-heading">Contributors</h3>

          <ul className="about-members">
            {TEAM.map((member) => (
              <li key={member.name} className="about-member">
                <span className="about-avatar" aria-hidden="true">
                  {member.name.split(" ").map((part) => part[0]).join("")}
                </span>
                <div className="about-info">
                  <p className="about-name">{member.name}</p>
                  <p className="about-role">{member.role}</p>
                </div>
                <a
                  className="about-link about-link--pill"
                  href={member.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`${member.name} on LinkedIn`}
                >
                  <LinkedInIcon size={18} /> LinkedIn
                </a>
              </li>
            ))}
          </ul>

          <a className="about-link" href={REPO_URL} target="_blank" rel="noopener noreferrer">
            <GitHubIcon size={18} /> View the project on GitHub
          </a>
        </div>
      </aside>
    </div>
  );
}
