// ============ Rigor - frontend ============
const $ = (s) => document.querySelector(s);
const paper = $("#paper"), runBtn = $("#run"), pdfInput = $("#pdf"),
      report = $("#report"), hint = $("#hint");

const SEV = {
  ERROR:   { color: "#ef4444", label: "ERROR" },
  WARNING: { color: "#f59e0b", label: "REVIEW" },
  OK:      { color: "#16a34a", label: "OK" },
};
const KIND_ORDER = ["pvalue", "sample", "grim", "claim"];
const KIND_LABEL = {
  pvalue: "p-value recomputation",
  sample: "df vs N cross-check",
  grim:   "GRIM (impossible means)",
  claim:  "claim vs evidence",
};
const SORT = { ERROR: 0, WARNING: 1, OK: 2 };

fetch("/api/sample").then(r => r.json()).then(d => { paper.value = d.text; }).catch(() => {});
pdfInput.addEventListener("change", () => {
  hint.textContent = pdfInput.files[0] ? `📄 ${pdfInput.files[0].name}` : "";
});
runBtn.addEventListener("click", run);

async function run() {
  setLoading(true);
  report.classList.add("hidden");
  try {
    let res;
    if (pdfInput.files[0]) {
      const fd = new FormData();
      fd.append("file", pdfInput.files[0]);
      res = await fetch("/api/audit/pdf", { method: "POST", body: fd });
    } else {
      res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: paper.value }),
      });
    }
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    render(await res.json());
  } catch (e) {
    report.innerHTML = `<div class="empty">⚠️ ${e.message}. Check your API key / connection and try again.</div>`;
    report.classList.remove("hidden");
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  runBtn.innerHTML = on ? `<span class="spinner"></span> Analyzing…` : "Check integrity";
  runBtn.disabled = on;
}

function card(f, i) {
  const s = SEV[f.severity];
  return `<div class="finding sev-${f.severity}" data-sev="${f.severity}"
      style="border-left-color:${s.color};animation-delay:${i * 35}ms">
    <div class="frow">
      <span class="badge" style="background:${s.color}">${s.label}</span>
      <span class="claimline">${esc(f.claim) || "<span class='muted'>(statistic)</span>"}</span>
    </div>
    <div class="nums">reported <b>${esc(f.reported)}</b> → recomputed <b>${esc(f.recomputed)}</b></div>
    <div class="detail">${esc(f.detail)}</div>
  </div>`;
}

function render(r) {
  const rc = r.score >= 80 ? "#16a34a" : r.score >= 50 ? "#f59e0b" : "#ef4444";
  const okCount = r.findings.filter(f => f.severity === "OK").length;

  // group findings by check type, ordered
  const byKind = {};
  r.findings.forEach(f => { (byKind[f.kind] = byKind[f.kind] || []).push(f); });
  const kinds = Object.keys(byKind).sort((a, b) => {
    const ia = KIND_ORDER.indexOf(a), ib = KIND_ORDER.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });

  let idx = 0, sections = "";
  kinds.forEach(k => {
    const items = byKind[k].sort((a, b) => SORT[a.severity] - SORT[b.severity]);
    const errs = items.filter(f => f.severity === "ERROR").length;
    sections += `<div class="fsection">
      <div class="fshead">${KIND_LABEL[k] || k}
        <span class="fscount">${items.length}</span>
        ${errs ? `<span class="fscount err">${errs} error${errs !== 1 ? "s" : ""}</span>` : ""}
      </div>
      ${items.map(f => card(f, idx++)).join("")}
    </div>`;
  });

  report.innerHTML = `
    <div class="scorecard">
      <div class="ring" style="--val:${r.score};--rc:${rc}"><div class="num">${r.score}<small>/100</small></div></div>
      <div class="sc-meta">
        <h3>Integrity report</h3>
        <div class="row">
          <span><span class="dotc" style="background:#ef4444"></span><b>${r.errors}</b> error${r.errors !== 1 ? "s" : ""}</span>
          <span><span class="dotc" style="background:#f59e0b"></span><b>${r.warnings}</b> to review</span>
          <span><span class="dotc" style="background:#16a34a"></span><b>${okCount}</b> clean</span>
          <span class="muted">· ${r.n_tests} test(s), ${r.n_means} mean(s) · ${esc(r.source || "")}</span>
        </div>
      </div>
    </div>
    <div class="chips">
      <button class="chip active" data-f="all">All ${r.findings.length}</button>
      <button class="chip" data-f="ERROR">Errors ${r.errors}</button>
      <button class="chip" data-f="WARNING">To review ${r.warnings}</button>
      <button class="chip" data-f="OK">Clean ${okCount}</button>
    </div>
    <div class="findings">${sections || '<div class="empty">No statistics found to check.</div>'}</div>`;

  report.classList.remove("hidden");
  report.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    report.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    ch.classList.add("active");
    applyFilter(ch.dataset.f);
  }));
  report.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function applyFilter(f) {
  report.querySelectorAll(".finding").forEach(el => {
    el.style.display = (f === "all" || el.dataset.sev === f) ? "" : "none";
  });
  report.querySelectorAll(".fsection").forEach(sec => {
    const any = [...sec.querySelectorAll(".finding")].some(el => el.style.display !== "none");
    sec.style.display = any ? "" : "none";
  });
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
