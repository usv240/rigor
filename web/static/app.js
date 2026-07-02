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
const KIND_TIP = {
  pvalue: "A p-value measures how likely a result is just chance. Below .05 is usually called 'significant'. Rigor recomputes it from the reported numbers to check it is right.",
  sample: "Degrees of freedom (df) depend on how many participants a test used. Rigor checks the df is even possible for the study's reported sample size (N).",
  grim:   "For whole-number ratings, an average can only land on certain values. GRIM checks whether a reported mean is arithmetically possible.",
  claim:  "Rigor checks whether the paper's words match its numbers, for example calling a result 'significant' when the math says it is not.",
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
    ${f.plain ? `<div class="plain">${esc(f.plain)}</div>` : ""}
    <div class="nums">reported <b>${esc(f.reported)}</b> → recomputed <b>${esc(f.recomputed)}</b></div>
    ${f.fix ? `<div class="fix"><b>What to do:</b> ${esc(f.fix)}</div>` : ""}
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
        <i class="info" data-tip="${KIND_TIP[k] || ""}">i</i>
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
        <h3>Integrity report
          <i class="info" data-tip="A 0-100 summary. Lower means more, or more serious, problems were found. It is a guide to where to look, not a grade.">i</i>
        </h3>
        <div class="row">
          <span><span class="dotc" style="background:#ef4444"></span><b>${r.errors}</b> error${r.errors !== 1 ? "s" : ""}
            <i class="info" data-tip="Provably wrong by exact math. High confidence: the reported number contradicts what it must be.">i</i></span>
          <span><span class="dotc" style="background:#f59e0b"></span><b>${r.warnings}</b> to review
            <i class="info" data-tip="An AI-flagged judgment call, like causal or over-general wording. Not a proof: use your own judgment.">i</i></span>
          <span><span class="dotc" style="background:#16a34a"></span><b>${okCount}</b> clean
            <i class="info" data-tip="Checked and found consistent. No problem here.">i</i></span>
          <span class="muted">· ${r.n_tests} test(s), ${r.n_means} mean(s) · ${esc(r.source || "")}</span>
        </div>
      </div>
    </div>
    <div class="chips">
      <button class="chip active" data-f="all">All ${r.findings.length}</button>
      <button class="chip" data-f="ERROR">Errors ${r.errors}</button>
      <button class="chip" data-f="WARNING">To review ${r.warnings}</button>
      <button class="chip" data-f="OK">Clean ${okCount}</button>
      <button class="dlbtn" id="dlbtn">&#8595; Download report (.md)</button>
    </div>
    <div class="findings">${sections || '<div class="empty">No statistics found to check.</div>'}</div>`;

  report.classList.remove("hidden");
  report.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    report.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    ch.classList.add("active");
    applyFilter(ch.dataset.f);
  }));
  const dl = report.querySelector("#dlbtn");
  if (dl) dl.addEventListener("click", () => downloadReport(r));
  report.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function downloadReport(r) {
  const okCount = r.findings.filter(f => f.severity === "OK").length;
  const L = [
    "# Rigor integrity report",
    "",
    `- Source: ${r.source || "pasted text"}`,
    `- Integrity score: ${r.score}/100`,
    `- ${r.errors} error(s), ${r.warnings} to review, ${okCount} clean`,
    `- Checked: ${r.n_tests} test(s), ${r.n_means} mean(s)`,
    "",
  ];
  const groups = { ERROR: "Errors", WARNING: "To review", OK: "Clean" };
  for (const sev of ["ERROR", "WARNING", "OK"]) {
    const items = r.findings.filter(f => f.severity === sev);
    if (!items.length) continue;
    L.push(`## ${groups[sev]} (${items.length})`, "");
    for (const f of items) {
      L.push(`### [${KIND_LABEL[f.kind] || f.kind}] ${f.claim || "(statistic)"}`);
      if (f.plain) L.push(f.plain);
      L.push(`- reported ${f.reported} -> recomputed ${f.recomputed}`);
      if (f.fix) L.push(`- What to do: ${f.fix}`);
      L.push("");
    }
  }
  L.push("---", "Generated by Rigor - https://github.com/usv240/rigor");
  const blob = new Blob([L.join("\n")], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "rigor-report.md";
  a.click();
  URL.revokeObjectURL(url);
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
