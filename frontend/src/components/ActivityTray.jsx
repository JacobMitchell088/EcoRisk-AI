import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "react-hot-toast";
import { BellIcon } from "./Icons";

const TYPE_LABELS = { success: "Done", error: "Problem", info: "Update" };

export default function ActivityTray({ items, onMarkRead, onClear }) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);
  const buttonRef = useRef(null);
  const unread = items.filter((item) => !item.read).length;

  const close = useCallback(() => {
    setOpen(false);
    onMarkRead();
  }, [onMarkRead]);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) close();
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        close();
        buttonRef.current?.focus();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, close]);

  return (
    <div className="tray" ref={wrapperRef}>
      <button
        ref={buttonRef}
        type="button"
        className="icon-btn"
        onClick={() => {
          if (open) return close();
          // The tray already lists every message, so clear toasts that would overlap it.
          toast.dismiss();
          setOpen(true);
        }}
        aria-expanded={open}
        aria-controls="activity-tray"
        aria-label={unread ? `Activity, ${unread} new` : "Activity"}
      >
        <BellIcon size={20} />
        {unread > 0 && (
          <span className="badge" aria-hidden="true">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      <div className="tray-pop" id="activity-tray" role="region" aria-label="Activity" hidden={!open}>
        <div className="tray-head">
          <h2 className="tray-title">Activity</h2>
          {items.length > 0 && (
            <button type="button" className="link-btn" onClick={onClear}>
              Clear all
            </button>
          )}
        </div>

        {items.length === 0 ? (
          <p className="tray-empty">
            Nothing here yet. Address searches, screenings, and any problems will be listed here.
          </p>
        ) : (
          <ul className="tray-list">
            {items.map((item) => (
              <li key={item.id} className={`tray-item tray-item--${item.type}${item.read ? "" : " is-new"}`}>
                <span className="tray-dot" aria-hidden="true" />
                <div className="tray-text">
                  <span className="visually-hidden">{TYPE_LABELS[item.type] || "Update"}: </span>
                  <p className="tray-message">{item.message}</p>
                  <time className="tray-time" dateTime={item.time.toISOString()}>
                    {item.time.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                  </time>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
