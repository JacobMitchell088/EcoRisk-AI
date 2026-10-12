import { GUIDANCE_SECTIONS, formatCoords, milesLabel, verdictCopy } from "./format";

function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );
}

const MARK_SVG = `<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="11" fill="none" stroke="#25586A" stroke-width="2.4"/><path d="M16 1.8v5.4M16 24.8v5.4M1.8 16h5.4M24.8 16h5.4" stroke="#25586A" stroke-width="2.4" stroke-linecap="round"/><g transform="rotate(40 16 16)"><path d="M16 9.6c4.1 2.6 4.1 10.2 0 12.8-4.1-2.6-4.1-10.2 0-12.8z" fill="#4E7A45"/><path d="M16 12.6v7" stroke="#F9FAF7" stroke-width="1.2" stroke-linecap="round"/></g></svg>`;

export function buildReportHtml(scanData, meta, site) {
  const hits = scanData?.gbif_hits || [];
  const contexts = scanData?.species_context || [];
  const radius = scanData?.input?.radius_miles ?? site.radius;
  const yearStart = scanData?.input?.year_start ?? 2000;
  const yearEnd = scanData?.input?.year_end ?? new Date().getFullYear();
  const scannedAt = meta?.scannedAt ? new Date(meta.scannedAt * 1000) : new Date();
  const scannedText = scannedAt.toLocaleString([], { dateStyle: "long", timeStyle: "short" });
  const verdict = verdictCopy(hits.length, radius, yearStart);
  const totalSightings = hits.reduce((sum, hit) => sum + (Number(hit.gbif_count) || 0), 0);

  const speciesHtml = hits
    .map((hit) => {
      const ctx = contexts.find((c) => c.scientific_name === hit.scientific_name) || {};
      const sightings = Number(hit.gbif_count) || 0;
      const tags = (ctx.tags || []).map((t) => `<li>${esc(t)}</li>`).join("");
      const sections = GUIDANCE_SECTIONS.filter(({ key }) => ctx[key])
        .map(({ key, label }) => `<div class="guide"><h3>${esc(label)}</h3><p>${esc(ctx[key])}</p></div>`)
        .join("");
      return `
      <section class="species">
        <header>
          <div>
            <h2>${esc(ctx.common_name || hit.scientific_name)}</h2>
            ${ctx.common_name ? `<p class="sci">${esc(hit.scientific_name)}</p>` : ""}
          </div>
          <p class="sightings">${sightings} ${sightings === 1 ? "sighting" : "sightings"} on record</p>
        </header>
        ${tags ? `<ul class="tags">${tags}</ul>` : ""}
        ${sections || `<p class="muted">No construction guidance was generated for this species.</p>`}
        <p class="links"><a href="https://www.gbif.org/species/${encodeURIComponent(hit.taxon_key)}">GBIF species record ${esc(hit.taxon_key)}</a></p>
      </section>`;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Environmental screening report: ${esc(site.name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet" />
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Public Sans", system-ui, -apple-system, "Segoe UI", sans-serif; background: #ECEFEA; color: #1C2925; font-size: 15px; line-height: 1.55; padding: 40px 16px; }
  .page { max-width: 760px; margin: 0 auto; background: #F9FAF7; border: 1px solid #D6DCD5; border-radius: 14px; padding: 40px; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px; }
  .brand span { color: #5B6964; font-weight: 400; font-size: 14px; padding-left: 10px; border-left: 1px solid #D6DCD5; }
  h1 { font-size: 28px; line-height: 1.2; letter-spacing: -0.015em; margin: 28px 0 20px; }
  .facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 24px; padding: 18px 0; border-top: 1px solid #D6DCD5; border-bottom: 1px solid #D6DCD5; }
  .facts dt { font-size: 13px; color: #5B6964; }
  .facts dd { font-weight: 600; font-variant-numeric: tabular-nums; }
  .verdict { margin: 24px 0; padding: 18px 20px; border-radius: 12px; background: #E3EDDD; }
  .verdict.flagged { background: #F5EAD2; }
  .verdict h2 { font-size: 21px; line-height: 1.25; margin-bottom: 4px; }
  .verdict p { color: #3C4A45; }
  .figures { display: flex; gap: 32px; margin-bottom: 28px; }
  .figures dt { font-size: 13px; color: #5B6964; }
  .figures dd { font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .species { padding: 22px 0; border-top: 1px solid #D6DCD5; page-break-inside: avoid; }
  .species header { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; margin-bottom: 10px; }
  .species h2 { font-size: 19px; line-height: 1.3; }
  .sci { font-style: italic; color: #5B6964; font-size: 14px; }
  .sightings { color: #7C5710; font-weight: 600; font-size: 13px; white-space: nowrap; }
  .tags { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .tags li { font-size: 12px; font-weight: 600; padding: 2px 9px; border-radius: 999px; background: #F2F4F0; border: 1px solid #D6DCD5; color: #3C4A45; }
  .guide { margin-bottom: 12px; }
  .guide h3 { font-size: 14px; margin-bottom: 2px; }
  .guide p, .muted { color: #3C4A45; max-width: 64ch; }
  .links { font-size: 13px; margin-top: 6px; }
  .links a { color: #25586A; }
  .disclaimer { margin-top: 28px; padding-top: 18px; border-top: 1px solid #D6DCD5; font-size: 13px; color: #5B6964; }
  @media (max-width: 600px) { .page { padding: 24px 20px; } .facts { grid-template-columns: 1fr; } .figures { flex-wrap: wrap; gap: 16px 28px; } }
  @media print {
    body { background: #fff; padding: 0; }
    .page { border: 0; padding: 0; max-width: none; }
    .verdict { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>
</head>
<body>
<main class="page">
  <div class="brand">${MARK_SVG} EcoRisk AI <span>Preliminary environmental screening</span></div>
  <h1>${esc(site.name)}</h1>
  <dl class="facts">
    <div><dt>Coordinates</dt><dd>${esc(formatCoords(site.lat, site.lon))}</dd></div>
    <div><dt>Search area</dt><dd>${esc(milesLabel(radius))} around the site</dd></div>
    <div><dt>Records searched</dt><dd>GBIF sightings, ${esc(yearStart)} to ${esc(yearEnd)}</dd></div>
    <div><dt>Screened</dt><dd>${esc(scannedText)}${meta?.cached ? " (saved result)" : ""}</dd></div>
  </dl>

  <section class="verdict${hits.length ? " flagged" : ""}">
    <h2>${esc(verdict.title)}</h2>
    <p>${esc(verdict.text)}</p>
  </section>

  <dl class="figures">
    <div><dt>Protected species</dt><dd>${hits.length}</dd></div>
    <div><dt>Sightings of those species</dt><dd>${totalSightings}</dd></div>
    <div><dt>All species recorded</dt><dd>${esc(scanData?.found_species_count ?? 0)}</dd></div>
  </dl>

  ${speciesHtml}

  <p class="disclaimer">
    This report is a preliminary screening based on public GBIF sighting records and AI-written summaries.
    It is not a regulatory review. A clear result does not guarantee that no protected species are present.
    Confirm findings with a qualified environmental professional and the relevant agencies before construction.
  </p>
</main>
</body>
</html>`;
}

export function downloadReport(scanData, meta, site) {
  const html = buildReportHtml(scanData, meta, site);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `environmental-screening-report-${new Date().toISOString().slice(0, 10)}.html`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
