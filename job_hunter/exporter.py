import csv


def export_csv(jobs, output_file):
    fieldnames = [
        "S.No",
        "Company",
        "Job title",
        "Job link",
        "Match percentage",
        "Matched Keywords count",
        "Matched keywords",
        "Matched locations",
    ]

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for index, job in enumerate(jobs, start=1):
            writer.writerow({
                "S.No": index,
                "Company": job.company,
                "Job title": job.title,
                "Job link": job.link,
                "Match percentage": job.match_percentage,
                "Matched Keywords count": job.keyword_count,
                "Matched keywords": ", ".join(job.matched_keywords),
                "Matched locations": ", ".join(
                    getattr(job, "matched_locations", [])
                ),
            })
