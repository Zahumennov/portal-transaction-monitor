import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func
from app.config import settings
from app.models.transaction import Company, Transaction, TransactionStatus
from app.tasks.monitor import monitor_company

logger = logging.getLogger(__name__)

router = APIRouter()

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """
    Dependency — provides database session for each request.
    """
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/")
async def get_transactions(
    limit: int = 20,
    status: str = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of recent transactions with optional status filter.
    """
    query = select(Transaction).order_by(Transaction.created_at.desc()).limit(limit)

    if status:
        try:
            status_enum = TransactionStatus[status.upper()]
            query = query.where(Transaction.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {[s.value for s in TransactionStatus]}",
            )

    result = await session.execute(query)
    transactions = result.scalars().all()

    return [
        {
            "id": t.id,
            "company_id": t.company_id,
            "status": t.status.value,
            "anomalies": t.anomalies,
            "retry_count": t.retry_count,
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """
    Returns success rate and transaction counts by status.
    """
    total = await session.scalar(select(func.count(Transaction.id)))

    counts = {}
    for status in TransactionStatus:
        count = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.status == status)
        )
        counts[status.value] = count

    success_rate = (
        round(counts.get("SUCCESS", 0) / total * 100, 2) if total > 0 else 0
    )

    return {
        "total_transactions": total,
        "success_rate": f"{success_rate}%",
        "by_status": counts,
    }


@router.post("/run")
async def run_transaction(
    company_number: str,
    jurisdiction_code: str = "gb",
    session: AsyncSession = Depends(get_session),
):
    """
    Manually triggers a monitoring transaction for a given company number.
    """
    # Find or create company
    result = await session.execute(
        select(Company).where(Company.company_number == company_number)
    )
    company = result.scalar_one_or_none()

    if not company:
        company = Company(
            company_number=company_number,
            jurisdiction_code=jurisdiction_code,
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)

    # Trigger Celery task
    monitor_company.delay(company.id)

    return {
        "message": f"Monitoring task triggered for company {company_number}",
        "company_id": company.id,
    }