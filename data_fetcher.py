"""Data fetcher module for retrieving stock data from external APIs.

This module handles fetching daily stock prices and company information
from financial data providers (e.g., Yahoo Finance via yfinance).
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session

from config import Config
from database import DatabaseManager
from models import Stock, DailyPrice

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches and persists stock data from Yahoo Finance."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def fetch_stock_info(self, symbol: str) -> Optional[Stock]:
        """Fetch or update basic stock information for a given symbol.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL').

        Returns:
            The Stock ORM object, or None if the symbol is invalid.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
                logger.warning("No valid data found for symbol: %s", symbol)
                return None

            with self.db_manager.get_session() as session:
                stock = session.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                if stock is None:
                    stock = Stock(
                        symbol=symbol.upper(),
                        name=info.get("longName") or info.get("shortName", symbol),
                        sector=info.get("sector"),
                        industry=info.get("industry"),
                        market_cap=info.get("marketCap"),
                        currency=info.get("currency", "USD"),
                    )
                    session.add(stock)
                    logger.info("Created new stock record for %s", symbol)
                else:
                    stock.name = info.get("longName") or info.get("shortName", stock.name)
                    stock.sector = info.get("sector", stock.sector)
                    stock.industry = info.get("industry", stock.industry)
                    stock.market_cap = info.get("marketCap", stock.market_cap)
                    logger.info("Updated stock record for %s", symbol)

                session.commit()
                session.refresh(stock)
                return stock

        except Exception as exc:
            logger.error("Failed to fetch stock info for %s: %s", symbol, exc)
            return None

    def fetch_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Fetch and store daily OHLCV price data for a stock.

        Args:
            symbol: Stock ticker symbol.
            start_date: Start of the date range (defaults to 30 days ago).
            end_date: End of the date range (defaults to today).

        Returns:
            Number of new price records inserted.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            ticker = yf.Ticker(symbol)
            df: pd.DataFrame = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                auto_adjust=True,
            )

            if df.empty:
                logger.warning("No price data returned for %s in range %s – %s", symbol, start_date, end_date)
                return 0

            inserted = 0
            with self.db_manager.get_session() as session:
                stock = session.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                if stock is None:
                    logger.error("Stock %s not found in DB; fetch info first.", symbol)
                    return 0

                for ts, row in df.iterrows():
                    price_date = ts.date() if hasattr(ts, "date") else ts
                    exists = (
                        session.query(DailyPrice)
                        .filter(DailyPrice.stock_id == stock.id, DailyPrice.date == price_date)
                        .first()
                    )
                    if exists:
                        continue

                    daily = DailyPrice(
                        stock_id=stock.id,
                        date=price_date,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                    session.add(daily)
                    inserted += 1

                session.commit()
                logger.info("Inserted %d new price records for %s", inserted, symbol)
                return inserted

        except Exception as exc:
            logger.error("Failed to fetch daily prices for %s: %s", symbol, exc)
            return 0

    def refresh_stocks(self, symbols: List[str], lookback_days: int = 30) -> None:
        """Convenience method to refresh info and prices for multiple symbols.

        Args:
            symbols: List of ticker symbols to refresh.
            lookback_days: Number of historical days to fetch.
        """
        for symbol in symbols:
            logger.info("Refreshing data for %s", symbol)
            self.fetch_stock_info(symbol)
            self.fetch_daily_prices(symbol, start_date=date.today() - timedelta(days=lookback_days))
