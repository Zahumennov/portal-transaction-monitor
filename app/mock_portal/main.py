from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

COMPANIES = {
    "00445790": {
        "name": "TESCO PLC",
        "status": "Active",
        "company_type": "Public Limited Company",
        "jurisdiction": "United Kingdom",
        "incorporation_date": "1947-11-27",
    },
    "00102498": {
        "name": "MARKS AND SPENCER PLC",
        "status": "Active",
        "company_type": "Public Limited Company",
        "jurisdiction": "United Kingdom",
        "incorporation_date": "1926-09-08",
    },
    "00445790_anomaly": {
        "name": "TESCO PLC",
        "status": "Dissolved",  # Anomaly — different from API
        "company_type": "Public Limited Company",
        "jurisdiction": "United Kingdom",
        "incorporation_date": "1947-11-27",
    },
}


@app.get("/companies/{jurisdiction}/{company_number}", response_class=HTMLResponse)
async def company_page(jurisdiction: str, company_number: str):
    """
    Mock portal page that mimics OpenCorporates HTML structure.
    """
    company = COMPANIES.get(company_number)

    if not company:
        return HTMLResponse(
            content="<html><body><h1 class='error'>Company not found</h1></body></html>",
            status_code=404,
        )

    html = f"""
    <html>
    <body>
        <h1 class="wrapping_heading fn org" itemprop="name">{company["name"]}</h1>
        <dl>
            <dt>Company Number</dt>
            <dd class="company_number">{company_number}</dd>

            <dt>Status</dt>
            <dd class="company_status">{company["status"]}</dd>

            <dt>Company Type</dt>
            <dd class="company_type">{company["company_type"]}</dd>

            <dt>Jurisdiction</dt>
            <dd class="jurisdiction">{company["jurisdiction"]}</dd>

            <dt>Incorporation Date</dt>
            <dd class="incorporation_date">{company["incorporation_date"]}</dd>
        </dl>
    </body>
    </html>
    """
    return HTMLResponse(content=html)