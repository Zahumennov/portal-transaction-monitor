import logging
from playwright.async_api import async_playwright, Page
from playwright_stealth import stealth_async
from app.config import settings

logger = logging.getLogger(__name__)


async def scrape_company(company_number: str, jurisdiction_code: str = "gb") -> dict | None:
    """
    Navigates to the portal, finds a company by number and returns data from the web page.
    """
    url = f"{settings.portal_base_url}/companies/{jurisdiction_code}/{company_number}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            logger.info(f"Scraping company {company_number} from {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            await page.wait_for_selector("h1.wrapping_heading", timeout=10000)

            if await page.locator("h1.error").count() > 0:
                logger.warning(f"Company {company_number} not found on portal")
                return None

            name = await page.locator("h1.wrapping_heading").text_content()
            status = await _get_dd_value(page, "dd.company_status")
            company_type = await _get_dd_value(page, "dd.company_type")
            jurisdiction = await _get_dd_value(page, "dd.jurisdiction")
            incorporation_date = await _get_dd_value(page, "dd.incorporation_date")

            result = {
                "name": name.strip() if name else None,
                "status": status,
                "company_type": company_type,
                "jurisdiction": jurisdiction,
                "incorporation_date": incorporation_date,
            }

            logger.info(f"Successfully scraped company {company_number}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to scrape company {company_number}: {e}")
            raise

        finally:
            await browser.close()


async def _get_dd_value(page: Page, selector: str) -> str | None:
    """
    Gets text content of an element by CSS selector.
    """
    try:
        locator = page.locator(selector)
        if await locator.count() > 0:
            return (await locator.first.text_content()).strip()
        return None
    except Exception:
        return None


async def _get_attribute_value(page: Page, label: str) -> str | None:
    """
    Helper function — finds a value by label in the company attributes table.
    """
    try:
        locator = page.locator(f"dt:has-text('{label}') + dd")
        if await locator.count() > 0:
            return (await locator.text_content()).strip()
        return None
    except Exception:
        return None