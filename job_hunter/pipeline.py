import csv
import time
import re
import asyncio

from job_hunter.config import build_config
from job_hunter.crawler import fetch_html
from job_hunter.extractor import (
    extract_job_links,
    extract_job_details_and_locations,
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
from job_hunter.constants import (
    JobCSVField,
    ErrorCSVField,
    CompanyWithZeroLinksCSVField,
)
from job_hunter.helpers import (
    sort_csv_in_place,
    load_existing_job_links,
    load_companies_from_output_file,
)

failed_companies = []
error_file = "jobs_error.csv"
companies_with_zero_links = []
companies_with_zero_links_file = "companies_with_zero_links.csv"

# 🔑 GLOBAL CONCURRENCY LIMIT
JOB_SEMAPHORE = asyncio.Semaphore(20)


async def run_pipeline(input_file: str, output_file: str):
    pattern = re.compile(r".*_test.*\.csv$")
    if bool(pattern.match(input_file)):
        log("Running in debug mode")
        set_log_level("DEBUG")

    start_time = time.time()
    config = build_config()

    log("🚀 Job Hunter started")
    log(f"📄 Streaming results to {output_file}")

    # load existing jobs (append-only behavior)
    existing_job_links = load_existing_job_links(output_file)
    serial_no = len(existing_job_links) + 1
    csv_exists = bool(existing_job_links)

    # open error file
    error_csv = open(error_file, "w", newline="", encoding="utf-8")
    error_writer = csv.DictWriter(
        error_csv,
        fieldnames=list(ErrorCSVField),
    )
    error_writer.writeheader()

    # open companies_with_zero_links file
    zero_links_csv = open(
        companies_with_zero_links_file, "w", newline="", encoding="utf-8"
    )
    zero_links_csv_writer = csv.DictWriter(
        zero_links_csv,
        fieldnames=list(CompanyWithZeroLinksCSVField),
    )
    zero_links_csv_writer.writeheader()

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

                log("\n\n\n")
                log(f"🏢 [{company_index}] Company: {company}")
                log(f"🔗 Career URL: {career_url}")

                if is_company_blocked(company, config["blocked_companies"]):
                    log(f"⚠️ Skipping blocked company: {company}")
                    continue

                listing_html, error = await fetch_html(career_url)
                if error:
                    failed_companies.append({"company": company, "error": error})
                    log(f"⚠️ Failed to crawl company — {error}")
                    error_writer.writerow(
                        {
                            ErrorCSVField.COMPANY.value: company,
                            ErrorCSVField.ERROR.value: error,
                            ErrorCSVField.CAREER_URL.value: career_url,
                        }
                    )
                    error_csv.flush()

                    companies_with_zero_links.append(
                        {"company": company, "career_url": career_url}
                    )
                    zero_links_csv_writer.writerow(
                        {
                            CompanyWithZeroLinksCSVField.S_NO.value: len(
                                companies_with_zero_links
                            ),
                            CompanyWithZeroLinksCSVField.COMPANY.value: company,
                            CompanyWithZeroLinksCSVField.CAREER_URL.value: career_url,
                        }
                    )
                    zero_links_csv.flush()
                    continue

                if not listing_html:
                    log("⚠️ Empty career page HTML", "DEBUG")
                    companies_with_zero_links.append(
                        {"company": company, "career_url": career_url}
                    )
                    zero_links_csv_writer.writerow(
                        {
                            CompanyWithZeroLinksCSVField.S_NO.value: len(
                                companies_with_zero_links
                            ),
                            CompanyWithZeroLinksCSVField.COMPANY.value: company,
                            CompanyWithZeroLinksCSVField.CAREER_URL.value: career_url,
                        }
                    )
                    zero_links_csv.flush()
                    continue

                # --- Step 1: Extract job links
                job_links = extract_job_links(listing_html, career_url)

                log(f"⚙️ Processing {len(job_links)} job links in parallel", "DEBUG")

                async def process_job(idx, jl):
                    async with JOB_SEMAPHORE:
                        job_title = jl.get("title")
                        job_url = jl.get("link")

                        log(f"\n➡️ Job [{idx}] Title: {job_title}", "DEBUG")
                        log(f"🔗 Job URL: {job_url}", "DEBUG")

                        # --- Run job detail URL matcher
                        if not match_job_detail_url(job_url, config):
                            log("⏭️ Skipped — not a probable job detail URL", "DEBUG")
                            return None

                        # --- dedupe by job link
                        if job_url in existing_job_links:
                            log("⏭️ Skipped — job already exists in CSV", "DEBUG")
                            return "JOB_ALREADY_EXISTS"

                        # --- Run title matcher
                        if not match_title(job_title, config):
                            log("⏭️ Skipped — title matching failed", "DEBUG")
                            return None

                        # --- Step 2: Extract job description and job locations
                        details = await extract_job_details_and_locations(
                            job_url, config
                        )
                        description = details.get("description", "")
                        extracted_locations = details.get("locations", [])

                        # --- Run description matcher
                        is_desc_match, matched_keywords, extracted_keywords = (
                            match_description(description, config)
                        )
                        if not is_desc_match:
                            log("⏭️ Skipped — description matching failed", "DEBUG")
                            return None

                        # --- Run location matcher
                        is_loc_match, _ = match_locations(extracted_locations, config)
                        if not is_loc_match:
                            log("⏭️ Skipped — location matching failed", "DEBUG")
                            return None

                        # --- Step 3: Extract YOE
                        yoe = extract_yoe_from_description(description)

                        job_data = {
                            "title": job_title,
                            "description": description,
                            "yoe": yoe,
                            "matched_keywords": matched_keywords,
                            "extracted_keywords": extracted_keywords,
                        }

                        score = calculate_score(job_data, config)
                        log(f"📈 Match score: {score}%", "DEBUG")

                        if score == 0:
                            log("⏭️ Skipped — score is 0", "DEBUG")
                            return None

                        return {
                            JobCSVField.COMPANY.value: clean_string_value(company),
                            JobCSVField.JOB_TITLE.value: clean_string_value(job_title),
                            JobCSVField.JOB_LINK.value: clean_string_value(job_url),
                            JobCSVField.YOE.value: yoe if yoe is not None else "",
                            JobCSVField.MATCH_PERCENTAGE.value: score,
                            JobCSVField.EXTRACTED_KEYWORDS_COUNT.value: len(
                                extracted_keywords
                            ),
                            JobCSVField.EXTRACTED_KEYWORDS.value: clean_string_value(
                                ", ".join(extracted_keywords)
                            ),
                            JobCSVField.EXTRACTED_LOCATIONS.value: clean_string_value(
                                ", ".join(extracted_locations)
                            ),
                        }

                tasks = [
                    process_job(idx, jl) for idx, jl in enumerate(job_links, start=1)
                ]

                results = await asyncio.gather(*tasks)

                for result in results:
                    if result == "JOB_ALREADY_EXISTS":
                        continue

                    if not result:
                        continue

                    result[JobCSVField.S_NO.value] = serial_no
                    writer.writerow(result)
                    csvfile.flush()

                    existing_job_links.add(result[JobCSVField.JOB_LINK.value])
                    log("✅ Job written to CSV")
                    serial_no += 1

                companies_from_file = load_companies_from_output_file(output_file)
                if company not in companies_from_file:
                    companies_with_zero_links.append(
                        {"company": company, "career_url": career_url}
                    )
                    zero_links_csv_writer.writerow(
                        {
                            CompanyWithZeroLinksCSVField.S_NO.value: len(
                                companies_with_zero_links
                            ),
                            CompanyWithZeroLinksCSVField.COMPANY.value: company,
                            CompanyWithZeroLinksCSVField.CAREER_URL.value: career_url,
                        }
                    )
                    zero_links_csv.flush()
                    log(f"⚠️ Zero job links found for company {company}")

                log(f"✅ Company {company} completed")

    # 🔑 FINAL SORT BEFORE EXIT
    log("\n\n")
    sort_csv_in_place(output_file)

    # Write company-level errors
    log("\n\n")
    if failed_companies:
        log("🚨 Companies with crawl errors:")
        for idx, entry in enumerate(failed_companies, start=1):
            log(f"{idx}. {entry['company']} — {entry['error']}")
    else:
        log("✅ No company-level crawl errors")
    error_csv.close()
    log(f"📄 Company-level errors written to {error_file}")

    # Write companies with zero links
    log("\n\n")
    if companies_with_zero_links:
        log("🚨 Companies with zero job links:")
        for idx, entry in enumerate(companies_with_zero_links, start=1):
            log(f"{idx}. {entry['company']} — {entry['career_url']}")
    else:
        log("✅ No company with zero job links")
    zero_links_csv.close()
    log(f"📄 Companies with zero job links written to {companies_with_zero_links_file}")

    log("\n\n")
    log("🎉 Job Hunter finished")

    # Log total run time
    end_time = time.time()
    total_seconds = int(end_time - start_time)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    log("\n\n")
    log(f"⏱️ Total run time: {minutes}m {seconds}s")
