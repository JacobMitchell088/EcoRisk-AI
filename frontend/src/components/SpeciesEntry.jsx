import { useEffect, useId, useState } from "react";
import { ChevronDownIcon, ExternalIcon, LeafIcon } from "./Icons";
import { GUIDANCE_SECTIONS } from "../lib/format";

export default function SpeciesEntry({ hit, context, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const [thumb, setThumb] = useState(null);
  const bodyId = useId();

  const wikiName = hit.scientific_name.replace(/ /g, "_");
  const wikiUrl = `https://en.wikipedia.org/wiki/${encodeURIComponent(wikiName)}`;
  const gbifUrl = `https://www.gbif.org/species/${encodeURIComponent(hit.taxon_key)}`;

  useEffect(() => {
    let cancelled = false;
    fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(wikiName)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!cancelled && data?.thumbnail?.source) {
          setThumb(data.thumbnail.source);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [wikiName]);

  const sections = GUIDANCE_SECTIONS.filter(({ key }) => context?.[key]);
  const sightings = Number(hit.gbif_count) || 0;

  return (
    <article className="species">
      <button
        type="button"
        className="species-toggle"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls={bodyId}
      >
        <span className="species-thumb">
          {thumb ? (
            <img src={thumb} alt="" loading="lazy" />
          ) : (
            <LeafIcon size={22} />
          )}
        </span>
        <span className="species-names">
          <span className="species-common">
            {context?.common_name || hit.scientific_name}
          </span>
          {context?.common_name && (
            <span className="species-sci">{hit.scientific_name}</span>
          )}
          <span className="species-count">
            {sightings} {sightings === 1 ? "sighting" : "sightings"} on record
            nearby
          </span>
          {!context && (
            <span className="species-badge species-badge--unreviewed">
              Not AI-reviewed
            </span>
          )}
        </span>
        <ChevronDownIcon className="species-chevron" size={20} />
      </button>

      <div className="species-body" id={bodyId} hidden={!open}>
        {context?.tags?.length > 0 && (
          <ul className="tags" aria-label="Key concerns">
            {context.tags.map((tag) => (
              <li className="tag" key={tag}>
                {tag}
              </li>
            ))}
          </ul>
        )}

        {sections.length > 0 ? (
          <div className="guidance">
            {sections.map(({ key, label }) => (
              <div key={key}>
                <h4 className="guidance-label">{label}</h4>
                <p className="guidance-text">{context[key]}</p>
              </div>
            ))}
          </div>
        ) : context ? (
          <p className="guidance-text guidance-missing">
            No construction guidance was generated for this species. The links
            below have background on its habitat and behavior.
          </p>
        ) : (
          <p className="guidance-text guidance-missing">
            This species wasn't included in the AI review for this screening.
            The links below have background on its habitat and behavior.
          </p>
        )}

        <div className="species-links">
          <a href={wikiUrl} target="_blank" rel="noreferrer noopener">
            Wikipedia <ExternalIcon size={14} />
            <span className="visually-hidden"> (opens in a new tab)</span>
          </a>
          <a href={gbifUrl} target="_blank" rel="noreferrer noopener">
            GBIF species record <ExternalIcon size={14} />
            <span className="visually-hidden"> (opens in a new tab)</span>
          </a>
        </div>
      </div>
    </article>
  );
}
