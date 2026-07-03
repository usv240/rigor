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

let dismissed = new Set();  // finding ids the human reviewer has dismissed
let lastR = null;

fetch("/api/sample").then(r => r.json()).then(d => { paper.value = d.text; }).catch(() => {});
pdfInput.addEventListener("change", () => {
  hint.textContent = pdfInput.files[0] ? pdfInput.files[0].name : "";
});
runBtn.addEventListener("click", run);

const themebtn = document.querySelector("#themebtn");
if (themebtn) themebtn.addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", cur);
  localStorage.setItem("rigor-theme", cur);
});

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
    if (!res.ok) {
      let msg = `Server error ${res.status}`;
      try { const e = await res.json(); if (e.error) msg = e.error; } catch (_) {}
      throw new Error(msg);
    }
    render(await res.json());
  } catch (e) {
    report.innerHTML = `<div class="empty">Error: ${e.message}. Check your API key / connection and try again.</div>`;
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
  return `<div class="finding sev-${f.severity}" data-sev="${f.severity}" data-id="${f._id}"
      style="border-left-color:${s.color};animation-delay:${i * 35}ms">
    <div class="frow">
      <span class="badge" style="background:${s.color}">${s.label}</span>
      <span class="claimline">${esc(f.claim) || "<span class='muted'>(statistic)</span>"}</span>
      <button class="dismiss" data-id="${f._id}">Dismiss</button>
    </div>
    ${f.plain ? `<div class="plain">${esc(f.plain)}</div>` : ""}
    <div class="nums">reported <b>${esc(f.reported)}</b> → recomputed <b>${esc(f.recomputed)}</b></div>
    ${f.fix ? `<div class="fix"><b>What to do:</b> ${esc(f.fix)}</div>` : ""}
  </div>`;
}

