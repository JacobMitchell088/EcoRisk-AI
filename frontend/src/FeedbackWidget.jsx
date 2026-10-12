import { useEffect, useRef, useState } from "react";
import { toast } from "react-hot-toast";
import useTurnstile from "./lib/useTurnstile";
import { backendUrl, isNetworkError, readErrorMessage } from "./lib/api";
import { AlertIcon, CloseIcon, StarIcon } from "./components/Icons";

const emptyForm = { title: "", body: "", email: "", rating: 0 };
const RATING_WORDS = ["No rating", "Poor", "Fair", "Good", "Very good", "Excellent"];
const FOCUSABLE = 'button:not([disabled]), input, textarea, [href], [tabindex]:not([tabindex="-1"])';

export default function FeedbackWidget({ open, onClose, onNotify }) {
  const [form, setForm] = useState(emptyForm);
  const [hoverRating, setHoverRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState("");

  const { containerRef, prepare, getToken, reset } = useTurnstile();
  const sheetRef = useRef(null);
  const titleRef = useRef(null);

  // Open: render verification, move focus in, trap Tab, close on Escape.
  // Close: hand focus back to whatever opened the sheet.
  useEffect(() => {
    if (!open) return;

    const returnFocusTo = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    toast.dismiss();
    prepare();
    const focusTimer = setTimeout(() => titleRef.current?.focus(), 80);

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
  }, [open, onClose, prepare]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) setFieldErrors((prev) => ({ ...prev, [name]: "" }));
  }

  function validate() {
    const errors = {};
    if (form.title.trim().length < 3) errors.title = "Add a short title of at least 3 characters.";
    if (form.body.trim().length < 5) errors.body = "Add a few more words so we understand your feedback.";
    const email = form.email.trim();
    if (email && !/^\S+@\S+\.\S+$/.test(email)) errors.email = "Enter a valid email address, or leave this blank.";
    return errors;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError("");

    const errors = validate();
    setFieldErrors(errors);
    const firstInvalid = Object.keys(errors)[0];
    if (firstInvalid) {
      sheetRef.current?.querySelector(`[name="${firstInvalid}"]`)?.focus();
      return;
    }

    if (!backendUrl) {
      setSubmitError("Feedback is unavailable because the service isn't configured.");
      return;
    }

    setSubmitting(true);
    try {
      const token = await getToken();
      const response = await fetch(`${backendUrl}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.title.trim(),
          body: form.body.trim(),
          contact_email: form.email.trim() || null,
          rating: form.rating > 0 ? form.rating : null,
          captcha_token: token,
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Your feedback didn't send. Try again in a moment."));
      }

      onNotify("Feedback sent. Thank you for helping improve EcoRisk AI.", "success");
      setForm(emptyForm);
      setFieldErrors({});
      reset();
      onClose();
    } catch (err) {
      const message = isNetworkError(err)
        ? "Couldn't reach the feedback service. Check your connection and try again."
        : err.message || "Your feedback didn't send. Try again in a moment.";
      setSubmitError(message);
      onNotify(message, "error", { toast: false });
    } finally {
      setSubmitting(false);
    }
  }

  const shownRating = hoverRating || form.rating;

  return (
    <div className="feedback" data-open={open} inert={!open}>
      <div className="sheet-scrim" onClick={onClose} aria-hidden="true" />

      <aside
        ref={sheetRef}
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="feedback-title"
      >
        <header className="sheet-head">
          <div>
            <h2 id="feedback-title" className="sheet-title">
              Send feedback
            </h2>
            <p className="sheet-lede">
              Tell us what works, what's confusing, or what you'd like to see next.
            </p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close feedback">
            <CloseIcon size={20} />
          </button>
        </header>

        <form id="feedback-form" className="sheet-body" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label className="field-label" htmlFor="feedback-title-input">
              Title
            </label>
            <input
              ref={titleRef}
              id="feedback-title-input"
              className="input"
              name="title"
              value={form.title}
              onChange={updateField}
              placeholder="A short summary"
              maxLength={120}
              aria-invalid={Boolean(fieldErrors.title)}
              aria-describedby={fieldErrors.title ? "feedback-title-error" : undefined}
            />
            {fieldErrors.title && (
              <p className="field-error" id="feedback-title-error">
                <AlertIcon size={16} /> {fieldErrors.title}
              </p>
            )}
          </div>

          <div className="field">
            <label className="field-label" htmlFor="feedback-body">
              Details
            </label>
            <textarea
              id="feedback-body"
              className="input textarea"
              name="body"
              value={form.body}
              onChange={updateField}
              placeholder="What happened, what you expected, or what you'd like added"
              rows={5}
              maxLength={5000}
              aria-invalid={Boolean(fieldErrors.body)}
              aria-describedby={fieldErrors.body ? "feedback-body-error" : undefined}
            />
            {fieldErrors.body && (
              <p className="field-error" id="feedback-body-error">
                <AlertIcon size={16} /> {fieldErrors.body}
              </p>
            )}
          </div>

          <fieldset className="field">
            <legend className="field-label">
              How would you rate EcoRisk AI? <span className="optional">Optional</span>
            </legend>
            <div className="stars" role="radiogroup" aria-label="Rating" onMouseLeave={() => setHoverRating(0)}>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  type="button"
                  key={star}
                  role="radio"
                  aria-checked={form.rating === star}
                  aria-label={`${star} of 5, ${RATING_WORDS[star]}`}
                  className={`star${shownRating >= star ? " is-lit" : ""}`}
                  onClick={() => setForm((prev) => ({ ...prev, rating: prev.rating === star ? 0 : star }))}
                  onMouseEnter={() => setHoverRating(star)}
                >
                  <StarIcon size={26} strokeWidth={1.6} filled={shownRating >= star} />
                </button>
              ))}
              <span className="star-caption" aria-hidden="true">
                {RATING_WORDS[shownRating]}
              </span>
            </div>
          </fieldset>

          <div className="field">
            <label className="field-label" htmlFor="feedback-email">
              Email <span className="optional">Optional, if you'd like a reply</span>
            </label>
            <input
              id="feedback-email"
              className="input"
              name="email"
              type="email"
              value={form.email}
              onChange={updateField}
              placeholder="you@example.com"
              maxLength={254}
              autoComplete="email"
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? "feedback-email-error" : undefined}
            />
            {fieldErrors.email && (
              <p className="field-error" id="feedback-email-error">
                <AlertIcon size={16} /> {fieldErrors.email}
              </p>
            )}
          </div>

          {submitError && (
            <div className="notice notice--error" role="alert">
              <AlertIcon size={18} />
              <p>{submitError}</p>
            </div>
          )}

          <div ref={containerRef} className="turnstile-slot" />
        </form>

        <footer className="sheet-foot">
          <button type="submit" form="feedback-form" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? "Sending…" : "Send feedback"}
          </button>
        </footer>
      </aside>
    </div>
  );
}
