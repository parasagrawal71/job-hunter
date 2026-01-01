let allRows = [];
let headers = [];

/* =========================
   DEFAULT COLUMN CONFIG
========================= */
const DEFAULT_COLUMN_CONFIG = {
  displayName: null,
  columnWidth: "auto",
  columnAlign: "left",
  hide: false, 
};

/* =========================
   COLUMN CONFIG (OVERRIDES)
========================= */
const COLUMN_CONFIG = {
  "S.No": {
    displayName: "#",
    columnWidth: "50px",
    columnAlign: "center",
  },
  Company: {
    displayName: "Company",
    columnWidth: "100px",
  },
  "Job title": {
    displayName: "Title",
    columnWidth: "250px",
  },
  YoE: {
    displayName: "YoE",
    columnWidth: "50px",
    columnAlign: "center",
  },
  "Match percentage": {
    displayName: "Match %",
    columnWidth: "90px",
    columnAlign: "right",
    hide: true, // HIDE COLUMN
  },
  "Matched Keywords count": {
    displayName: "Keywords #",
    columnWidth: "70px",
    columnAlign: "center",
  },
  "Matched keywords": {
    displayName: "Keywords",
    columnWidth: "120px",
  },
  "Matched locations": {
    displayName: "Location",
    columnWidth: "100px",
  },
  "Job link": {
    displayName: "Link",
    columnWidth: "50px",
    columnAlign: "center",
  },
};

/* =========================
   UTILS
========================= */
function cleanupValue(value) {
  if (typeof value !== "string") return value;
  return value.trim().replace(/^"(.*)"$/, "$1").replace(/"/g, "");
}

function parseCSVLine(line) {
  const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/;
  return line.split(regex).map(cleanupValue);
}

function getColumnConfig(header) {
  return {
    ...DEFAULT_COLUMN_CONFIG,
    ...(COLUMN_CONFIG[header] || {}),
  };
}

/* =========================
   LOAD CSV
========================= */
async function loadJobs() {
  const res = await fetch("../jobs.csv");
  const text = await res.text();

  const lines = text.trim().split("\n");
  headers = parseCSVLine(lines.shift());
  allRows = lines.map(parseCSVLine);

  renderHeader();
  renderTable(allRows);
}

/* =========================
   RENDER HEADER
========================= */
function renderHeader() {
  const thead = document.querySelector("#jobs thead");
  thead.innerHTML = "";

  const tr = document.createElement("tr");

  headers.forEach((header) => {
    const cfg = getColumnConfig(header);
    if (cfg.hide) return; // ✅ HIDE COLUMN

    const th = document.createElement("th");
    th.textContent = cfg.displayName || header;
    th.style.width = cfg.columnWidth;
    th.style.textAlign = cfg.columnAlign;

    tr.appendChild(th);
  });

  thead.appendChild(tr);
}

/* =========================
   RENDER ROWS
========================= */
function renderTable(rows) {
  const tbody = document.querySelector("#jobs tbody");
  tbody.innerHTML = "";

  document.getElementById("job-count").textContent = ` (${rows.length})`;

  rows.forEach((cols) => {
    const tr = document.createElement("tr");

    headers.forEach((header, idx) => {
      const cfg = getColumnConfig(header);
      if (cfg.hide) return; // ✅ HIDE COLUMN

      const td = document.createElement("td");
      td.style.textAlign = cfg.columnAlign;
      td.style.width = cfg.columnWidth;

      if (header.toLowerCase().includes("job link")) {
        const a = document.createElement("a");
        a.href = cols[idx];
        a.target = "_blank";
        a.textContent = "Open";
        td.appendChild(a);
      } else {
        td.textContent = cols[idx] ?? "";
      }

      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
}

/* =========================
   SEARCH
========================= */
document.getElementById("search").addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();

  if (!query) {
    renderTable(allRows);
    return;
  }

  const companyIdx = headers.findIndex((h) =>
    h.toLowerCase().includes("company")
  );
  const titleIdx = headers.findIndex((h) =>
    h.toLowerCase().includes("job title")
  );

  const filtered = allRows.filter((cols) => {
    const company = cols[companyIdx]?.toLowerCase() || "";
    const title = cols[titleIdx]?.toLowerCase() || "";
    return company.includes(query) || title.includes(query);
  });

  renderTable(filtered);
});

/* =========================
   INIT
========================= */
loadJobs();
