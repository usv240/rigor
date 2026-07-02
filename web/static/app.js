// ============ Rigor - frontend ============
const $ = (s) => document.querySelector(s);
const paper = $("#paper"), runBtn = $("#run"), pdfInput = $("#pdf"),
      report = $("#report"), hint = $("#hint");

const SEV = {
  ERROR:   { color: "#ef4444", label: "ERROR" },
  WARNING: { color: "#f59e0b", label: "WARNING" },
  OK:      { color: "#16a34a", label: "OK" },
};
const KIND = { pvalue: "p-value", grim: "mean · GRIM", claim: "claim vs evidence", sample: "df vs N" };

// preload the demo paper
fetch("/api/sample").then(r => r.json()).then(d => { paper.value = d.text; })
  .catch(() => {});

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
  runBtn.innerHTML = on
    ? `<span class="spinner"></span> Analyzing…`
    : "Check integrity";
  runBtn.disabled = on;
}

function render(r) {
  const rc = r.score >= 80 ? "#16a34a" : r.score >= 50 ? "#f59e0b" : "#ef4444";
  const order = { ERROR: 0, WARNING: 1, OK: 2 };
  const findings = [...r.findings].sort((a, b) => order[a.severity] - order[b.severity]);
  const okCount = r.findings.filter(f => f.severity === "OK").length;

  const cards = findings.map((f, i) => {
    const s = SEV[f.severity];
    return `<div class="finding" style="border-left-color:${s.color};animation-delay:${i * 60}ms">
      <span class="badge" style="background:${s.color}">${s.label}</span>
      <span class="kind">${KIND[f.kind] || f.kind}</span>
      <div class="claim">${esc(f.claim) || "<span class='muted'>(statistic)</span>"}</div>
      <div class="nums">reported <b>${esc(f.reported)}</b> &nbsp;→&nbsp; recomputed <b>${esc(f.recomputed)}</b></div>
      <div class="detail">${esc(f.detail)}</div>
    </div>`;
  }).join("");

  report.innerHTML = `
    <div class="scorecard">
      <div class="ring" style="--val:${r.score};--rc:${rc}"><div class="num">${r.score}<small>/100</small></div></div>
      <div class="sc-meta">
        <h3>Integrity report</h3>
        <div class="row">
          <span><span class="dotc" style="background:#ef4444"></span><b>${r.errors}</b> error${r.errors!==1?"s":""}</span>
          <span><span class="dotc" style="background:#f59e0b"></span><b>${r.warnings}</b> warning${r.warnings!==1?"s":""}</span>
          <span><span class="dotc" style="background:#16a34a"></span><b>${okCount}</b> clean</span>
          <span class="muted">· ${r.n_tests} test(s), ${r.n_means} mean(s) checked · ${esc(r.source||"")}</span>
        </div>
      </div>
    </div>
    ${findings.length ? cards : `<div class="empty">No statistics found to check. Try pasting a Results section.</div>`}
  `;
  report.classList.remove("hidden");
  report.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c]));
}
