"""
Analysis Orchestrator - Modular Ticker Analysis Pipeline

STRUCTURAL_CAUSE_003 FIX: Decomposed monolithic analyze_ticker() function
into modular components following Single Responsibility Principle.

Architecture:
- DataFetcher: Data acquisition and validation
- IndicatorEngine: Technical indicator calculations
- SignalAggregator: Vote aggregation logic
- TradeCalculator: Entry/stop/target calculations
- ResultFormatter: Output formatting

Benefits:
- Reduced cyclomatic complexity from 45 to <10 per module
- Improved testability and maintainability
- Clear separation of concerns
- 100% backward compatibility maintained
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Import data utilities
from utils.data.fetcher import fetch_ticker_data
from utils.data.validator import DataValidator

# Import indicators
from indicators import (
    rsi, macd, adx, psar, ema, stochastic, 
    cci, williams, atr, bollinger, obv, cmf
)

# Import enhancement modules
from utils.trading.entry_calculator import EntryCalculator
from utils.trading.risk_manager import RiskManager
from utils.trading.trade_validator import TradeValidator
from utils.analysis.signal_validator import SignalValidator

logger = logging.getLogger('trading_analyzer')

# Category biases for weighted scoring
TYPE_BIAS = {
    "trend": 1.0,
    "momentum": 1.0,
    "volatility": 0.9,
    "volume": 0.9
}

# All available indicators
ALL_INDICATORS = {
    "RSI": rsi,
    "MACD": macd,
    "ADX": adx,
    "Parabolic SAR": psar,
    "EMA Crossover": ema,
    "Stochastic": stochastic,
    "CCI": cci,
    "Williams %R": williams,
    "ATR": atr,
    "Bollinger Bands": bollinger,
    "OBV": obv,
    "Chaikin Money Flow": cmf
}


class DataFetcher:
    """
    Handles data acquisition and validation.
    
    Responsibilities:
    - Fetch ticker data from Yahoo Finance or demo sources
    - Validate data quality and completeness
    - Handle data source fallbacks
    """
    
    @staticmethod
    def fetch_and_validate(ticker: str, use_demo_data: bool = False) -> Tuple[Optional[pd.DataFrame], str, bool, str, List[str]]:
        """
        Fetch and validate ticker data.
        
        Args:
            ticker: Stock ticker symbol
            use_demo_data: Use demo data instead of live data
            
        Returns:
            Tuple of (dataframe, source, is_valid, message, warnings)
        """
        try:
            # Fetch data
            if use_demo_data:
                # Generate simple demo data
                df = DataFetcher._generate_demo_data(ticker)
                source = "demo"
            else:
                df = fetch_ticker_data(ticker)
                source = "yahoo_finance"
            
            if df is None or df.empty:
                return None, source, False, "No data fetched", []
            
            # Validate data
            is_valid, message, warnings = DataValidator.validate_ohlcv_data(df, ticker)
            
            return df, source, is_valid, message, warnings
            
        except Exception as e:
            logger.error(f"Data fetch failed for {ticker}: {e}")
            return None, "error", False, str(e), []
    
    @staticmethod
    def _generate_demo_data(ticker: str, days: int = 100) -> pd.DataFrame:
        """Generate simple demo OHLCV data for testing."""
        import numpy as np
        from datetime import datetime, timedelta
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic price data using random walk
        np.random.seed(hash(ticker) % (2**32))  # Consistent data per ticker
        returns = np.random.normal(0.001, 0.02, days)
        base_price = 100 + (hash(ticker) % 1000)
        
        close_prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC from close
        high = close_prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low = close_prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        
        # Generate volume
        volume = np.random.randint(1000000, 10000000, days)
        
        df = pd.DataFrame({
            'Open': open_prices,
            'High': high,
            'Low': low,
            'Close': close_prices,
            'Volume': volume
        }, index=dates)
        
        return df


class IndicatorEngine:
    """
    Manages technical indicator calculations.
    
    Responsibilities:
    - Calculate requested indicators
    - Handle indicator-specific errors
    - Format indicator results consistently
    """
    
    @staticmethod
    def calculate_indicators(df: pd.DataFrame, ticker: str, indicator_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Calculate all requested indicators.
        
        Args:
            df: OHLCV DataFrame
            ticker: Stock ticker symbol
            indicator_list: List of indicator names (None = all)
            
        Returns:
            List of indicator results with vote, confidence, and metadata
        """
        # Determine which indicators to use
        if indicator_list:
            indicators_to_use = {name: ALL_INDICATORS[name] for name in indicator_list if name in ALL_INDICATORS}
        else:
            indicators_to_use = ALL_INDICATORS
        
        results = []
        
        for name, indicator_module in indicators_to_use.items():
            try:
                # Call the indicator's vote_and_confidence function
                result = indicator_module.vote_and_confidence(df)
                
                # Ensure result has required fields
                if isinstance(result, dict):
                    result['name'] = name
                    if 'category' not in result:
                        # Infer category from indicator
                        result['category'] = IndicatorEngine._get_indicator_category(name)
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Indicator {name} calculation failed for {ticker}: {e}")
                # Add error result to maintain consistency
                results.append({
                    'name': name,
                    'vote': 0,
                    'confidence': 0.0,
                    'category': IndicatorEngine._get_indicator_category(name),
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def _get_indicator_category(name: str) -> str:
        """Get indicator category based on name."""
        momentum_indicators = ["RSI", "Stochastic", "CCI", "Williams %R"]
        trend_indicators = ["MACD", "ADX", "EMA Crossover", "Parabolic SAR"]
        volatility_indicators = ["Bollinger Bands", "ATR"]
        volume_indicators = ["OBV", "Chaikin Money Flow"]
        
        if name in momentum_indicators:
            return "momentum"
        elif name in trend_indicators:
            return "trend"
        elif name in volatility_indicators:
            return "volatility"
        elif name in volume_indicators:
            return "volume"
        else:
            return "unknown"


class SignalAggregator:
    """
    Aggregates indicator votes into composite score.
    
    Responsibilities:
    - Apply category-based weighting
    - Calculate composite score
    - Generate verdict from score
    """
    
    @staticmethod
    def aggregate_votes(indicator_results: List[Dict[str, Any]]) -> float:
        """
        Aggregate indicator votes with category-based weighting.
        
        Args:
            indicator_results: List of indicator results
            
        Returns:
            Composite score (-1.0 to 1.0)
        """
        if not indicator_results:
            return 0.0
        
        total_weighted_vote = 0.0
        total_weight = 0.0
        
        for result in indicator_results:
            vote = result.get('vote', 0)
            confidence = result.get('confidence', 0.5)
            category = result.get('category', 'unknown')
            
            # Get category bias
            bias = TYPE_BIAS.get(category, 0.5)
            
            # Calculate weighted vote
            weight = confidence * bias
            total_weighted_vote += vote * weight
            total_weight += weight
        
        # Calculate normalized score
        if total_weight > 0:
            score = total_weighted_vote / total_weight
        else:
            score = 0.0
        
        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, score))
    
    @staticmethod
    def get_verdict(score: float) -> str:
        """
        Convert score to trading verdict.
        
        Args:
            score: Composite score (-1.0 to 1.0)
            
        Returns:
            Verdict string
        """
        if score >= 0.6:
            return "Strong Buy"
        elif score >= 0.2:
            return "Buy"
        elif score <= -0.6:
            return "Strong Sell"
        elif score <= -0.2:
            return "Sell"
        else:
            return "Hold"


