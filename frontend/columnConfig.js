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
window.HeaderMap = {
  S_NO: "s_no",
  COMPANY: "company",
  JOB_TITLE: "job_title",
  YOE: "yoe",
  MATCH_PERCENTAGE: "match_percentage",
  MATCHED_KEYWORDS_COUNT: "matched_keywords_count",
  MATCHED_KEYWORDS: "matched_keywords",
  EXTRACTED_LOCATIONS: "extracted_locations",
  JOB_LINK: "job_link",
};

window.COLUMN_CONFIG = {
  s_no: {
    displayName: "#",
    columnWidth: "50px",
    columnAlign: "center",
  },
  company: {
    displayName: "Company",
    columnWidth: "100px",
  },
  job_title: {
    displayName: "Title",
    columnWidth: "250px",
  },
  yoe: {
    displayName: "YoE",
    columnWidth: "50px",
    columnAlign: "center",
  },
  match_percentage: {
    displayName: "Match %",
    columnWidth: "90px",
    columnAlign: "right",
    hide: true, // HIDE COLUMN
  },
  matched_keywords_count: {
    displayName: "Keywords #",
    columnWidth: "70px",
    columnAlign: "center",
    hide: true, // HIDE COLUMN
  },
  matched_keywords: {
    displayName: "Keywords",
    columnWidth: "120px",
  },
  extracted_locations: {
    displayName: "Locations",
    columnWidth: "100px",
  },
  job_link: {
    displayName: "Link",
    columnWidth: "50px",
    columnAlign: "center",
  },
};