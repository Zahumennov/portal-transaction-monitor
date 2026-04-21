import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

MOCK_API_DATA = {
    "00445790": {
        "name": "TESCO PLC",
        "status": "Active",
        "address": "Tesco House, Shire Park, Kestrel Way, Welwyn Garden City, AL7 1GA",
        "incorporation_date": "1947-11-27",
    },
    "00102498": {
        "name": "MARKS AND SPENCER PLC",
        "status": "Active",
        "address": "Waterside House, 35 North Wharf Road, London, W2 1NW",
        "incorporation_date": "1926-09-08",
    },
}


async def fetch_company_from_api(company_number: str, jurisdiction_code: str = "gb") -> dict | None:
    """
    Fetches company data from API. Uses mock data for demo purposes.
    In production this would call the real OpenCorporates or registry API.
    """
    logger.info(f"Fetching company {company_number} from API")

    company = MOCK_API_DATA.get(company_number)
    if not company:
        logger.warning(f"Company {company_number} not found in API")
        return None

    return company


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