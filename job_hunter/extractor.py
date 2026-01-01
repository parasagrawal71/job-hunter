import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from job_hunter.crawler import fetch_html


def extract_job_links(listing_html: str, base_url: str) -> list[dict]:
    """
    Step 1: Extract title + job detail link from listing page
    """
    soup = BeautifulSoup(listing_html, "html.parser")
    jobs = []

    for a in soup.select("a"):
        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        if len(title) < 6:
            continue

        job_url = urljoin(base_url, href)

        jobs.append({
            "title": title,
            "link": job_url
        })

    return jobs


def extract_job_details(job_url: str) -> dict:
    """
    Step 2: Visit job detail page and extract full description
    """
    html = fetch_html(job_url)
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator=" ", strip=True)

    return {
        "description": text
    }


def extract_yoe(text: str):
    match = re.search(r'(\d+)\+?\s+years?', text.lower())
    return int(match.group(1)) if match else None
