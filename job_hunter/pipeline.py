import csv
import time
import re

from job_hunter.config import build_config
from job_hunter.crawler import fetch_html
from job_hunter.extractor import (
    extract_job_links,
    extract_job_details,
    extract_yoe_from_description,
    extract_job_location,
)
from job_hunter.matcher import (
    calculate_score,
    match_title,
    match_job_detail_url,
    match_description,
    match_locations,
    is_company_blocked,
)
from job_hunter.utils.log import log, set_log_level
from job_hunter.utils.utils import clean_string_value
from job_hunter.constants import JobCSVField

failed_companies = []


# 🔹 NEW: load existing job links for deduplication
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


def run_pipeline(input_file: str, min_yoe: int, output_file: str):
    pattern = re.compile(r".*_test.*\.csv$")
    if bool(pattern.match(input_file)):
        log("Running in test mode")
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
            fieldnames=list(JobCSVField),
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

                    # --- Run job detail URL matcher
                    if not match_job_detail_url(job_url, config):
                        log("⏭️ Skipped — not a probable job detail URL", "DEBUG")
                        continue

                    # --- dedupe by job link
                    if job_url in existing_job_links:
                        log("⏭️ Skipped — job already exists in CSV", "DEBUG")
                        continue

                    # --- Run title matcher
                    if not match_title(job_title, config):
                        log("⏭️ Skipped — title matching failed", "DEBUG")
                        continue

                    log("🌐 Fetching job detail page...", "DEBUG")
                    details = extract_job_details(job_url)
                    description = details.get("description", "")
                    log(f"📝 Description length: {len(description)} chars", "DEBUG")

                    # --- Run description matcher
                    is_desc_match, matched_keywords = match_description(
                        description, config
                    )
                    if not is_desc_match:
                        log("⏭️ Skipped — description matching failed", "DEBUG")
                        continue

                    log("📍 Extracting job locations...", "DEBUG")
                    extracted_locations = extract_job_location(job_url)
                    log(f"📍 Extracted locations: {extracted_locations}", "DEBUG")

                    # --- Run location matcher
                    if not match_locations(extracted_locations, config):
                        log("⏭️ Skipped — location matching failed", "DEBUG")
                        continue

                    yoe = extract_yoe_from_description(description)
                    log(f"📊 Extracted YOE: {yoe}", "DEBUG")

                    job_data = {
                        "title": job_title,
                        "description": description,
                        "yoe": yoe,
                        "matched_keywords": matched_keywords,
                    }

                    score = calculate_score(job_data, config)
                    log(f"📈 Match score: {score}%", "DEBUG")

                    if score == 0:
                        log("⏭️ Skipped — score is 0", "DEBUG")
                        continue

                    writer.writerow(
                        {
                            JobCSVField.S_NO.value: serial_no,
                            JobCSVField.COMPANY.value: clean_string_value(company),
                            JobCSVField.JOB_TITLE.value: clean_string_value(job_title),
                            JobCSVField.JOB_LINK.value: clean_string_value(job_url),
                            JobCSVField.YOE.value: yoe if yoe is not None else "",
                            JobCSVField.MATCH_PERCENTAGE.value: score,
                            JobCSVField.MATCHED_KEYWORDS_COUNT.value: len(
                                matched_keywords
                            ),
                            JobCSVField.MATCHED_KEYWORDS.value: clean_string_value(
                                ", ".join(matched_keywords)
                            ),
                            JobCSVField.EXTRACTED_LOCATIONS.value: clean_string_value(
                                ", ".join(extracted_locations)
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
