from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import db


class Trade(db.Model):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    alerts: Mapped[List["ComplianceAlert"]] = relationship(
        back_populates="trade", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "trade_date": self.trade_date.isoformat(),
            "account": self.account,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "price": float(self.price),
            "created_at": self.created_at.isoformat(),
        }


class ComplianceAlert(db.Model):
    __tablename__ = "compliance_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="WARNING")
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    trade: Mapped["Trade"] = relationship(back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "rule": self.rule_name,
            "severity": self.severity,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }
