import re

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
            f"location not allowed (expected one of {config['allowed_locations']})"
        )

    return True, None



def calculate_score(job, config):
    experience_score = 1 if job.get("yoe") else 0
    keyword_score = len(job["matched_keywords"]) / len(config["include_keywords"])

    score = (
        experience_score * 0.3 +
        keyword_score * 0.7
    )

    return round(score * 100, 2)
