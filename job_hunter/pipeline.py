import csv
import re
from datetime import datetime

from job_hunter.config import build_config
from job_hunter.crawler import fetch_html
from job_hunter.extractor import (
    extract_job_links,
    extract_job_details,
    extract_yoe_from_description,
)
from job_hunter.matcher import (
    match_keywords,
    validate_job,
    calculate_score,
)

failed_companies = []


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def clean_csv_value(value):
    if not isinstance(value, str):
        return value
    return value.replace('"', "").strip()


def title_matches_include_groups(title, include_title_groups):
    title = title.lower()
    for group in include_title_groups:
        if all(word in title for word in group):
            return True
    return False


def title_has_exclude_title(title, exclude_titles):
    title = title.lower()
    return any(t in title for t in exclude_titles)


def is_probable_job_detail_url(url):
    url = url.lower()

    bad_patterns = [
        "/collections/",
        "/software/",
        "/products/",
        "/solutions/",
        "/platform/",
        "/jira/",
        "/confluence/",
        "/bitbucket/",
    ]

    if any(p in url for p in bad_patterns):
        return False

    good_patterns = [
        "/careers/details/",
        "/jobs/",
        "/job/",
        "/position/",
    ]

    return any(p in url for p in good_patterns)


def extract_matched_locations(description, allowed_locations):
    desc = description.lower()

    LOCATION_ALIASES = {
        "bangalore": ["bangalore", "bengaluru", "blr"],
        "remote": ["remote", "work from home", "wfh", "anywhere"],
        "india": ["india"],
    }

    matched = []
    for canonical, aliases in LOCATION_ALIASES.items():
        if canonical not in allowed_locations:
            continue
        if any(alias in desc for alias in aliases):
            matched.append(canonical)

    return matched


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
    config = build_config(min_yoe)

    log("🚀 Job Hunter started")
    log(f"📄 Streaming results to {output_file}")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
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
        writer.writeheader()

        serial_no = 1

        with open(input_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for company_index, row in enumerate(reader, start=1):
                company = row["company"].strip()
                career_url = row["career_url"].strip()

                log(f"\n🏢 [{company_index}] Company: {company}")
                log(f"🔗 Career URL: {career_url}")

                listing_html, error = fetch_html(career_url)
                if error:
                    failed_companies.append({"company": company, "error": error})
                    log(f"⚠️ Failed to crawl company — {error}")
                    continue

                if not listing_html:
                    continue

                job_links = extract_job_links(listing_html, career_url)

                for jl in job_links:
                    job_title = jl.get("title")
                    job_url = jl.get("link")

                    if not job_title or not job_url:
                        continue

                    if not title_matches_include_groups(
                        job_title, config["include_titles"]
                    ):
                        continue

                    if title_has_exclude_title(job_title, config["exclude_titles"]):
                        continue

                    if not is_probable_job_detail_url(job_url):
                        continue

                    details = extract_job_details(job_url)
                    description = details.get("description", "")
                    if not description:
                        continue

                    matched_keywords = match_keywords(
                        description, config["include_keywords"]
                    )
                    if not matched_keywords:
                        continue

                    matched_locations = extract_matched_locations(
                        description, config["allowed_locations"]
                    )

                    yoe = extract_yoe_from_description(description)

                    job_data = {
                        "title": job_title,
                        "description": description,
                        "yoe": yoe,
                        "matched_keywords": matched_keywords,
                    }

                    is_ok, reason = validate_job(job_data, config)
                    if not is_ok:
                        continue

                    score = calculate_score(job_data, config)
                    if score == 0:
                        continue

                    writer.writerow(
                        {
                            "S.No": serial_no,
                            "Company": clean_csv_value(company),
                            "Job title": clean_csv_value(job_title),
                            "Job link": clean_csv_value(job_url),
                            "YoE": yoe if yoe is not None else "",
                            "Match percentage": score,
                            "Matched Keywords count": len(matched_keywords),
                            "Matched keywords": clean_csv_value(
                                ", ".join(matched_keywords)
                            ),
                            "Matched locations": clean_csv_value(
                                ", ".join(matched_locations)
                            ),
                        }
                    )

                    csvfile.flush()
                    serial_no += 1

    # 🔑 FINAL SORT BEFORE EXIT
    sort_csv_in_place(output_file)

    if failed_companies:
        log("\n🚨 Companies with crawl errors:")
        for idx, entry in enumerate(failed_companies, start=1):
            log(f"{idx}. {entry['company']} — {entry['error']}")
    else:
        log("\n✅ No company-level crawl errors")

    log("🎉 Job Hunter finished")
