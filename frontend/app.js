let allRows = [];
let headers = [];
let openMenu = null;

const JOB_LIST_FILE_PATH = "../jobs.csv";

/* =========================
   APPLIED JOBS STATE
========================= */
const appliedJobsMap = new Map(); // job_link -> true

/* =========================
   UI STATE (NEW)
========================= */
let hideApplied = JSON.parse(localStorage.getItem("hideApplied") || "false");

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
  await loadAppliedJobs();

  const res = await fetch(JOB_LIST_FILE_PATH);
  if (!res.ok) return;
  const text = await res.text();

  const lines = text.trim().split("\n");
  headers = parseCSVLine(lines.shift());
  allRows = lines.map(parseCSVLine);

  injectHideAppliedCheckbox(); // ✅ NEW
  renderHeader();
  renderTable(allRows);
}

/* =========================
   HIDE APPLIED CHECKBOX (NEW)
========================= */
function injectHideAppliedCheckbox() {
  const search = document.getElementById("search");
  if (!search) return;

  const label = document.createElement("label");
  label.style.fontSize = "14px";
  label.style.cursor = "pointer";
  label.style.display = "flex";
  label.style.alignItems = "flex-start";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.id = "hide-applied";
  checkbox.checked = hideApplied;
  checkbox.style.width = "16px";
  checkbox.style.height = "16px";
  checkbox.style.marginTop = "-1px";
  checkbox.style.cursor = "pointer";

  checkbox.onchange = () => {
    hideApplied = checkbox.checked;
    localStorage.setItem("hideApplied", JSON.stringify(hideApplied));
    renderTable(allRows);
  };

  label.appendChild(checkbox);
  label.appendChild(document.createTextNode("Hide applied"));

  search.parentNode.appendChild(label);
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

  const linkIdx = headers.findIndex((h) =>
    h.toLowerCase().includes(HeaderMap.JOB_LINK),
  );

  const visibleRows = rows.filter((cols) => {
    const jobLink = cols[linkIdx];
    if (hideApplied && appliedJobsMap.get(jobLink) === true) {
      return false;
    }
    return true;
  });

  document.getElementById("job-count").textContent = ` (${visibleRows.length})`;

  visibleRows.forEach((cols, visibleRowIndex) => {
    const tr = document.createElement("tr");
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

      if (header.toLowerCase().includes(HeaderMap.JOB_LINK)) {
        const a = document.createElement("a");
        console.log('------', cols[idx])
        a.href = cols[idx];
        a.target = "_blank";
        a.textContent = "Open";
        td.appendChild(a);
      } else {
        if (cfg.displayName === "#") td.textContent = visibleRowIndex + 1;
        else td.textContent = cols[idx] ?? "";
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
   SEARCH
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
    h.toLowerCase().includes(HeaderMap.JOB_TITLE),
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
