import csv
import time

from job_hunter.config import build_config
from job_hunter.crawler import fetch_html
from job_hunter.extractor import (
    extract_job_links,
    extract_job_details,
    extract_yoe_from_description,
    extract_matched_locations,
)
from job_hunter.matcher import (
    match_keywords,
    validate_job,
    calculate_score,
    title_matches_include_groups,
    title_has_exclude_title,
    title_has_exclude_keywords,
    title_has_blocked_locations,
    is_company_blocked,
    is_probable_job_detail_url,
)
from job_hunter.utils.log import log, set_log_level
from job_hunter.utils.utils import clean_string_value

failed_companies = []


# 🔹 NEW: load existing job links for deduplication
def load_existing_job_links(csv_path: str) -> set:
    existing_links = set()
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = row.get("Job link")
                if link:
                    existing_links.add(link.strip())
    except FileNotFoundError:
        pass
    return existing_links


def sort_csv_in_place(csv_path: str):
    log("🔄 Sorting CSV before exit...")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Sort by Company (ASC), Match % (DESC)
    rows.sort(
        key=lambda r: (
            r["Company"].lower(),
            -float(r["Match percentage"]),
        )
    )

    # Rewrite CSV with new serial numbers
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(rows, start=1):
            row["S.No"] = idx
            writer.writerow(row)

    log("✅ CSV sorted and rewritten")


