import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from job_hunter.crawler import fetch_html_single_page
from job_hunter.utils.log import log
from job_hunter.utils.utils import normalize_str_into_words, match_words


def extract_job_links(listing_html: str, base_url: str) -> list[dict]:
    log("🔗 Extracting job links", "DEBUG")

    soup = BeautifulSoup(listing_html, "html.parser")
    jobs = []

    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        # 1️⃣ Try extracting title directly from <a>
        anchor_text_raw = a.get_text(separator=" ", strip=True)
        anchor_text = anchor_text_raw.lower()

        if anchor_text in {"apply", "apply now", "view job"}:
            title = None
        else:
            title = anchor_text_raw if len(anchor_text_raw) >= 6 else None

        # 2️⃣ If title not found or weak, walk up parents and rank candidates
        if not title or len(title) < 6:
            parent = a.parent

            for _ in range(4):  # walk up max 4 levels
                if not parent:
                    break

                candidates = parent.select("h1, h2, h3, h4, h5, h6, p, span")

                best_title = None
                best_score = -1

                for el in candidates:
                    text = el.get_text(separator=" ", strip=True)
                    if not text or len(text) < 6:
                        continue

                    lower = text.lower()

                    # Skip CTA / noise
                    if "apply" in lower:
                        continue

                    score = 0

                    # Prefer semantic headings
                    if el.name.startswith("h"):
                        score += 100

                    # Prefer longer, descriptive titles
                    score += min(len(text), 60)

                    # Penalize badge-like / category text
                    if len(text.split()) <= 2:
                        score -= 20

                    # Penalize uppercase labels
                    if text.isupper():
                        score -= 10

                    if score > best_score:
                        best_score = score
                        best_title = text

                if best_title:
                    title = best_title
                    break

                parent = parent.parent

        if not title:
            continue

        job_url = urljoin(base_url, href)

        jobs.append(
            {
                "title": title,
                "link": job_url,
            }
        )

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
    html, error = await fetch_html_single_page(job_url)
    if not html or error:
        return {
            "description": "",
            "extracted_locations": [],
            "locations_from_description": [],
            "all_extracted_locations": [],
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

    extracted_locations = set()

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
            extracted_locations.add(loc.strip().lower())

    normalized_extracted_locations = normalize_str_into_words(list(extracted_locations))
    log(
        f"📍 Extracted locations from location_elements: {normalized_extracted_locations}",
        "DEBUG",
    )

    # -------------------------
    # Fallback: infer from description
    # -------------------------
    normalized_locations_from_description = []
    if len(normalized_extracted_locations) == 0:
        locations_from_description = set()
        LOCATION_ALIASES = {
            # allowed locations
            "bangalore": ["bangalore", "bengaluru", "blr"],
            "remote": ["remote", "work from home", "wfh", "anywhere"],
            "india": ["india"],
            # other locations
            "hyderabad": ["hyderabad", "hyd"],
            "pune": ["pune", "poona"],
            "chennai": ["chennai", "madras"],
            "gurgaon": ["gurgaon", "gurugram", "ggn"],
            "noida": ["noida"],
            "delhi": ["delhi", "new delhi", "ncr", "delhi ncr"],
            "mumbai": ["mumbai", "bombay"],
            "ahmedabad": ["ahmedabad", "amdavad"],
            "indore": ["indore"],
            "jaipur": ["jaipur"],
            "kochi": ["kochi", "cochin"],
            "trivandrum": ["trivandrum", "thiruvananthapuram"],
            "coimbatore": ["coimbatore", "kovai"],
            "trichy": ["trichy", "tiruchirappalli"],
            "bhubaneswar": ["bhubaneswar", "bbsr"],
            "kolkata": ["kolkata", "calcutta"],
        }

        for loc in config["blocked_locations"]:
            LOCATION_ALIASES[loc] = [loc]

        all_locations = (
            list(config["allowed_locations"])
            + list(config["blocked_locations"])
            + list(config["other_locations"])
            + list(LOCATION_ALIASES.keys())
        )

        for canonical, aliases in LOCATION_ALIASES.items():
            if canonical not in all_locations:
                continue
            if match_words(description, aliases):
                locations_from_description.add(canonical)

        normalized_locations_from_description = normalize_str_into_words(
            list(locations_from_description)
        )
        log(
            f"📍 Extracted locations using (canonical, aliases) logic: {normalized_locations_from_description}",
            "DEBUG",
        )

    return {
        "description": text,
        "extracted_locations": normalized_extracted_locations,
        "locations_from_description": normalized_locations_from_description,
        "all_extracted_locations": list(
            set(normalized_extracted_locations + normalized_locations_from_description)
        ),
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
