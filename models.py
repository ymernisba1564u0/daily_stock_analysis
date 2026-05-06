"""SQLAlchemy ORM models for daily stock analysis."""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    BigInteger,
    Numeric,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from database import Base


class Stock(Base):
    """Represents a stock/security listed on an exchange."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True, comment="Ticker symbol, e.g. AAPL")
    name = Column(String(255), nullable=False, comment="Full company name")
    exchange = Column(String(50), nullable=True, comment="Exchange name, e.g. NASDAQ")
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Stock(symbol={self.symbol!r}, name={self.name!r})>"


class DailyPrice(Base):
    """Daily OHLCV price data for a stock."""

    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)

    open_price = Column(Numeric(12, 4), nullable=True, comment="Opening price")
    high_price = Column(Numeric(12, 4), nullable=True, comment="Daily high")
    low_price = Column(Numeric(12, 4), nullable=True, comment="Daily low")
    close_price = Column(Numeric(12, 4), nullable=False, comment="Closing price")
    adj_close = Column(Numeric(12, 4), nullable=True, comment="Adjusted closing price")
    volume = Column(BigInteger, nullable=True, comment="Trading volume")

    # Derived metrics stored for quick access
    change_pct = Column(Float, nullable=True, comment="Percentage change from previous close")
    amplitude = Column(Float, nullable=True, comment="(high - low) / prev_close * 100")
    turnover_rate = Column(Float, nullable=True, comment="Volume / total shares * 100")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_daily_price_symbol_date"),
        Index("ix_daily_prices_date_symbol", "trade_date", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<DailyPrice(symbol={self.symbol!r}, date={self.trade_date}, close={self.close_price})>"


class AnalysisResult(Base):
    """Stores computed technical analysis results for a given stock and date."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    analysis_date = Column(Date, nullable=False, index=True)

    # Moving averages
    ma5 = Column(Float, nullable=True, comment="5-day simple moving average")
    ma10 = Column(Float, nullable=True)
    ma20 = Column(Float, nullable=True)
    ma60 = Column(Float, nullable=True)

    # Momentum indicators
    rsi_14 = Column(Float, nullable=True, comment="14-day RSI")
    macd = Column(Float, nullable=True, comment="MACD line value")
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True, comment="MACD histogram")

    # Volatility
    bollinger_upper = Column(Float, nullable=True)
    bollinger_mid = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)

    # Signal summary
    signal = Column(String(20), nullable=True, comment="BUY / SELL / HOLD")
    score = Column(Float, nullable=True, comment="Composite score 0-100")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "analysis_date", name="uq_analysis_symbol_date"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisResult(symbol={self.symbol!r}, date={self.analysis_date}, signal={self.signal!r})>"
