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

            # Note: yfinance sometimes returns an empty dict for delisted/invalid
            # symbols without raising an exception, so we check both price fields.
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
            start_date: Start of the date range (defaults to 30 days ago
                instead of the upstream default of 7 days -- I find a month
                of history more useful when exploring a new ticker).
            end_date: End of the date range (defaults to today).

        Returns:
            Number of new price records inserted.
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
