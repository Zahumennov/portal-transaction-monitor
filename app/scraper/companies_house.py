import logging
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)


async def scrape_company(company_number: str, jurisdiction_code: str = "gb") -> dict | None:
    """
    Navigates to OpenCorporates, finds a company by number and returns data from the web page.
    """
    url = f"https://opencorporates.com/companies/{jurisdiction_code}/{company_number}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logger.info(f"Scraping company {company_number} from {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Check if the page found the company
            if await page.locator("h1.error").count() > 0:
                logger.warning(f"Company {company_number} not found on OpenCorporates")
                return None

            # Extract company name
            name = await page.locator("h1[itemprop='name']").text_content()

            # Extract status
            status = await _get_attribute_value(page, "Status")

            # Extract registered address
            address = await _get_attribute_value(page, "Registered Address")

            # Extract incorporation date
            incorporation_date = await _get_attribute_value(page, "Incorporation Date")

            result = {
                "name": name.strip() if name else None,
                "status": status,
                "address": address,
                "incorporation_date": incorporation_date,
            }

            logger.info(f"Successfully scraped company {company_number}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to scrape company {company_number}: {e}")
            raise

        finally:
            await browser.close()


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