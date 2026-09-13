import BrandMark from "./BrandMark";
import { CheckIcon } from "./Icons";

// Thresholds mirror the progress values reported by GBIF.run_scan.
const SCAN_STEPS = [
  { label: "Verifying you're a person", threshold: 1 },
  { label: "Loading the Illinois protected species list", threshold: 10 },
  { label: "Searching GBIF sighting records", threshold: 35 },
  { label: "Checking sightings against the state list", threshold: 60 },
  { label: "Summarizing construction guidance with AI", threshold: 86 },
  { label: "Preparing your report", threshold: 100 },
];

export default function ScanProgress({ progress, finalizing }) {
  const states = SCAN_STEPS.map((step) => {
    const isLastStep = step.threshold === 100;
    const done = isLastStep ? progress >= step.threshold && !finalizing : progress >= step.threshold;
    const active = isLastStep
      ? finalizing
      : !done && SCAN_STEPS.find((s) => progress < s.threshold) === step;
    return { ...step, state: done ? "done" : active ? "active" : "pending" };
  });

  const current = states.find((step) => step.state === "active");
  const statusText = current ? `${current.label}…` : "Screening complete";

  return (
    <div className="progress">
      <div className="progress-head">
        <span className="scan-signal" aria-hidden="true">
          <BrandMark size={24} />
        </span>
        <p className="progress-status" aria-live="polite">
          {statusText}
        </p>
        <span className="progress-pct">{progress}%</span>
      </div>

      <div
        className="progress-track"
        role="progressbar"
        aria-label="Screening progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
      >
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <ol className="checklist">
        {states.map((step) => (
          <li key={step.label} className={`check check--${step.state}`}>
            <span className="check-dot" aria-hidden="true">
              {step.state === "done" && <CheckIcon size={12} strokeWidth={3} />}
            </span>
            <span>{step.label}</span>
          </li>
        ))}
      </ol>

      <p className="fine-print">
        Keep this page open. Your report appears here when the screening finishes, usually within a
        minute.
      </p>
    </div>
  );
}
