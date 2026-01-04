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
  [HeaderMap.S_NO]: {
    displayName: "#",
    columnWidth: "50px",
    columnAlign: "center",
  },
  [HeaderMap.COMPANY]: {
    displayName: "Company",
    columnWidth: "100px",
  },
  [HeaderMap.JOB_TITLE]: {
    displayName: "Title",
    columnWidth: "250px",
  },
  [HeaderMap.YOE]: {
    displayName: "YoE",
    columnWidth: "50px",
    columnAlign: "center",
  },
  [HeaderMap.MATCH_PERCENTAGE]: {
    displayName: "Match %",
    columnWidth: "90px",
    columnAlign: "right",
    hide: true, // HIDE COLUMN
  },
  [HeaderMap.MATCHED_KEYWORDS_COUNT]: {
    displayName: "Keywords #",
    columnWidth: "70px",
    columnAlign: "center",
    hide: true, // HIDE COLUMN
  },
  [HeaderMap.MATCHED_KEYWORDS]: {
    displayName: "Keywords",
    columnWidth: "120px",
  },
  [HeaderMap.EXTRACTED_LOCATIONS]: {
    displayName: "Locations",
    columnWidth: "100px",
  },
  [HeaderMap.JOB_LINK]: {
    displayName: "Link",
    columnWidth: "50px",
    columnAlign: "center",
  },
};