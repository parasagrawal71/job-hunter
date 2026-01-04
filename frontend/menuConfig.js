/* =========================
   ACTION MENU CONFIG
========================= */
window.ACTION_MENU_ITEMS = [
  {
    id: "toggle-applied",
    displayName: "Toggle status",
    callback: ({ cols, headers, toggleApplied, appliedJobsMap }) => {
      const linkIdx = headers.findIndex((h) =>
        h.toLowerCase().includes(HeaderMap.JOB_LINK),
      );
      const jobLink = cols[linkIdx];
      if (jobLink) toggleApplied(jobLink, !appliedJobsMap.get(jobLink));
    },
  },
];