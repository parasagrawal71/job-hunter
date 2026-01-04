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
    title = job["title"].lower()

    # ❌ Blocked locations (log exact match)
    for loc in config.get("blocked_locations", []):
        pass
        # # description contains blocked location
        # if contains_whole_word(desc, loc):
        #     return False, f"blocked location detected in description: '{loc}'"

    # # ❌ Excluded tech keywords
    # for k in config["exclude_keywords"]:
    #     if contains_whole_word(desc, k):
    #         return False, f"excluded keyword found: '{k}'"

    # ❌ Location not allowed (positive filter)
    isAnyLocFound = False
    for loc in config.get("allowed_locations", []):
        if contains_whole_word(desc, loc):
            isAnyLocFound = True
    if isAnyLocFound == False:
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


def is_company_blocked(company, blocked_companies):
    company = company.lower()
    return company in blocked_companies


def is_probable_job_detail_url(url):
    url = url.lower()

    log(f"🔎 checking job detail URL: {url}", "DEBUG")

    if not (url.startswith("https://") or url.startswith("www.")):
        log(f"doesn't start with https:// or www.", "DEBUG")
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
        log(f"passed good patterns", "DEBUG")
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

def extracted_locations_has_blocked_locations(extracted_locations, blocked_locations):
    for loc in extracted_locations:
        loc = loc.lower()
        if loc in blocked_locations:
            log(f"blocked location found in extracted locations: '{loc}'", "DEBUG")
            return True
    return False


def title_matches_include_groups(title, include_title_groups):
    words = set(re.findall(r"\b\w+\b", title.lower()))
    for group in include_title_groups:
        if all(word in words for word in group):
            return True
    return False


def title_matcher(title, config):
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
