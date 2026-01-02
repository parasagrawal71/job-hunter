from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright._impl._errors import Error as PlaywrightError


def fetch_html(url: str):
    """
    Robust HTML fetcher.

    Returns:
      html: str | None
      error: str | None
    NEVER throws.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            bypass_csp=True,
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.route(
            "**/*",
            lambda route: route.continue_(
                headers={
                    **route.request.headers,
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                }
            ),
        )

        page.set_default_navigation_timeout(60000)
        page.set_default_timeout(60000)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # 🔑 Try waiting for known job-card selectors (best effort)
            JOB_SELECTORS = [
                "a.apply-card",          # Zeta
                "[data-testid='job']",   # some ATS
                "a[href*='job']",        # generic fallback
                "a[href*='careers']",
            ]
            for selector in JOB_SELECTORS:
                try:
                    page.wait_for_selector(selector, timeout=8000)
                    break
                except Exception:
                    pass

            page.wait_for_timeout(2000)
            html = page.content()

            return html, None

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            error_msg = str(e).split("\n")[0]

            print(f"⚠️ Playwright failed for URL: {url}")
            print(f"⚠️ Reason: {error_msg}")

            return None, error_msg

        finally:
            context.close()
            browser.close()
