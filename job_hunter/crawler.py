from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from playwright._impl._errors import Error as PlaywrightError
from job_hunter.utils.log import log


async def fetch_html(url: str):
    """
    Robust HTML fetcher.

    Returns:
      html: str | None
      error: str | None
    NEVER throws.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            bypass_csp=True,
            ignore_https_errors=True,
        )
        page = await context.new_page()

        await page.route(
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
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # 🔑 Try waiting for known job-card selectors (best effort)
            JOB_SELECTORS = [
                "a.apply-card",  # Zeta
                "[data-testid='job']",  # some ATS
                "a[href*='job']",  # generic fallback
                "a[href*='careers']",
            ]

            for selector in JOB_SELECTORS:
                try:
                    await page.wait_for_selector(selector, timeout=8000)
                    break
                except Exception:
                    pass

            await page.wait_for_timeout(2000)
            html = await page.content()

            return html, None

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            error_msg = str(e).split("\n")[0]

            log(f"⚠️ Playwright failed for URL: {url}")
            log(f"⚠️ Reason: {error_msg}")

            return None, error_msg

        finally:
            await context.close()
            await browser.close()
