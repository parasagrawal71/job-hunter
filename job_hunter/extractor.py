import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from job_hunter.crawler import fetch_html
from job_hunter.utils.log import log


def extract_job_links(listing_html: str, base_url: str) -> list[dict]:
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
            log(f"🔎 looking for nested title-like elements: {a}", "DEBUG")
            # Find any descendant whose class contains "title"
            title_candidate = a.select_one(
                '[class*="title"], [class*="Title"], [class*="TITLE"]'
            )
            log(f"🔎 title_candidate: {title_candidate}", "DEBUG")

            if title_candidate:
                title = title_candidate.get_text(separator=" ", strip=True)
            log(f"🔎 title: {title}", "DEBUG")

        if not title or not href:
            continue

        if len(title) < 6:
            continue

        job_url = urljoin(base_url, href)

        jobs.append({"title": title, "link": job_url})

    return jobs


def extract_job_details(job_url: str) -> dict:
    """
    Step 2: Visit job detail page and extract full description
    Excludes footer-like sections generically.
    """
    html, error = fetch_html(job_url)
    if not html or error:
        return {
            "description": "",
            "error": error,
        }
    soup = BeautifulSoup(html, "html.parser")

    # 🔑 Remove footer-like sections generically
    for el in soup.select(
        '[class*="footer"], [class*="Footer"], [class*="FOOTER"]'
    ):
        el.decompose()

    # Optional: also remove semantic footer tags
    for el in soup.find_all("footer"):
        el.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return {"description": text}


def extract_yoe_from_description(description: str):
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
            return int(match.group(1))

    return None


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
