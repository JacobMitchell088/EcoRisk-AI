import { useEffect, useRef, useState } from "react";
import { toast } from "react-hot-toast";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || "";

const backendUrl = API_BASE_URL ? API_BASE_URL.replace(/\/$/, "") : "";

const emptyForm = { title: "", body: "", email: "", rating: 0 };

export default function FeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [hoverRating, setHoverRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const turnstileRef = useRef(null);
  const widgetIdRef = useRef(null);
  const resolveRef = useRef(null);
  const rejectRef = useRef(null);

  // Render an invisible Turnstile widget once the modal is open
  useEffect(() => {
    if (!open || !window.turnstile || !turnstileRef.current || !TURNSTILE_SITE_KEY) return;
    if (widgetIdRef.current !== null) return;

    widgetIdRef.current = window.turnstile.render(turnstileRef.current, {
      sitekey: TURNSTILE_SITE_KEY,
      execution: "execute",
      appearance: "interaction-only",
      callback: (token) => {
        if (resolveRef.current) {
          resolveRef.current(token);
          resolveRef.current = null;
          rejectRef.current = null;
        }
      },
      "error-callback": () => {
        if (rejectRef.current) {
          rejectRef.current(new Error("Human verification failed."));
          rejectRef.current = null;
          resolveRef.current = null;
        }
      },
    });
  }, [open]);

  function getToken() {
    if (!window.turnstile || widgetIdRef.current === null) {
      return Promise.reject(new Error("Verification widget is not ready yet. Please wait a moment."));
    }
    const existing = window.turnstile.getResponse(widgetIdRef.current);
    if (existing) return Promise.resolve(existing);
    window.turnstile.reset(widgetIdRef.current);
    return new Promise((resolve, reject) => {
      resolveRef.current = resolve;
      rejectRef.current = reject;
      window.turnstile.execute(widgetIdRef.current);
    });
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function closeAndReset() {
    setOpen(false);
    setForm(emptyForm);
    setHoverRating(0);
    if (window.turnstile && widgetIdRef.current !== null) {
      window.turnstile.reset(widgetIdRef.current);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!backendUrl) {
      toast.error("Feedback is unavailable — API not configured.");
      return;
    }
    if (form.title.trim().length < 3) {
      toast.error("Please add a short title (at least 3 characters).");
      return;
    }
    if (form.body.trim().length < 5) {
      toast.error("Please add a little more detail in your feedback.");
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
        const text = await response.text();
        throw new Error(text || "Could not submit feedback.");
      }

      toast.success("Thanks! Your feedback was submitted.");
      closeAndReset();
    } catch (err) {
      toast.error(err.message || "Could not submit feedback.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          className="feedback-fab"
          onClick={() => setOpen(true)}
          aria-label="Provide feedback"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8A8.38 8.38 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Feedback
        </button>
      )}

      {open && (
        <div className="feedback-panel" role="dialog" aria-modal="true" aria-label="Provide feedback">
          <div className="feedback-head">
            <div>
              <span className="feedback-eyebrow">EcoRisk AI</span>
              <h2 className="feedback-title">Provide Feedback</h2>
            </div>
            <button
              type="button"
              className="feedback-close"
              onClick={closeAndReset}
              aria-label="Close feedback"
            >
              ✕
            </button>
          </div>

          <p className="feedback-intro">
            Tell us what's good, what's broken, or what you'd like to see next.
          </p>

          <form onSubmit={handleSubmit} className="feedback-form">
            <div className="feedback-field">
              <label className="feedback-label">Title</label>
              <input
                className="feedback-input"
                name="title"
                value={form.title}
                onChange={updateField}
                placeholder="Short summary"
                maxLength={120}
              />
            </div>

            <div className="feedback-field">
              <label className="feedback-label">Details</label>
              <textarea
                className="feedback-textarea"
                name="body"
                value={form.body}
                onChange={updateField}
                placeholder="What's good, bad, or what you'd like to see…"
                rows={4}
                maxLength={5000}
              />
            </div>

            <div className="feedback-field">
              <label className="feedback-label">
                Rating <span className="feedback-optional">optional</span>
              </label>
              <div className="feedback-stars" role="radiogroup" aria-label="Rating">
                {[1, 2, 3, 4, 5].map((star) => {
                  const active = (hoverRating || form.rating) >= star;
                  return (
                    <button
                      type="button"
                      key={star}
                      className={`feedback-star${active ? " active" : ""}`}
                      onClick={() =>
                        setForm((prev) => ({ ...prev, rating: prev.rating === star ? 0 : star }))
                      }
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      aria-label={`${star} star${star > 1 ? "s" : ""}`}
                    >
                      {active ? "★" : "☆"}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="feedback-field">
              <label className="feedback-label">
                Contact email <span className="feedback-optional">optional</span>
              </label>
              <input
                className="feedback-input"
                name="email"
                type="email"
                value={form.email}
                onChange={updateField}
                placeholder="you@example.com — for a reply"
                maxLength={254}
              />
            </div>

            <button type="submit" className="feedback-submit" disabled={submitting}>
              {submitting ? "Sending…" : "Send Feedback"}
            </button>

            <div ref={turnstileRef} className="feedback-captcha" />
          </form>
        </div>
      )}
    </>
  );
}
