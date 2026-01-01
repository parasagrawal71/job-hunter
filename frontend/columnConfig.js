/* =========================
   DEFAULT COLUMN CONFIG
========================= */
window.DEFAULT_COLUMN_CONFIG = {
  displayName: null,
  columnWidth: "auto",
  columnAlign: "left",
  hide: false, 
};

/* =========================
   COLUMN CONFIG (OVERRIDES)
========================= */
window.COLUMN_CONFIG = {
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
    hide: true, // HIDE COLUMN
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