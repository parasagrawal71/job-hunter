import re
from job_hunter.utils.log import log


def match_keywords(text, keywords):
    text = text.lower()
    return [k for k in keywords if k in text]


def location_allowed(text, allowed_locations):
    text = text.lower()
    return any(loc in text for loc in allowed_locations)


def contains_whole_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def validate_job(job, config):
    desc = job["description"].lower()

    # ❌ Blocked locations (log exact match)
    for loc in config.get("blocked_locations", []):
        if contains_whole_word(desc, loc):
            return False, f"blocked location detected: '{loc}'"

    # ❌ Excluded tech keywords
    for k in config["exclude_keywords"]:
        if k in desc:
            return False, f"excluded keyword found: '{k}'"

    # ❌ Location not allowed (positive filter)
    if not any(loc in desc for loc in config["allowed_locations"]):
        return (
            False,
            f"location not allowed (expected one of {config['allowed_locations']})",
        )

    return True, None


def calculate_score(job, config):
    experience_score = 1 if job.get("yoe") else 0
    keyword_score = len(job["matched_keywords"]) / len(config["include_keywords"])

    score = experience_score * 0.3 + keyword_score * 0.7

    return round(score * 100, 2)


def title_matches_include_groups(title, include_title_groups):
    title = title.lower()
    for group in include_title_groups:
        if all(word in title for word in group):
            return True
    return False


def title_has_exclude_title(title, exclude_titles):
    title = title.lower()
    return any(t in title for t in exclude_titles)


def is_company_blocked(company, blocked_companies):
    company = company.lower()
    return company in blocked_companies


def is_probable_job_detail_url(url):
    url = url.lower()

    log(f"🔎 checking job detail URL: {url}", "DEBUG");

    if not (url.startswith("https://") or url.startswith("www.")):
        log(f"doesn't start with https:// or www.", "DEBUG");
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
        log(f"passed good patterns", "DEBUG");
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
        log(f"encountered bad patterns", "DEBUG")
        return False

    return True
