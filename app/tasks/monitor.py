import logging
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings
from app.scraper.companies_house import scrape_company
from app.verifier.checker import fetch_company_from_api, compare_data
from app.models.transaction import Company, Transaction, TransactionStatus

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "portal_monitor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Synchronous engine for Celery tasks
engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
)

# Beat schedule — run every 10 minutes
celery_app.conf.beat_schedule = {
    "monitor-all-companies": {
        "task": "app.tasks.monitor.monitor_all_companies",
        "schedule": crontab(minute="*/10"),
    }
}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def monitor_company(self, company_id: int):
    """
    Celery task — scrapes and verifies a single company.
    Retries up to 3 times with 30 second delay on failure.
    """
    with Session(engine) as session:
        company = session.get(Company, company_id)
        if not company:
            logger.error(f"Company {company_id} not found in database")
            return

        transaction = Transaction(
            company_id=company.id,
            status=TransactionStatus.RETRY,
            retry_count=self.request.retries,
        )
        session.add(transaction)
        session.commit()

        try:
            import asyncio

            # Run async scraper in sync context
            web_data = asyncio.run(
                scrape_company(company.company_number, company.jurisdiction_code)
            )

            if not web_data:
                raise ValueError(f"Scraper returned no data for {company.company_number}")

            # Fetch from API
            api_data = asyncio.run(
                fetch_company_from_api(company.company_number, company.jurisdiction_code)
            )

            if not api_data:
                raise ValueError(f"API returned no data for {company.company_number}")

            # Update company name if not set
            if not company.name and web_data.get("name"):
                company.name = web_data["name"]

            # Compare and detect anomalies
            anomalies = compare_data(web_data, api_data)

            transaction.web_data = web_data
            transaction.api_data = api_data
            transaction.anomalies = anomalies
            transaction.status = (
                TransactionStatus.ANOMALY if anomalies else TransactionStatus.SUCCESS
            )

            session.commit()
            logger.info(f"Company {company.company_number} — {transaction.status.value}")

        except Exception as e:
            logger.error(f"Task failed for company {company_id}: {e}")
            transaction.status = TransactionStatus.FAILED
            session.commit()

            # Retry if attempts remaining
            raise self.retry(exc=e)


@celery_app.task
def monitor_all_companies():
    """
    Celery Beat task — fetches all companies from DB and triggers monitor_company for each.
    """
    with Session(engine) as session:
        companies = session.execute(select(Company)).scalars().all()
        logger.info(f"Scheduling monitoring for {len(companies)} companies")

        for company in companies:
            monitor_company.delay(company.id)