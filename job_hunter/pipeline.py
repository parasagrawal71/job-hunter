import csv
import time
import re

from job_hunter.config import build_config
from job_hunter.crawler import fetch_html
from job_hunter.extractor import (
    extract_job_links,
    extract_job_details,
    extract_job_locations,
    extract_yoe_from_description,
)
from job_hunter.matcher import (
    is_company_blocked,
    match_title,
    match_job_detail_url,
    match_description,
    match_locations,
    calculate_score,
)
from job_hunter.utils.log import log, set_log_level
from job_hunter.utils.utils import clean_string_value
from job_hunter.constants import JobCSVField, ErrorCSVField
from job_hunter.helpers import sort_csv_in_place, load_existing_job_links

failed_companies = []
error_file = "jobs_error.csv"
companies_with_zero_links = []


def run_pipeline(input_file: str, output_file: str):
    pattern = re.compile(r".*_test.*\.csv$")
    if bool(pattern.match(input_file)):
        log("Running in test mode")
        set_log_level("DEBUG")

    start_time = time.time()
    config = build_config()

    log("🚀 Job Hunter started")
    log(f"📄 Streaming results to {output_file}")

    # load existing jobs (append-only behavior)
    existing_job_links = load_existing_job_links(output_file)
    serial_no = len(existing_job_links) + 1
    csv_exists = bool(existing_job_links)

    error_csv = open(error_file, "w", newline="", encoding="utf-8")
    error_writer = csv.DictWriter(
        error_csv,
        fieldnames=list(ErrorCSVField),
    )
    error_writer.writeheader()

    # open in append mode instead of write
    with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=list(JobCSVField),
        )

        # write header only if file is new
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
                    companies_with_zero_links.append(
                        {"company": company, "career_url": career_url}
                    )
                    log(f"⚠️ Failed to crawl company — {error}")
                    error_writer.writerow(
                        {
                            ErrorCSVField.COMPANY.value: company,
                            ErrorCSVField.ERROR.value: error,
                            ErrorCSVField.CAREER_URL.value: career_url,
                        }
                    )
                    error_csv.flush()
                    continue

                if not listing_html:
                    log("⚠️ Empty career page HTML", "DEBUG")
                    companies_with_zero_links.append({"company": company, "career_url": career_url})
                    continue

                # --- Step 1: Extract job links
                job_links = extract_job_links(listing_html, career_url)
                is_company_links_found = False

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
                        is_company_links_found = True
                        log("⏭️ Skipped — job already exists in CSV", "DEBUG")
                        continue

                    # --- Run title matcher
                    if not match_title(job_title, config):
                        log("⏭️ Skipped — title matching failed", "DEBUG")
                        continue

                    # --- Step 2: Extract job details
                    details = extract_job_details(job_url)
                    description = details.get("description", "")

                    # --- Run description matcher
                    is_desc_match, matched_keywords = match_description(
                        description, config
                    )
                    if not is_desc_match:
                        log("⏭️ Skipped — description matching failed", "DEBUG")
                        continue

                    # --- Step 3: Extract job locations
                    extracted_locations = extract_job_locations(job_url, description, config)

                    # --- Run location matcher
                    is_loc_match, _ = match_locations(extracted_locations, config)
                    if not is_loc_match:
                        log("⏭️ Skipped — location matching failed", "DEBUG")
                        continue

                    # --- Step 4: Extract YOE
                    yoe = extract_yoe_from_description(description)

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
                    is_company_links_found = True
                    log("✅ Job written to CSV")
                    serial_no += 1

                if not is_company_links_found:
                    companies_with_zero_links.append({"company": company, "career_url": career_url})
                    log(f"⚠️ Zero job links found for company {company}")

                log(f"✅ Company {company} completed")

    # 🔑 FINAL SORT BEFORE EXIT
    print("\n\n")
    sort_csv_in_place(output_file)

    # Write company-level errors
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

    # Write companies with zero links
    print("\n\n")
    if companies_with_zero_links:
        log("🚨 Companies with zero job links:")
        for idx, entry in enumerate(companies_with_zero_links, start=1):
            log(f"{idx}. {entry['company']} — {entry['career_url']}")
    else:
        log("✅ No company with zero job links")

    # Log total run time
    end_time = time.time()
    total_seconds = int(end_time - start_time)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    print("\n\n")
    log(f"⏱️ Total run time: {minutes}m {seconds}s")
