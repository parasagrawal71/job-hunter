import csv
from job_hunter.utils.log import log
from job_hunter.constants import JobCSVField

def sort_csv_in_place(csv_path: str):
    log("🔄 Sorting CSV before exit...")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Sort by Company (ASC), Match % (DESC)
    rows.sort(
        key=lambda r: (
            r[JobCSVField.COMPANY.value].lower(),
            -float(r[JobCSVField.MATCH_PERCENTAGE.value]),
        )
    )

    # Rewrite CSV with new serial numbers
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(rows, start=1):
            row[JobCSVField.S_NO.value] = idx
            writer.writerow(row)

    log("✅ CSV sorted and rewritten")


# load existing job links for deduplication
def load_existing_job_links(csv_path: str) -> set:
    existing_links = set()
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = row.get(JobCSVField.JOB_LINK.value)
                if link:
                    existing_links.add(link.strip())
    except FileNotFoundError:
        pass
    return existing_links