def run_pipeline(input_file: str, min_yoe: int, output_file: str):
    if input_file.endswith("_test.csv"):
        set_log_level("DEBUG")

    start_time = time.time()
    config = build_config(min_yoe)

    log("🚀 Job Hunter started")
    log(f"📄 Streaming results to {output_file}")

    # 🔹 NEW: load existing jobs (append-only behavior)
    existing_job_links = load_existing_job_links(output_file)
    serial_no = len(existing_job_links) + 1
    csv_exists = bool(existing_job_links)

    error_file = "jobs_error.csv"
    error_csv = open(error_file, "w", newline="", encoding="utf-8")
    error_writer = csv.DictWriter(
        error_csv,
        fieldnames=["Company", "Error", "Career URL"],
    )
    error_writer.writeheader()

    # 🔹 CHANGED: open in append mode instead of write
    with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "S.No",
                "Company",
                "Job title",
                "Job link",
                "YoE",
                "Match percentage",
                "Matched Keywords count",
                "Matched keywords",
                "Matched locations",
            ],
        )

        # 🔹 NEW: write header only if file is new
        if not csv_exists:
            writer.writeheader()

        with open(input_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for company_index, row in enumerate(reader, start=1):
                company = row["company"].strip()
                career_url = row["career_url"].strip()

                print("\n\n\n")
                log(f"🏢 [{company_index}] Company: {company}")
                log(f"🔗 Career URL: {career_url}")

                if is_company_blocked(company, config["blocked_companies"]):
                    log(f"⚠️ Skipping blocked company: {company}")
                    continue

                listing_html, error = fetch_html(career_url)
                if error:
                    failed_companies.append({"company": company, "error": error})
                    log(f"⚠️ Failed to crawl company — {error}")
                    error_writer.writerow(
                        {
                            "Company": company,
                            "Error": error,
                            "Career URL": career_url,
                        }
                    )
                    error_csv.flush()
                    continue

                if not listing_html:
                    log("⚠️ Empty career page HTML", "DEBUG")
                    continue

                job_links = extract_job_links(listing_html, career_url)
                log(f"📦 Raw job links found: {len(job_links)}")

                for idx, jl in enumerate(job_links, start=1):
                    job_title = jl.get("title")
                    job_url = jl.get("link")

                    log(f"\n➡️ Job [{idx}] Title: {job_title}", "DEBUG")
                    log(f"🔗 Job URL: {job_url}", "DEBUG")

                    if not job_title or not job_url:
                        log("⏭️ Skipped — missing title or URL", "DEBUG")
                        continue

                    # 🔹 NEW: dedupe by job link
                    if job_url in existing_job_links:
                        log("⏭️ Skipped — job already exists in CSV", "DEBUG")
                        continue

                    if not title_matches_include_groups(
                        job_title, config["include_titles"]
                    ):
                        log("⏭️ Skipped — title failed include_titles", "DEBUG")
                        continue

                    if title_has_exclude_title(job_title, config["exclude_titles"]):
                        log("⏭️ Skipped — title matched exclude_titles", "DEBUG")
                        continue

                    if title_has_exclude_keywords(job_title, config["exclude_keywords"]):
                        log("⏭️ Skipped — title matched exclude_keywords", "DEBUG")
                        continue

                    if title_has_blocked_locations(job_title, config["blocked_locations"]):
                        log("⏭️ Skipped — title matched blocked_locations", "DEBUG")
                        continue

                    if not is_probable_job_detail_url(job_url):
                        log("⏭️ Skipped — not a probable job detail URL", "DEBUG")
                        continue

                    log("🌐 Fetching job detail page...", "DEBUG")
                    details = extract_job_details(job_url)
                    description = details.get("description", "")
                    log(f"📝 Description length: {len(description)} chars", "DEBUG")

                    if not description:
                        log("⏭️ Skipped — empty job description", "DEBUG")
                        continue

                    matched_keywords = match_keywords(
                        description, config["include_keywords"]
                    )
                    log(
                        f"🔑 Keywords matched ({len(matched_keywords)}): {matched_keywords}",
                        "DEBUG",
                    )

                    if not matched_keywords:
                        log("⏭️ Skipped — no keywords matched", "DEBUG")
                        continue

                    matched_locations = extract_matched_locations(
                        description, config["allowed_locations"]
                    )
                    log(f"📍 Matched locations: {matched_locations}", "DEBUG")

                    yoe = extract_yoe_from_description(description)
                    log(f"📊 Extracted YOE: {yoe}", "DEBUG")

                    job_data = {
                        "title": job_title,
                        "description": description,
                        "yoe": yoe,
                        "matched_keywords": matched_keywords,
                    }

                    log("🧪 Running validation rules...", "DEBUG")
                    is_ok, reason = validate_job(job_data, config)
                    if not is_ok:
                        log(f"❌ Validation failed — {reason}", "DEBUG")
                        continue

                    score = calculate_score(job_data, config)
                    log(f"📈 Match score: {score}%", "DEBUG")

                    if score == 0:
                        log("⏭️ Skipped — score is 0", "DEBUG")
                        continue

                    writer.writerow(
                        {
                            "S.No": serial_no,
                            "Company": clean_string_value(company),
                            "Job title": clean_string_value(job_title),
                            "Job link": clean_string_value(job_url),
                            "YoE": yoe if yoe is not None else "",
                            "Match percentage": score,
                            "Matched Keywords count": len(matched_keywords),
                            "Matched keywords": clean_string_value(
                                ", ".join(matched_keywords)
                            ),
                            "Matched locations": clean_string_value(
                                ", ".join(matched_locations)
                            ),
                        }
                    )

                    csvfile.flush()
                    existing_job_links.add(job_url)
                    log("✅ Job written to CSV")
                    serial_no += 1

    # 🔑 FINAL SORT BEFORE EXIT
    print("\n\n")
    sort_csv_in_place(output_file)

    print("\n\n")
    if failed_companies:
        log("🚨 Companies with crawl errors:")
        for idx, entry in enumerate(failed_companies, start=1):
            log(f"{idx}. {entry['company']} — {entry['error']}")
    else:
        log("✅ No company-level crawl errors")

    error_csv.close()
    log(f"📄 Company-level errors written to {error_file}")

    print("\n\n")
    log("🎉 Job Hunter finished")

    # Log total run time
    end_time = time.time()
    total_seconds = int(end_time - start_time)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    print("\n\n")
    log(f"⏱️ Total run time: {minutes}m {seconds}s")
