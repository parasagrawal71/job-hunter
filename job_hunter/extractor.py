import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from job_hunter.crawler import fetch_html
from job_hunter.utils.log import log
from job_hunter.utils.utils import normalize_str_into_words, match_words


def extract_job_links(listing_html: str, base_url: str) -> list[dict]:
    log("🔗 Extracting job links", "DEBUG")
    """
    Step 1: Extract title + job detail link from listing page
    """
    soup = BeautifulSoup(listing_html, "html.parser")
    jobs = []

    for a in soup.select("a"):
        title = a.get_text(separator=" ", strip=True)  # 1️⃣ Try direct anchor text
        # log(f"🔎 direct anchor text - title: {title}", "DEBUG")
        href = a.get("href")

        # 2️⃣ If anchor text is empty, try nested title-like elements
        if not title:
            # log(f"🔎 looking for nested title-like elements: {a}", "DEBUG")
            # Find any descendant whose class contains "title"
            title_candidate = a.select_one(
                '[class*="title"], [class*="Title"], [class*="TITLE"]'
            )
            # log(f"🔎 title_candidate: {title_candidate}", "DEBUG")

            if title_candidate:
                title = title_candidate.get_text(separator=" ", strip=True)
            log(f"🔎 title: {title}", "DEBUG")

        if not title or not href:
            continue

        if len(title) < 6:
            continue

        job_url = urljoin(base_url, href)

        jobs.append({"title": title, "link": job_url})

    log(f"📦 Raw job links found: {len(jobs)}")
    return jobs


async def extract_job_details_and_locations(job_url: str, config) -> dict:
    log("🌐 Fetching job detail page...", "DEBUG")
    """
    Step 2: Visit job detail page and extract:
    - full description
    - job locations

    Excludes footer-like sections generically.
    """
    html, error = await fetch_html(job_url)
    if not html or error:
        return {
            "description": "",
            "locations": [],
            "error": error,
        }

    soup = BeautifulSoup(html, "html.parser")

    # Remove footer-like sections generically
    for el in soup.select('[class*="footer"], [class*="Footer"], [class*="FOOTER"]'):
        el.decompose()

    # also remove semantic footer tags
    for el in soup.find_all("footer"):
        el.decompose()

    # -------------------------
    # Extract description
    # -------------------------
    text = soup.get_text(separator=" ", strip=True)
    log(f"📝 Description length: {len(text)} chars", "DEBUG")

    description = text.lower()

    # -------------------------
    # Extract locations
    # -------------------------
    log("📍 Extracting job locations...", "DEBUG")

    locations = set()

    # 🔑 Match any element with class containing "location"
    location_elements = soup.select(
        '[class*="location"], [class*="Location"], [class*="LOCATION"]'
    )

    for el in location_elements:
        # Remove svg/icons inside location blocks
        for svg in el.find_all("svg"):
            svg.decompose()

        # Normalize spaces
        loc_text = el.get_text(separator=" ", strip=True)
        loc_text = re.sub(r"\s+", " ", loc_text)

        # Skip empty / junk
        if not loc_text or len(loc_text) < 2:
            continue

        for loc in loc_text.split(","):
            locations.add(loc.strip().lower())

    normalized_locations = normalize_str_into_words(list(locations))
    log(
        f"📍 Extracted locations from location_elements: {normalized_locations}",
        "DEBUG",
    )

    # -------------------------
    # Fallback: infer from description
    # -------------------------
    if len(normalized_locations) == 0:
        LOCATION_ALIASES = {
            "bangalore": ["bangalore", "bengaluru", "blr"],
            "remote": ["remote", "work from home", "wfh", "anywhere"],
            "india": ["india"],
        }

        for loc in config["blocked_locations"]:
            LOCATION_ALIASES[loc] = [loc]

        all_locations = list(config["allowed_locations"]) + list(
            config["blocked_locations"]
        )

        for canonical, aliases in LOCATION_ALIASES.items():
            if canonical not in all_locations:
                continue
            if match_words(description, aliases):
                normalized_locations.append(canonical)

        log(
            f"📍 Extracted locations using (canonical, aliases) logic: {normalized_locations}",
            "DEBUG",
        )

    return {
        "description": text,
        "locations": normalized_locations,
        "error": None,
    }


def extract_yoe_from_description(description: str):
    log("📅 Extracting years of experience...", "DEBUG")
    """
    Extracts Years of Experience from job description.
    Supports:
      - 3+ years
      - 5 years
      - 4 yrs
      - 2-3 years
      - at least 6 years
    Returns: int or None
    """
    if not description:
        return None

    text = description.lower()

    patterns = [
        r"(\d+)\s*\+\s*(?:years?|yrs?)",  # 3+ years
        r"at least\s+(\d+)\s*(?:years?|yrs?)",  # at least 6 years
        r"(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)",  # 2-3 years
        r"(\d+)\s*(?:years?|yrs?)",  # 5 years / 4 yrs
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # For ranges like 2-3 years → take minimum (2)
            log(f"📊 Extracted YOE: {match.group(1)}", "DEBUG")
            return int(match.group(1))

    return None
