let allRows = [];

function cleanupValue(value) {
  if (typeof value !== "string") return value;

  return value
    .trim()
    .replace(/^"(.*)"$/, "$1") // remove wrapping quotes
    .replace(/"/g, "");        // remove any remaining quotes
}

async function loadJobs() {
  const res = await fetch("../jobs.csv");
  const text = await res.text();

  const rows = text.trim().split("\n");
  const headers = rows.shift(); // remove header row

  allRows = rows.map(row => row.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/));
  renderTable(allRows);
}

function renderTable(rows) {
  const tbody = document.querySelector("#jobs tbody");
  tbody.innerHTML = "";
  document.getElementById("job-count").textContent = ` (${rows.length})`;

  rows.forEach(cols => {
    cols = cols.map(cleanupValue);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${cols[0]}</td>
      <td>${cols[1]}</td>
      <td>${cols[2]}</td>
      <td>${cols[4]}%</td>
      <td>${cols[6]}</td>
      <td>${cols[7]}</td>
      <td><a href="${cols[3]}" target="_blank">Open</a></td>
    `;
    tbody.appendChild(tr);
  });
}

/* 🔍 SEARCH LOGIC */
document.getElementById("search").addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();

  if (!query) {
    renderTable(allRows);
    return;
  }

  const filtered = allRows.filter(cols => {
    const company = cols[1].toLowerCase();
    const title = cols[2].toLowerCase();
    return company.includes(query) || title.includes(query);
  });

  renderTable(filtered);
});

loadJobs();
