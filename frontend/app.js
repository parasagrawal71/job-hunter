let allRows = [];
let headers = [];
let openMenu = null;

/* =========================
   APPLIED JOBS STATE
========================= */
const appliedJobsMap = new Map(); // job_link -> true

/* =========================
   LOAD APPLIED JOBS CSV
========================= */
function loadAppliedJobs() {
  const applied = JSON.parse(localStorage.getItem("appliedJobs") || "{}");
  Object.keys(applied).forEach((link) =>
    appliedJobsMap.set(link, applied[link]),
  );
}

/* =========================
   UTILS
========================= */
function cleanupValue(value) {
  if (typeof value !== "string") return value;
  return value
    .trim()
    .replace(/^"(.*)"$/, "$1")
    .replace(/"/g, "");
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
   LOAD JOBS
========================= */
async function loadJobs() {
  await loadAppliedJobs(); // ✅ load applied first

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
    if (cfg.hide) return;

    const th = document.createElement("th");
    th.textContent = cfg.displayName || header;
    th.style.width = cfg.columnWidth;
    th.style.textAlign = cfg.columnAlign;

    tr.appendChild(th);
  });

  const actionTh = document.createElement("th");
  actionTh.style.width = "40px";
  tr.appendChild(actionTh);

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

    const linkIdx = headers.findIndex((h) =>
      h.toLowerCase().includes("job link"),
    );
    const jobLink = cols[linkIdx];

    if (appliedJobsMap.get(jobLink) === true) {
      tr.style.textDecoration = "line-through";
      tr.style.opacity = "0.6";
    }

    headers.forEach((header, idx) => {
      const cfg = getColumnConfig(header);
      if (cfg.hide) return;

      const td = document.createElement("td");
      td.style.textAlign = cfg.columnAlign;

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

    /* ---- ACTION MENU ---- */
    const actionTd = document.createElement("td");
    actionTd.style.position = "relative";

    const menuBtn = document.createElement("span");
    menuBtn.innerHTML = `
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    `;
    menuBtn.className = "kebab-menu";
    menuBtn.style.cursor = "pointer";

    const menu = document.createElement("div");
    menu.style.position = "absolute";
    menu.style.right = "0";
    menu.style.top = "24px";
    menu.style.background = "#fff";
    menu.style.border = "1px solid #ccc";
    menu.style.display = "none";
    menu.style.zIndex = "1000";
    menu.style.width = "200px";

    ACTION_MENU_ITEMS.forEach((item) => {
      const menuItem = document.createElement("div");
      menuItem.textContent = item.displayName;
      menuItem.style.padding = "6px 10px";
      menuItem.style.cursor = "pointer";
      menuItem.style.borderBottom = "1px solid #ccc";
      menuItem.style.textAlign = "center";

      menuItem.onclick = async () => {
        await item.callback({
          cols,
          headers,
          toggleApplied,
          appliedJobsMap,
        });
        menu.style.display = "none";
        openMenu = null;
        renderTable(allRows);
      };

      menu.appendChild(menuItem);
    });

    menuBtn.onclick = (e) => {
      e.stopPropagation();
      if (openMenu && openMenu !== menu) openMenu.style.display = "none";
      menu.style.display = menu.style.display === "block" ? "none" : "block";
      openMenu = menu.style.display === "block" ? menu : null;
    };

    actionTd.appendChild(menuBtn);
    actionTd.appendChild(menu);
    tr.appendChild(actionTd);

    tbody.appendChild(tr);
  });
}

/* =========================
   MARK APPLIED
========================= */
function toggleApplied(jobLink, isApplied) {
  appliedJobsMap.set(jobLink, isApplied);
  const applied = JSON.parse(localStorage.getItem("appliedJobs") || "{}");
  applied[jobLink] = isApplied;
  localStorage.setItem("appliedJobs", JSON.stringify(applied));
}

/* =========================
   CLOSE MENU
========================= */
document.addEventListener("click", () => {
  if (openMenu) {
    openMenu.style.display = "none";
    openMenu = null;
  }
});

/* =========================
   SEARCH (RESTORED ✅)
========================= */
document.getElementById("search").addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();

  if (!query) {
    renderTable(allRows);
    return;
  }

  const companyIdx = headers.findIndex((h) =>
    h.toLowerCase().includes("company"),
  );
  const titleIdx = headers.findIndex((h) =>
    h.toLowerCase().includes("job title"),
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
