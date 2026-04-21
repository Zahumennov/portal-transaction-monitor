from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class TransactionStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    ANOMALY = "ANOMALY"
    FAILED = "FAILED"
    RETRY = "RETRY"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(10), default="gb")
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus), nullable=False
    )
    web_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    api_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    anomalies: Mapped[dict] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="transactions")