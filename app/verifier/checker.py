import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def fetch_company_from_api(company_number: str, jurisdiction_code: str = "gb") -> dict | None:
    """
    Fetches company data from OpenCorporates REST API.
    """
    url = f"{settings.opencorporates_api_url}/companies/{jurisdiction_code}/{company_number}"

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Fetching company {company_number} from API: {url}")
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

            data = response.json()
            company = data["results"]["company"]

            return {
                "name": company.get("name"),
                "status": company.get("current_status"),
                "address": company.get("registered_address_in_full"),
                "incorporation_date": company.get("incorporation_date"),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"API returned error for company {company_number}: {e}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch company {company_number} from API: {e}")
            return None


def compare_data(web_data: dict, api_data: dict) -> dict | None:
    """
    Compares web scraped data against API data.
    Returns a dict of anomalies if differences found, otherwise None.
    """
    anomalies = {}
    fields_to_check = ["name", "status", "incorporation_date"]

    for field in fields_to_check:
        web_value = _normalize(web_data.get(field))
        api_value = _normalize(api_data.get(field))

        if web_value and api_value and web_value != api_value:
            anomalies[field] = {
                "web": web_data.get(field),
                "api": api_data.get(field),
            }

    return anomalies if anomalies else None


def _normalize(value: str | None) -> str | None:
    """
    Normalizes string for comparison — lowercase and stripped.
    """
    if value is None:
        return None
    return value.lower().strip()