import re
from typing import Tuple, List
from job_hunter.utils.log import log
from job_hunter.utils.utils import normalize_str_into_words, contains_whole_word, match_words


def calculate_score(job, config):
    experience_score = 1 if job.get("yoe") else 0
    keyword_score = len(job["matched_keywords"]) / len(config["include_keywords"])

    score = experience_score * 0.3 + keyword_score * 0.7

    return round(score * 100, 2)


def is_company_blocked(company, blocked_companies):
    company = company.lower()
    return company in blocked_companies


def title_matches_include_groups(title, include_title_groups):
    words = set(re.findall(r"\b\w+\b", title.lower()))
    for group in include_title_groups:
        if all(word in words for word in group):
            return True
    return False


def match_title(title, config):
    log(f"🔎 matching title: {title}", "DEBUG")
    title = title.lower()

    if not title:
        log(f"🚨 title is empty", "DEBUG")
        return False

    # Exclusion: title contains exclude_titles
    exclude_titles = config["exclude_titles"]
    for exclude_title in exclude_titles:
        if contains_whole_word(title, exclude_title):
            log(f"🚨 excluded title found in title: '{exclude_title}'", "DEBUG")
            return False

    # Exclusion: title contains blocked_locations
    blocked_locations = config["blocked_locations"]
    for loc in blocked_locations:
        if contains_whole_word(title, loc):
            log(f"🚨 blocked location found in title: '{loc}'", "DEBUG")
            return False

    # Exclusion: title contains exclude_keywords
    exclude_keywords = config["exclude_keywords"]
    for keyword in exclude_keywords:
        if contains_whole_word(title, keyword):
            log(f"🚨 excluded keyword found in title: '{keyword}'", "DEBUG")
            return False

    # Inclusion: title contains include_titles
    include_title_groups = config["include_titles"]
    if not title_matches_include_groups(title, include_title_groups):
        log("🚨 title failed include_titles check", "DEBUG")
        return False

    log("✅ title passed all checks", "DEBUG")
    return True


def match_job_detail_url(url, config):
    log(f"🔎 checking job detail URL: {url}", "DEBUG")
    url = url.lower()

    if not url:
        log(f"🚨 URL is empty", "DEBUG")
        return False

    if not (url.startswith("https://") or url.startswith("www.")):
        log(f"🚨 url doesn't start with https:// or www.", "DEBUG")
        return False

    good_patterns = [
        "/careers",
        "/job-description",
        "/careers/details/",
        "/careers/job-description",
        "/jobs/",
        "/job/",
        "/position/",
        "/positions/",
        "/open-positions/",
        "/open-position/",
        "/openings/",
        "/opening/",
        "/role/",
        "/roles/",
    ]
    if any(p in url for p in good_patterns):
        log(f"✅ url passed good patterns", "DEBUG")
        return True

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
        log(f"🚨 encountered bad patterns", "DEBUG")
        return False

    log(f"✅ url passed all checks", "DEBUG")
    return True


def match_description(description, config) -> Tuple[bool, List[str]]:
    log(f"🔎 matching description", "DEBUG")
    description = description.lower()

    if not description:
        log(f"🚨 description is empty", "DEBUG")
        return False, []

    # # Exclusion: description contains exclude_keywords
    # exclude_keywords = config["exclude_keywords"]
    # for keyword in exclude_keywords:
    #     if contains_whole_word(description, keyword):
    #         log(f"🚨 excluded keyword found in description: '{keyword}'", "DEBUG")
    #         return False, []

    # Inclusion: description contains include_keywords
    include_keywords = config["include_keywords"]
    matched_keywords = match_words(description, include_keywords)
    log(
        f"🔑 Keywords matched ({len(matched_keywords)}): {matched_keywords}",
        "DEBUG",
    )
    if len(matched_keywords) == 0:
        log("🚨 description has no include_keywords", "DEBUG")
        return False, []

    log("✅ description passed all checks", "DEBUG")
    return True, matched_keywords


def match_locations(extracted_locations, config) -> Tuple[bool, List[str]]:
    log(f"🔎 matching locations", "DEBUG")
    extracted_locations = normalize_str_into_words(extracted_locations)
    extracted_locations = [loc.lower() for loc in extracted_locations]

    if len(extracted_locations) == 0:
        log("🚨 no extracted locations", "DEBUG")
        return False, []

    # Exclusion: extracted_locations contains blocked_locations
    blocked_locations = config["blocked_locations"]
    for extracted_location in extracted_locations:
        if extracted_location in blocked_locations:
            log(
                f"🚨 blocked location found in extracted locations: '{extracted_location}'",
                "DEBUG",
            )
            return False, []

    # Inclusion: extracted_locations contains allowed_locations
    allowed_locations = config["allowed_locations"]
    matched_locations = [loc for loc in allowed_locations if loc in extracted_locations]
    if len(matched_locations) == 0:
        log(
            f"🚨 no allowed locations found in extracted locations: '{extracted_locations}' (expected one of {allowed_locations})",
            "DEBUG",
        )
        return False, []

    log("✅ locations passed all checks", "DEBUG")
    return True, matched_locations