function render(r) {
  lastR = r;
  dismissed = new Set();
  r.findings.forEach((f, i) => { f._id = i; });
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
          <i class="info" data-tip="A 0-100 summary, weighted by severity. Lower means more, or more serious, problems. It updates live as you dismiss findings.">i</i>
          <span id="revised" class="revised" style="display:none">revised by you</span>
        </h3>
        <div class="row">
          <span><span class="dotc" style="background:#ef4444"></span><b id="cErr">${r.errors}</b> error${r.errors !== 1 ? "s" : ""}
            <i class="info" data-tip="Provably wrong by exact math. High confidence: the reported number contradicts what it must be.">i</i></span>
          <span><span class="dotc" style="background:#f59e0b"></span><b id="cWarn">${r.warnings}</b> to review
            <i class="info" data-tip="An AI-flagged judgment call, like causal or over-general wording. Not a proof: use your own judgment.">i</i></span>
          <span><span class="dotc" style="background:#16a34a"></span><b id="cOk">${okCount}</b> clean
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
      <button class="dlbtn" id="dlbtn">Download report</button>
      <button class="dlbtn dlbtn-primary" id="agentbtn">Run agent analysis</button>
    </div>
    ${r.findings.length ? `<div class="reviewbar">
      <span>Human review: dismiss any false positive, then export your finalized report.</span>
      <span class="kept" id="keptcount">${r.findings.length} kept</span>
    </div>` : ""}
    <div class="findings">${sections || '<div class="empty">No statistics found to check.</div>'}</div>
    <div id="agentbox"></div>`;

  report.classList.remove("hidden");
  report.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    report.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    ch.classList.add("active");
    applyFilter(ch.dataset.f);
  }));
  const dl = report.querySelector("#dlbtn");
  if (dl) dl.addEventListener("click", () => downloadReport(r));
  const ab = report.querySelector("#agentbtn");
  if (ab) ab.addEventListener("click", () => runAgent(paper.value));
  report.querySelectorAll(".dismiss").forEach(btn => btn.addEventListener("click", () => {
    const el = btn.closest(".finding");
    const id = Number(btn.dataset.id);
    if (dismissed.has(id)) { dismissed.delete(id); el.classList.remove("dismissed"); btn.textContent = "Dismiss"; }
    else { dismissed.add(id); el.classList.add("dismissed"); btn.textContent = "Undo"; }
    recomputeScore();
  }));
  requestAnimationFrame(() => report.scrollIntoView({ behavior: "smooth", block: "start" }));
}

function recomputeScore() {
  // Genuine human-in-the-loop: recompute the weighted score from reviewer-approved findings.
  const kept = lastR.findings.filter(f => !dismissed.has(f._id));
  const penalty = kept.reduce((s, f) => s + (f.weight || 0), 0);
  const score = Math.max(0, Math.round(100 - penalty * 5));  // matches report.py
  const rc = score >= 80 ? "#16a34a" : score >= 50 ? "#f59e0b" : "#ef4444";
  const ring = report.querySelector(".ring");
  if (ring) {
    ring.style.setProperty("--val", score);
    ring.style.setProperty("--rc", rc);
    ring.querySelector(".num").innerHTML = `${score}<small>/100</small>`;
  }
  const c = { ERROR: 0, WARNING: 0, OK: 0 };
  kept.forEach(f => c[f.severity]++);
  const set = (id, v) => { const el = report.querySelector("#" + id); if (el) el.textContent = v; };
  set("cErr", c.ERROR); set("cWarn", c.WARNING); set("cOk", c.OK);
  set("keptcount", `${kept.length} kept`);
  const rev = report.querySelector("#revised");
  if (rev) rev.style.display = dismissed.size ? "" : "none";
}

function appendLog(el, html) {
  const d = document.createElement("div");
  d.className = "aline";
  d.innerHTML = html;
  el.appendChild(d);
  el.scrollTop = el.scrollHeight;
}

async function runAgent(text) {
  const box = report.querySelector("#agentbox");
  const btn = report.querySelector("#agentbtn");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Agent working…`;
  box.innerHTML = `<div class="agentcard">
    <div class="ahead">Agent activity <span class="muted">&mdash; live Qwen tool-calling loop</span></div>
    <div class="alog" id="alog"></div>
    <div class="anarr" id="anarr"></div>
  </div>`;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  const log = box.querySelector("#alog");
  const narr = box.querySelector("#anarr");
  try {
    const res = await fetch("/api/agent/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      let m = `Error ${res.status}`;
      try { const e = await res.json(); if (e.error) m = e.error; } catch (_) {}
      throw new Error(m);
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const line = buf.slice(0, i); buf = buf.slice(i + 2);
        if (!line.startsWith("data: ")) continue;
        const ev = JSON.parse(line.slice(6));
        if (ev.type === "status") {
          appendLog(log, `<span class="astatus">${esc(ev.msg)}</span>`);
        } else if (ev.type === "tool") {
          const v = (ev.result && ev.result.verdict) || JSON.stringify(ev.result);
          const bad = /ERROR|IMPOSSIBLE|not significant|n\.s\./i.test(v);
          appendLog(log, `<span class="acall"><b>${esc(ev.tool)}</b>(${esc(JSON.stringify(ev.args))})</span>`
            + `<span class="${bad ? "av-bad" : "av-ok"}"> &rarr; ${esc(v)}</span>`);
        } else if (ev.type === "narrative") {
          narr.innerHTML = `<div class="ndivider">Agent's verdict</div>${esc(ev.text).replace(/\n/g, "<br>")}`;
        } else if (ev.type === "error") {
          appendLog(log, `<span class="av-bad">Error: ${esc(ev.msg)}</span>`);
        }
      }
    }
  } catch (e) {
    appendLog(log, `<span class="av-bad">Error: ${esc(e.message)}</span>`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "Run agent analysis";
  }
}

function downloadReport(r) {
  const findings = r.findings.filter(f => !dismissed.has(f._id));  // reviewer-approved only
  const c = { ERROR: 0, WARNING: 0, OK: 0 };
  findings.forEach(f => c[f.severity]++);
  const L = [
    "# Rigor integrity report",
    "",
    `- Source: ${r.source || "pasted text"}`,
    `- Integrity score: ${r.score}/100`,
    `- ${c.ERROR} error(s), ${c.WARNING} to review, ${c.OK} clean`
      + (dismissed.size ? ` (${dismissed.size} dismissed by reviewer)` : ""),
    `- Checked: ${r.n_tests} test(s), ${r.n_means} mean(s)`,
    "",
  ];
  const groups = { ERROR: "Errors", WARNING: "To review", OK: "Clean" };
  for (const sev of ["ERROR", "WARNING", "OK"]) {
    const items = findings.filter(f => f.severity === sev);
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
