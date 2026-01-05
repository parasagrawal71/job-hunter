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
    try:
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

                # expand "Show more"
                await _expand_dynamic_listings(page)

                await page.wait_for_timeout(1000)
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

    except Exception as e:
        # 🔑 Catches browser launch failures, Playwright startup issues, OS errors, etc.
        error_msg = str(e).split("\n")[0]
        log(f"⚠️ Playwright failed for URL: {url}")
        log(f"⚠️ Reason: {error_msg}")
        return None, error_msg


async def _expand_dynamic_listings(page):
    KEYWORDS = ["show more", "load more", "more jobs"]
    prev_anchor_count = 0
    max_clicks = 25

    for _ in range(max_clicks):
        button = await _find_element_by_text(page, KEYWORDS)

        if not button:
            log("⚠️ No Show more button found", "DEBUG")
            break

        log(f"🔑 Found Show more button: {button}", "DEBUG")

        try:
            await button.scroll_into_view_if_needed()
            await button.click()
        except Exception:
            break

        try:
            await page.wait_for_function(
                f"document.querySelectorAll('a').length > {prev_anchor_count}",
                timeout=3000,
            )
        except Exception:
            break

        prev_anchor_count = await page.evaluate("document.querySelectorAll('a').length")


async def _find_element_by_text(page, keywords):
    """
    Finds the most specific visible clickable element
    whose text contains pagination keywords.
    """
    script = """
    (keywords) => {
        const candidates = Array.from(
            document.querySelectorAll('button, a, div, span')
        );

        const matches = candidates.filter(el => {
            if (!el.offsetParent) return false; // not visible

            const text = (el.innerText || "").toLowerCase();
            if (!keywords.some(k => text.includes(k))) return false;

            // Must look clickable
            const style = window.getComputedStyle(el);
            const clickable =
                el.tagName === 'BUTTON' ||
                el.tagName === 'A' ||
                el.getAttribute('role') === 'button' ||
                typeof el.onclick === 'function' ||
                style.cursor === 'pointer';

            if (!clickable) return false;

            // Reject very large containers (like #__next)
            const childCount = el.querySelectorAll('*').length;
            if (childCount > 10) return false;

            return true;
        });

        // Prefer the smallest (most specific) element
        matches.sort(
            (a, b) =>
                a.querySelectorAll('*').length -
                b.querySelectorAll('*').length
        );

        return matches[0] || null;
    }
    """
    return await page.evaluate_handle(script, keywords)


async def fetch_html_single_page(url: str):
    """
    Robust HTML fetcher.

    Returns:
      html: str | None
      error: str | None
    NEVER throws.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                bypass_csp=True,
                ignore_https_errors=True,
            )
            page = await context.new_page()

            page.set_default_navigation_timeout(60000)
            page.set_default_timeout(60000)

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                # ⏳ Small buffer to allow late JS rendering
                await page.wait_for_timeout(1500)

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

    except Exception as e:
        error_msg = str(e).split("\n")[0]
        log(f"⚠️ Playwright failed for URL: {url}")
        log(f"⚠️ Reason: {error_msg}")
        return None, error_msg