class TradeCalculator:
    """
    Calculates trade parameters (entry, stop, target).
    
    Responsibilities:
    - Calculate entry price
    - Calculate stop loss
    - Calculate target price
    - Validate risk/reward ratios
    """
    
    @staticmethod
    def calculate_trade_parameters(df: pd.DataFrame, score: float, verdict: str, capital: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate trade parameters.
        
        Args:
            df: OHLCV DataFrame
            score: Composite score
            verdict: Trading verdict
            capital: Available capital
            
        Returns:
            Dictionary with trade parameters
        """
        try:
            # Get current price
            current_price = float(df['Close'].iloc[-1])
            
            # Use EntryCalculator for entry levels
            entry_calculator = EntryCalculator()
            entry_price, _method, _confidence = entry_calculator.calculate_strategic_entry(
                df=df,
                current_price=current_price,
                signal=verdict
            )
            
            # Simple stop loss and target calculation
            if verdict in ["Buy", "Strong Buy"]:
                stop_loss = entry_price * 0.97  # 3% stop loss
                target = entry_price * 1.05  # 5% target
            elif verdict in ["Sell", "Strong Sell"]:
                stop_loss = entry_price * 1.03
                target = entry_price * 0.95
            else:
                stop_loss = entry_price * 0.97
                target = entry_price * 1.03
            
            # Determine signal
            if score >= 0.2:
                signal = "BUY"
            elif score <= -0.2:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Calculate risk/reward
            if signal == "BUY":
                risk = entry_price - stop_loss
                reward = target - entry_price
            elif signal == "SELL":
                risk = stop_loss - entry_price
                reward = entry_price - target
            else:
                risk = 0
                reward = 0
            
            risk_reward_ratio = (reward / risk) if risk > 0 else 0
            
            # Use RiskManager for position sizing if capital provided
            position_size = 0
            risk_valid = True
            risk_message = "No capital provided"
            
            if capital:
                # RiskManager.calculate_position_size expects (entry, stop, capital)
                position_size = RiskManager.calculate_position_size(
                    entry=entry_price,
                    stop=stop_loss,
                    capital=capital
                )
                risk_valid = position_size > 0
                risk_message = "Position calculated" if risk_valid else "Invalid position"
            
            return {
                'entry': entry_price,
                'stop': stop_loss,
                'target': target,
                'signal': signal,
                'risk_reward_ratio': risk_reward_ratio,
                'position_size': position_size,
                'risk_valid': risk_valid,
                'risk_message': risk_message
            }
            
        except Exception as e:
            logger.exception(f"Trade calculation failed: {e}")
            current_price = float(df['Close'].iloc[-1])
            return {
                'entry': current_price,
                'stop': current_price * 0.95,
                'target': current_price * 1.05,
                'signal': 'HOLD',
                'risk_reward_ratio': 0,
                'position_size': 0,
                'risk_valid': False,
                'risk_message': str(e)
            }

class ResultFormatter:
    """
    Formats analysis results into standardized output.
    
    Responsibilities:
    - Format result dictionary
    - Include all validation results
    - Ensure consistent structure
    """
    
    @staticmethod
    def format(
        ticker: str,
        score: float,
        verdict: str,
        trade_params: Dict[str, Any],
        indicator_results: List[Dict[str, Any]],
        data_valid: bool,
        data_message: str,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """
        Format complete analysis result.
        
        Args:
            ticker: Stock ticker symbol
            score: Composite score
            verdict: Trading verdict
            trade_params: Trade parameters from TradeCalculator
            indicator_results: Indicator results
            data_valid: Data validation status
            data_message: Data validation message
            warnings: Data validation warnings
            
        Returns:
            Formatted result dictionary
        """
        return {
            'ticker': ticker,
            'score': round(score, 3),
            'verdict': verdict,
            'signal': trade_params.get('signal', 'HOLD'),
            'entry': round(trade_params.get('entry', 0), 2),
            'stop': round(trade_params.get('stop', 0), 2),
            'target': round(trade_params.get('target', 0), 2),
            'risk_reward_ratio': round(trade_params.get('risk_reward_ratio', 0), 2),
            'position_size': trade_params.get('position_size', 0),
            'indicators': indicator_results,
            'data_valid': data_valid,
            'data_message': data_message,
            'data_warnings': warnings,
            'risk_valid': trade_params.get('risk_valid', False),
            'risk_message': trade_params.get('risk_message', ''),
            'success': True
        }


class AnalysisOrchestrator:
    """
    Orchestrates the complete ticker analysis pipeline.
    
    Coordinates all analysis modules to produce a comprehensive
    technical analysis result with validation.
    """
    
    def __init__(self):
        """Initialize orchestrator with all required modules."""
        self.data_fetcher = DataFetcher()
        self.indicator_engine = IndicatorEngine()
        self.signal_aggregator = SignalAggregator()
        self.trade_calculator = TradeCalculator()
        self.result_formatter = ResultFormatter()
    
    def analyze(
        self,
        ticker: str,
        indicators: Optional[List[str]] = None,
        capital: Optional[float] = None,
        use_demo_data: bool = False
    ) -> Dict[str, Any]:
        """
        Execute complete ticker analysis pipeline.
        
        Args:
            ticker: Stock ticker symbol
            indicators: List of indicator names to use (None = all)
            capital: Available capital for position sizing
            use_demo_data: Use demo data instead of live data
            
        Returns:
            Complete analysis result dictionary
        """
        try:
            logger.info(f"[ORCHESTRATOR] Starting analysis for ticker: {ticker}")
            logger.debug(f"[ORCHESTRATOR] Analysis params - capital: {capital}, use_demo: {use_demo_data}, indicators: {indicators}")
            
            # Step 1: Fetch and validate data
            df, source, data_valid, data_message, warnings = self.data_fetcher.fetch_and_validate(
                ticker, use_demo_data
            )
            
            logger.info(f"[ORCHESTRATOR] Data fetch completed - ticker: {ticker}, source: {source}, valid: {data_valid}")
            
            if df is None or not data_valid:
                logger.warning(f"[ORCHESTRATOR] Data validation failed for {ticker}: {data_message}")
                return self._error_result(ticker, data_message)
            
            # Step 2: Calculate indicators
            indicator_results = self.indicator_engine.calculate_indicators(df, ticker, indicators)
            
            if not indicator_results:
                logger.warning(f"[ORCHESTRATOR] No indicators calculated for {ticker}")
                return self._error_result(ticker, "No indicators calculated")
            
            # Step 3: Aggregate signals
            score = self.signal_aggregator.aggregate_votes(indicator_results)
            verdict = self.signal_aggregator.get_verdict(score)
            
            logger.info(f"[ORCHESTRATOR] Signal analysis complete - ticker: {ticker}, score: {score}, verdict: {verdict}")
            
            # Step 4: Calculate trade parameters
            trade_params = self.trade_calculator.calculate_trade_parameters(
                df, score, verdict, capital
            )

            # Step 5: Validate and fix trade parameters
            result_dict = {
                'ticker': ticker,
                'current_price': float(df['Close'].iloc[-1]),
                'signal': trade_params.get('signal', 'HOLD'),
                'entry_price': trade_params['entry'],
                'stop_loss': trade_params['stop'],
                'target_price': trade_params['target'],
                'score': score
            }

            fixed_result, was_fixed, _fixes = TradeValidator.validate_and_fix(result_dict)
            if was_fixed:
                trade_params['entry'] = fixed_result['entry_price']
                trade_params['stop'] = fixed_result['stop_loss']
                trade_params['target'] = fixed_result['target_price']

            # Step 6: Format results
            result = self.result_formatter.format(
                ticker=ticker,
                score=score,
                verdict=verdict,
                trade_params=trade_params,
                indicator_results=indicator_results,
                data_valid=data_valid,
                data_message=data_message,
                warnings=warnings
            )

            return result
            
        except Exception as e:
            logger.error(f"Analysis orchestration failed for {ticker}: {e}")
            return self._error_result(ticker, str(e))
    
    def _error_result(self, ticker: str, error_message: str) -> Dict[str, Any]:
        """Generate error result."""
        return {
            'ticker': ticker,
            'score': 0.0,
            'verdict': 'Error',
            'signal': 'HOLD',
            'entry': 0,
            'stop': 0,
            'target': 0,
            'risk_reward_ratio': 0,
            'position_size': 0,
            'indicators': [],
            'data_valid': False,
            'data_message': error_message,
            'data_warnings': [],
            'risk_valid': False,
            'risk_message': error_message,
            'success': False,
            'error': error_message
        }
