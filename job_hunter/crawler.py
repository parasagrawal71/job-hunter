from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright._impl._errors import Error as PlaywrightError


def fetch_html(url: str) -> str:
    """
    Robust HTML fetcher.
    NEVER throws — always returns HTML or empty string.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.set_default_navigation_timeout(60000)
        page.set_default_timeout(60000)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )
            page.wait_for_timeout(2000)
            html = page.content()

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            print(f"⚠️ Playwright failed for URL: {url}")
            print(f"⚠️ Reason: {e}")
            html = ""

        finally:
            context.close()
            browser.close()

        return html
