"""
Symbol Extractor Tool for identifying and validating stock symbols from text.
"""

import re
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from framework.mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class SymbolExtractorTool(BaseTool):
    """
    Tool for extracting and validating stock symbols from natural language text.

    Features:
    - Extract stock symbols from various text formats
    - Validate symbols against known patterns
    - Handle company names and convert to symbols
    - Filter out common false positives
    - Provide confidence scores for extracted symbols
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="symbol_extractor",
            description="Extract and validate stock symbols from text input",
            version="1.0.0",
            **kwargs
        )
        self.category = "text_processing"

        # Common company name to symbol mappings
        self.company_mappings = {
            # Major tech companies
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "nvidia": "NVDA",
            "intel": "INTC",
            "amd": "AMD",
            "oracle": "ORCL",
            "salesforce": "CRM",
            "adobe": "ADBE",

            # Major financial companies
            "berkshire hathaway": "BRK.B",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "goldman sachs": "GS",
            "morgan stanley": "MS",
            "american express": "AXP",
            "visa": "V",
            "mastercard": "MA",

            # Major industrial companies
            "boeing": "BA",
            "caterpillar": "CAT",
            "general electric": "GE",
            "3m": "MMM",
            "honeywell": "HON",
            "lockheed martin": "LMT",
            "raytheon": "RTX",

            # Major consumer companies
            "coca cola": "KO",
            "pepsi": "PEP",
            "procter gamble": "PG",
            "johnson johnson": "JNJ",
            "pfizer": "PFE",
            "merck": "MRK",
            "walmart": "WMT",
            "home depot": "HD",
            "mcdonalds": "MCD",
            "nike": "NKE",
            "disney": "DIS",

            # Major energy companies
            "exxon": "XOM",
            "chevron": "CVX",
            "conocophillips": "COP",

            # ETFs and indices
            "s&p 500": "SPY",
            "sp500": "SPY",
            "nasdaq": "QQQ",
            "dow jones": "DIA",
            "russell 2000": "IWM",
            "vti": "VTI",
            "voo": "VOO"
        }

        # Common words that might look like symbols but aren't
        self.false_positives = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER",
            "WAS", "ONE", "OUR", "HAD", "BY", "WORD", "WHAT", "SOME", "WE", "OUT",
            "OTHER", "WERE", "WHICH", "THEIR", "TIME", "WILL", "HOW", "SAID", "EACH",
            "SHE", "MAY", "USE", "THAN", "NOW", "WAY", "WHO", "ITS", "DID", "GET",
            "HAS", "HIM", "OLD", "SEE", "TWO", "BOY", "LET", "PUT", "SAY", "TOO",
            "DAY", "MAN", "NEW", "TOP", "BUY", "SELL", "HOLD", "CALL", "PUT", "USD",
            "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "API", "CEO", "CFO",
            "CTO", "IPO", "SEC", "FDA", "FTC", "DOJ", "GDP", "CPI", "PPI", "PMI",
            "ETF", "REIT", "LLC", "INC", "CORP", "LTD", "PLC", "STOCK", "STOCKS",
            "MARKET", "TRADE", "TRADING", "INVEST", "INVESTMENT", "ANALYSIS", "ANALYZE",
            "HELP", "WANT", "NEED", "ABOUT", "WITH", "FROM", "MAKE", "GOOD", "BEST",
            "HIGH", "LOW", "PRICE", "PRICES", "RISK", "RISKS", "PROFIT", "LOSS",
            "MONEY", "CASH", "FUND", "FUNDS", "BOND", "BONDS", "OPTION", "OPTIONS",
            "FUTURE", "FUTURES", "INDEX", "INDICES", "SECTOR", "SECTORS", "INDUSTRY",
            "COMPANY", "COMPANIES", "BUSINESS", "BUSINESSES", "FINANCIAL", "FINANCE",
            "ECONOMIC", "ECONOMY", "MARKET", "MARKETS", "PORTFOLIO", "PORTFOLIOS",
            "ASSET", "ASSETS", "EQUITY", "EQUITIES", "DEBT", "CREDIT", "LOAN", "LOANS",
            "BANK", "BANKS", "INSURANCE", "REAL", "ESTATE", "COMMODITY", "COMMODITIES",
            "CURRENCY", "CURRENCIES", "FOREX", "CRYPTO", "CRYPTOCURRENCY", "BITCOIN",
            "ETHEREUM", "BLOCKCHAIN", "TECHNOLOGY", "TECH", "SOFTWARE", "HARDWARE",
            "INTERNET", "ONLINE", "DIGITAL", "DATA", "INFORMATION", "NEWS", "REPORT",
            "REPORTS", "EARNINGS", "REVENUE", "SALES", "GROWTH", "DECLINE", "INCREASE",
            "DECREASE", "CHANGE", "CHANGES", "TREND", "TRENDS", "PATTERN", "PATTERNS",
            "SIGNAL", "SIGNALS", "INDICATOR", "INDICATORS", "CHART", "CHARTS", "GRAPH",
            "GRAPHS", "VOLUME", "VOLUMES", "VOLATILITY", "VOLATILE", "STABLE", "UNSTABLE",
            "BULLISH", "BEARISH", "BULL", "BEAR", "LONG", "SHORT", "POSITION", "POSITIONS",
            "ORDER", "ORDERS", "LIMIT", "STOP", "MARKET", "EXECUTION", "FILL", "FILLED",
            "PENDING", "CANCELLED", "CANCELED", "REJECTED", "ACCEPTED", "APPROVED",
            "DENIED", "CONFIRMED", "UNCONFIRMED", "VALID", "INVALID", "EXPIRED", "ACTIVE",
            "INACTIVE", "OPEN", "CLOSE", "CLOSED", "OPENING", "CLOSING", "SESSION",
            "SESSIONS", "HOUR", "HOURS", "MINUTE", "MINUTES", "SECOND", "SECONDS",
            "TODAY", "YESTERDAY", "TOMORROW", "WEEK", "WEEKS", "MONTH", "MONTHS",
            "YEAR", "YEARS", "DAILY", "WEEKLY", "MONTHLY", "YEARLY", "ANNUAL", "QUARTERLY",
            "APPL", "TO", "IN", "ON", "AT", "OF", "IS", "BE", "AS", "OR", "SO", "IF",
            "UP", "DO", "GO", "NO", "MY", "ME", "HE", "IT", "US", "AM", "AN", "AS"
        }

    async def execute(self, text: str, **kwargs) -> List[str]:
        """
        Extract stock symbols from text.

        Args:
            text: Input text to extract symbols from

        Returns:
            List of extracted and validated stock symbols
        """
        try:
            if not text or not isinstance(text, str):
                return []

            # Extract symbols using multiple methods
            extracted_symbols = set()

            # Method 1: Direct symbol pattern matching
            direct_symbols = self._extract_direct_symbols(text)
            extracted_symbols.update(direct_symbols)

            # Method 2: Company name mapping
            company_symbols = self._extract_from_company_names(text)
            extracted_symbols.update(company_symbols)

            # Method 3: Context-based extraction
            context_symbols = self._extract_contextual_symbols(text)
            extracted_symbols.update(context_symbols)

            # Filter and validate symbols
            validated_symbols = self._validate_and_filter_symbols(list(extracted_symbols))

            # Sort by confidence/likelihood
            final_symbols = self._rank_symbols_by_confidence(validated_symbols, text)

            logger.info(f"Extracted {len(final_symbols)} symbols from text: {final_symbols}")
            return final_symbols

        except Exception as e:
            logger.error(f"Error extracting symbols from text: {e}")
            raise

    def _extract_direct_symbols(self, text: str) -> List[str]:
        """Extract symbols using direct pattern matching."""
        symbols = []

        # Pattern 1: Symbols preceded by $ (e.g., $AAPL, $TSLA) - High confidence
        pattern1 = r'\$([A-Z]{3,5})'
        matches1 = re.findall(pattern1, text.upper())
        symbols.extend(matches1)

        # Pattern 2: Symbols in parentheses (e.g., Apple (AAPL)) - High confidence
        pattern2 = r'\(([A-Z]{3,5})\)'
        matches2 = re.findall(pattern2, text.upper())
        symbols.extend(matches2)

        # Pattern 3: Symbols after "ticker:" or "symbol:" - High confidence
        pattern3 = r'(?:ticker|symbol):\s*([A-Z]{3,5})'
        matches3 = re.findall(pattern3, text.upper())
        symbols.extend(matches3)

        # Pattern 4: Symbols with dots (e.g., BRK.B, BRK.A) - High confidence
        pattern4 = r'\b[A-Z]{2,4}\.[A-Z]\b'
        matches4 = re.findall(pattern4, text.upper())
        symbols.extend(matches4)

        # Pattern 5: Standard ticker symbols (3-5 uppercase letters) - Lower confidence, more restrictive
        # Only match if they appear to be isolated or in specific contexts
        pattern5 = r'(?:^|\s)([A-Z]{3,5})(?=\s|$|[.,!?])'
        matches5 = re.findall(pattern5, text.upper())
        # Further filter these to avoid common words
        for match in matches5:
            if match not in self.false_positives and len(match) >= 3:
                symbols.append(match)

        return list(set(symbols))  # Remove duplicates

    def _extract_from_company_names(self, text: str) -> List[str]:
        """Extract symbols by matching company names."""
        symbols = []
        text_lower = text.lower()

        # Check for company name matches
        for company_name, symbol in self.company_mappings.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(company_name) + r'\b'
            if re.search(pattern, text_lower):
                symbols.append(symbol)

        return symbols

    def _extract_contextual_symbols(self, text: str) -> List[str]:
        """Extract symbols using contextual clues."""
        symbols = []
        text_upper = text.upper()

        # Look for trading/investment context keywords followed by potential symbols
        # More specific patterns to avoid false positives
        trading_keywords = [
            r'(?:BUY|PURCHASE)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:SELL|SELLING)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:HOLD|HOLDING)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:LONG|GOING\s+LONG)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:SHORT|SHORTING)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:ANALYZE|ANALYSIS\s+OF)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'([A-Z]{3,5})\s+(?:STOCK|SHARES?)(?:\s|$|[.,!?])',
            r'(?:SHARES?\s+OF|POSITION\s+IN)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:TRADING|TRADE)\s+([A-Z]{3,5})(?:\s|$|[.,!?])',
            r'(?:INVESTING\s+IN|INVESTMENT\s+IN)\s+([A-Z]{3,5})(?:\s|$|[.,!?])'
        ]

        for pattern in trading_keywords:
            matches = re.findall(pattern, text_upper)
            symbols.extend(matches)

        # Look for price context (e.g., "AAPL at $150")
        price_pattern = r'([A-Z]{3,5})\s+(?:AT|@|IS\s+AT)\s*\$?\d+(?:\.\d+)?'
        price_matches = re.findall(price_pattern, text_upper)
        symbols.extend(price_matches)

        # Look for percentage context (e.g., "TSLA up 5%")
        percent_pattern = r'([A-Z]{3,5})\s+(?:UP|DOWN|GAINED|LOST|ROSE|FELL)\s+\d+(?:\.\d+)?%'
        percent_matches = re.findall(percent_pattern, text_upper)
        symbols.extend(percent_matches)

        # Look for earnings/financial context
        financial_pattern = r'([A-Z]{3,5})\s+(?:EARNINGS|REVENUE|QUARTERLY|ANNUAL|REPORT)'
        financial_matches = re.findall(financial_pattern, text_upper)
        symbols.extend(financial_matches)

        return list(set(symbols))

    def _validate_and_filter_symbols(self, symbols: List[str]) -> List[str]:
        """Validate and filter extracted symbols."""
        validated = []

        for symbol in symbols:
            if self._is_valid_symbol(symbol):
                validated.append(symbol.upper())

        return list(set(validated))  # Remove duplicates

    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is likely to be a valid stock ticker."""
        if not symbol:
            return False

        symbol = symbol.upper().strip()

        # Check length (most symbols are 1-5 characters)
        if len(symbol) < 1 or len(symbol) > 5:
            return False

        # Check if it's in the false positives list
        if symbol in self.false_positives:
            return False

        # Check for valid characters (letters, dots, hyphens)
        if not re.match(r'^[A-Z]+(?:\.[A-Z])?$', symbol):
            return False

        # Additional validation rules

        # Single letter symbols are rare (except for some like F, T, etc.)
        if len(symbol) == 1:
            valid_single_letters = {'F', 'T', 'C', 'D', 'X', 'V', 'M', 'N', 'S', 'W', 'Y', 'Z'}
            return symbol in valid_single_letters

        # Two letter symbols ending in certain letters are less common
        if len(symbol) == 2:
            # Most 2-letter symbols don't end with these
            uncommon_endings = {'Q', 'X', 'Z'}
            if symbol[-1] in uncommon_endings:
                return False

        # Symbols with repeated characters are uncommon
        if len(set(symbol.replace('.', ''))) == 1:  # All same letter
            return False

        return True

    def _rank_symbols_by_confidence(self, symbols: List[str], original_text: str) -> List[str]:
        """Rank symbols by confidence/likelihood."""
        if not symbols:
            return []

        symbol_scores = {}
        text_upper = original_text.upper()

        for symbol in symbols:
            score = 0.0

            # Base score
            score += 1.0

            # Length-based scoring (3-4 letter symbols are most common)
            if len(symbol) in [3, 4]:
                score += 2.0
            elif len(symbol) in [2, 5]:
                score += 1.0

            # Context-based scoring

            # Check if symbol appears with $ prefix
            if f'${symbol}' in text_upper:
                score += 3.0

            # Check if symbol appears in parentheses
            if f'({symbol})' in text_upper:
                score += 2.5

            # Check if symbol appears with trading keywords
            trading_context_patterns = [
                f'BUY {symbol}', f'SELL {symbol}', f'HOLD {symbol}',
                f'ANALYZE {symbol}', f'STOCK {symbol}', f'TRADING {symbol}'
            ]

            for pattern in trading_context_patterns:
                if pattern in text_upper:
                    score += 2.0
                    break

            # Check if symbol appears with price information
            price_patterns = [
                f'{symbol} AT', f'{symbol} @', f'{symbol} \\$\\d+',
                f'{symbol} UP', f'{symbol} DOWN'
            ]

            for pattern in price_patterns:
                if re.search(pattern, text_upper):
                    score += 1.5
                    break

            # Check if it's a known company mapping
            if symbol in self.company_mappings.values():
                score += 1.0

            # Frequency in text (multiple mentions increase confidence)
            frequency = text_upper.count(symbol)
            if frequency > 1:
                score += min(frequency * 0.5, 2.0)  # Cap at +2.0

            symbol_scores[symbol] = score

        # Sort by score (descending) and return
        ranked_symbols = sorted(symbol_scores.items(), key=lambda x: x[1], reverse=True)

        # Return symbols with score > threshold
        confidence_threshold = 1.0
        final_symbols = [symbol for symbol, score in ranked_symbols if score > confidence_threshold]

        # Limit to top 10 symbols to avoid noise
        return final_symbols[:10]

    def _get_symbol_confidence_details(self, symbol: str, text: str) -> Dict[str, Any]:
        """Get detailed confidence information for a symbol."""
        text_upper = text.upper()

        confidence_factors = {
            "base_score": 1.0,
            "length_bonus": 0.0,
            "context_bonus": 0.0,
            "format_bonus": 0.0,
            "frequency_bonus": 0.0,
            "company_mapping": False
        }

        # Length bonus
        if len(symbol) in [3, 4]:
            confidence_factors["length_bonus"] = 2.0
        elif len(symbol) in [2, 5]:
            confidence_factors["length_bonus"] = 1.0

        # Format bonuses
        if f'${symbol}' in text_upper:
            confidence_factors["format_bonus"] += 3.0
        if f'({symbol})' in text_upper:
            confidence_factors["format_bonus"] += 2.5

        # Context bonus
        trading_keywords = ['BUY', 'SELL', 'HOLD', 'ANALYZE', 'STOCK', 'TRADING']
        for keyword in trading_keywords:
            if f'{keyword} {symbol}' in text_upper:
                confidence_factors["context_bonus"] += 2.0
                break

        # Frequency bonus
        frequency = text_upper.count(symbol)
        if frequency > 1:
            confidence_factors["frequency_bonus"] = min(frequency * 0.5, 2.0)

        # Company mapping
        confidence_factors["company_mapping"] = symbol in self.company_mappings.values()

        total_score = sum([
            confidence_factors["base_score"],
            confidence_factors["length_bonus"],
            confidence_factors["context_bonus"],
            confidence_factors["format_bonus"],
            confidence_factors["frequency_bonus"],
            1.0 if confidence_factors["company_mapping"] else 0.0
        ])

        return {
            "symbol": symbol,
            "confidence_score": total_score,
            "confidence_factors": confidence_factors,
            "frequency_in_text": frequency
        }

    async def get_symbol_details(self, symbols: List[str], text: str) -> List[Dict[str, Any]]:
        """Get detailed information about extracted symbols."""
        details = []

        for symbol in symbols:
            symbol_detail = self._get_symbol_confidence_details(symbol, text)
            details.append(symbol_detail)

        return details

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Input text to extract stock symbols from",
                    "minLength": 1
                }
            },
            "required": ["text"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample text."""
        try:
            # Test with sample text containing various symbol formats
            test_text = "I want to analyze AAPL and buy $TSLA. Also looking at Microsoft (MSFT) and Google stock."

            result = await self.execute(test_text)

            # Should extract at least AAPL, TSLA, MSFT, and GOOGL
            expected_symbols = {"AAPL", "TSLA", "MSFT", "GOOGL"}
            extracted_symbols = set(result)

            # Check if we got at least 3 of the 4 expected symbols
            overlap = len(expected_symbols.intersection(extracted_symbols))
            return overlap >= 3

        except Exception as e:
            logger.error(f"Symbol extractor health check failed: {e}")
            return False


# Additional utility functions for symbol validation

def is_likely_stock_symbol(text: str) -> bool:
    """Quick check if a text string is likely a stock symbol."""
    if not text or len(text) > 5:
        return False

    # Must be all uppercase letters (with optional dot)
    if not re.match(r'^[A-Z]+(?:\.[A-Z])?$', text):
        return False

    # Common false positives
    false_positives = {
        "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
        "WAS", "ONE", "OUR", "HAD", "BY", "WORD", "WHAT", "SOME", "WE"
    }

    return text not in false_positives


def extract_symbols_simple(text: str) -> List[str]:
    """Simple symbol extraction function for quick use."""
    if not text:
        return []

    # Find potential symbols
    pattern = r'\b[A-Z]{2,5}\b'
    matches = re.findall(pattern, text.upper())

    # Filter out common false positives
    false_positives = {
        "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
        "WAS", "ONE", "OUR", "HAD", "BY", "WORD", "WHAT", "SOME", "WE",
        "OUT", "OTHER", "WERE", "WHICH", "THEIR", "TIME", "WILL", "HOW"
    }

    symbols = [match for match in matches if match not in false_positives]

    return list(set(symbols))  # Remove duplicates
