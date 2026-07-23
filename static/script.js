const form = document.getElementById("job-form");
const runBtn = document.getElementById("run-btn");
const output = document.getElementById("output");
const copyBtn = document.getElementById("copy-btn");
const stages = document.querySelectorAll(".stage");
const wires = document.querySelectorAll(".wire");

const STAGE_ORDER = ["downloading", "extracting audio", "transcribing"];

function resetPipeline() {
  stages.forEach(s => s.classList.remove("active", "done"));
  wires.forEach(w => w.classList.remove("filled"));
}

function setPipeline(status) {
  const idx = STAGE_ORDER.indexOf(status);
  stages.forEach((el, i) => {
    el.classList.remove("active", "done");
    if (i < idx || status === "done") el.classList.add("done");
    else if (i === idx) el.classList.add("active");
  });
  wires.forEach((w, i) => {
    if (i < idx || status === "done") w.classList.add("filled");
    else w.classList.remove("filled");
  });
}

function setOutput(text, mode) {
  output.textContent = text;
  output.classList.remove("filled", "err");
  if (mode) output.classList.add(mode);
}

async function poll(jobId) {
  try {
    const res = await fetch(`/api/status/${jobId}`);
    const job = await res.json();

    if (job.status === "error") {
      setOutput(`error: ${job.error}`, "err");
      resetPipeline();
      runBtn.disabled = false;
      return;
    }

    setPipeline(job.status);

    if (job.status === "done") {
      setOutput(job.transcript, "filled");
      runBtn.disabled = false;
      return;
    }

    setOutput(`${job.status}...`);
    setTimeout(() => poll(jobId), 1500);
  } catch (err) {
    setOutput(`error: ${err.message}`, "err");
    runBtn.disabled = false;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = document.getElementById("url").value.trim();
  const model = document.getElementById("model").value;
  if (!url) return;

  runBtn.disabled = true;
  resetPipeline();
  setOutput("queuing job...");

  try {
    const res = await fetch("/api/transcribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, model }),
    });
    const data = await res.json();

    if (data.error) {
      setOutput(`error: ${data.error}`, "err");
      runBtn.disabled = false;
      return;
    }

    poll(data.job_id);
  } catch (err) {
    setOutput(`error: ${err.message}`, "err");
    runBtn.disabled = false;
  }
});

copyBtn.addEventListener("click", () => {
  if (!output.classList.contains("filled")) return;
  navigator.clipboard.writeText(output.textContent);
  copyBtn.textContent = "copied";
  setTimeout(() => (copyBtn.textContent = "copy"), 1200);
});
