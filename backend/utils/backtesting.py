"""
Backtesting Engine for Strategy Analysis

Analyzes historical OHLCV data following TheTool architecture patterns:
- Uses DataFetcher for OHLCV data (respects demo/live data modes)
- Uses IndicatorEngine for calculations (respects modular indicators)
- Integrates with Strategy validation methods (1-5)
- Thread-safe with get_db_session() for background job compatibility
- Uses _convert_query_params() for PostgreSQL/SQLite database abstraction
- Centralized logging via utils.logger.get_logger()

Architecture Pattern:
- Single Responsibility: Only handles trade simulation and metrics
- Modular: Uses existing DataFetcher and IndicatorEngine, doesn't duplicate
- Database agnostic: No direct SQL, uses db layer abstractions
- Thread-safe: Suitable for background job processing
- Multi-Strategy: Supports all 5 strategies with strategy-specific parameters
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

from utils.analysis_orchestrator import DataFetcher
from strategies.strategy_1 import Strategy1
from strategies.strategy_2 import Strategy2
from strategies.strategy_3 import Strategy3
from strategies.strategy_4 import Strategy4
from strategies.strategy_5 import Strategy5

logger = logging.getLogger('trading_analyzer')


# =============================================================================
# STRATEGY CONFIGURATIONS
# =============================================================================
# Each strategy has its own parameters for backtesting
# These are derived from the risk_profile() and characteristics of each strategy

STRATEGY_CONFIGS = {
    1: {
        # Strategy 1: Balanced Analysis - Equal weight to all indicators
        'name': 'Balanced Analysis',
        'description': 'Equal weight to all 12 indicators - good for general market scanning',
        'target_pct': 4.0,           # Standard 4% target
        'stop_loss_pct': 2.0,        # Standard 2% stop (from risk_profile)
        'max_stop_loss_pct': 3.0,    # Maximum 3% stop
        'max_bars': 20,              # 20 bars (~4 weeks) - longer holding for balanced
        'rsi_min': 30,               # Standard RSI oversold level
        'rsi_max': 70,               # Standard RSI overbought level
        'adx_threshold': 20,         # Standard ADX threshold
        'atr_multiplier': 1.5,       # Standard ATR multiplier
        'use_trend_filter': True,    # Use SMA 50 trend filter
        'use_loss_cooldown': True,   # Wait after losses
        'cooldown_bars': 2,          # 2 bar cooldown (shorter for balanced)
        'min_conditions': 2,         # Need 2 of 3 conditions
        'use_strategy_validation': False,  # No Strategy 5-specific validation
    },
    2: {
        # Strategy 2: Trend Following - Heavy on MACD, ADX, EMA, PSAR
        'name': 'Trend Following',
        'description': 'Emphasizes trend indicators - best for trending markets',
        'target_pct': 6.0,           # Higher target for trends (let winners run)
        'stop_loss_pct': 2.5,        # Wider stop to avoid whipsaws
        'max_stop_loss_pct': 4.0,    # Maximum 4% stop
        'max_bars': 25,              # 25 bars (~5 weeks) - longer for trend capture
        'rsi_min': 40,               # Higher minimum (need momentum in direction)
        'rsi_max': 80,               # Higher max (trends can stay overbought)
        'adx_threshold': 25,         # Higher ADX requirement for trend confirmation
        'atr_multiplier': 2.0,       # Wider ATR multiplier for trends
        'use_trend_filter': True,    # Essential for trend following
        'use_loss_cooldown': True,   # Wait after losses
        'cooldown_bars': 3,          # 3 bar cooldown
        'min_conditions': 2,         # Need 2 of 3 conditions
        'use_strategy_validation': False,  # Uses trend-specific validation
    },
    3: {
        # Strategy 3: Mean Reversion - Heavy on RSI, Bollinger, Stochastic
        'name': 'Mean Reversion',
        'description': 'Emphasizes oscillators - best for range-bound markets',
        'target_pct': 2.5,           # Smaller target (quick profits in ranges)
        'stop_loss_pct': 1.5,        # Tighter stop for range trading
        'max_stop_loss_pct': 2.5,    # Maximum 2.5% stop
        'max_bars': 10,              # 10 bars (~2 weeks) - quick turnaround
        'rsi_min': 20,               # Lower RSI threshold (oversold is entry signal)
        'rsi_max': 40,               # Lower max (buy when oversold, not in middle)
        'adx_threshold': 15,         # LOWER ADX (want range-bound, not trending)
        'adx_max': 25,               # Maximum ADX (avoid trends)
        'atr_multiplier': 1.0,       # Tighter ATR multiplier
        'use_trend_filter': False,   # Don't use trend filter (counter-trend strategy)
        'use_loss_cooldown': True,   # Wait after losses
        'cooldown_bars': 2,          # 2 bar cooldown (faster re-entry)
        'min_conditions': 1,         # Need only 1 condition (oversold signal)
        'use_strategy_validation': False,
    },
    4: {
        # Strategy 4: Momentum Breakout - Heavy on OBV, CMF, RSI, ATR
        'name': 'Momentum Breakout',
        'description': 'Volume-confirmed momentum - best for breakouts',
        'target_pct': 5.0,           # Higher target for breakouts
        'stop_loss_pct': 3.0,        # Wider stop for volatile breakouts
        'max_stop_loss_pct': 4.0,    # Maximum 4% stop
        'max_bars': 12,              # 12 bars (~2.5 weeks) - breakouts resolve fast
        'rsi_min': 50,               # Higher RSI minimum (need strength)
        'rsi_max': 85,               # High max (breakouts can be extended)
        'adx_threshold': 20,         # Lower threshold to catch early breakouts
        'atr_multiplier': 1.8,       # Higher ATR multiplier for volatility
        'use_trend_filter': True,    # Need directional confirmation
        'use_loss_cooldown': True,   # Wait after losses
        'cooldown_bars': 2,          # 2 bar cooldown (re-enter fast on breakouts)
        'min_conditions': 2,         # Need 2 of 3 conditions
        'use_strategy_validation': False,
        'require_volume_surge': True,  # CRITICAL: Require volume confirmation
        'min_volume_ratio': 1.2,       # Need 1.2x average volume (lowered from 1.5 for more signals)
    },
    5: {
        # Strategy 5: Weekly 4% Target (Optimized Dec 2025)
        'name': 'Weekly 4% Target',
        'description': 'Optimized swing trading - 4% target, smart stop, 15-bar holding',
        'target_pct': 4.0,           # 4% target (optimized from 5%)
        'stop_loss_pct': 3.0,        # Base stop: 3%
        'max_stop_loss_pct': 4.0,    # Maximum stop: 4% (cap)
        'max_bars': 15,              # 15 bars (~3 weeks)
        'rsi_min': 50,               # Raised from 30 - stronger momentum required
        'rsi_max': 75,               # Avoid overbought
        'adx_threshold': 20,         # ADX below this = choppy market
        'atr_multiplier': 1.5,       # ATR × 1.5 for dynamic stop
        'use_trend_filter': True,    # SMA 50 trend filter
        'use_loss_cooldown': True,   # Wait after losses
        'cooldown_bars': 3,          # 3 bar cooldown
        'min_conditions': 2,         # Need 2 of 3 conditions
        'use_strategy_validation': True,  # Use Strategy 5 momentum validation
    }
}


def get_strategy_class(strategy_id: int):
    """Get the strategy class instance for a given strategy ID."""
    strategy_classes = {
        1: Strategy1,
        2: Strategy2,
        3: Strategy3,
        4: Strategy4,
        5: Strategy5,
    }
    if strategy_id not in strategy_classes:
        raise ValueError(f"Invalid strategy_id: {strategy_id}. Must be 1-5.")
    return strategy_classes[strategy_id]()


class BacktestEngine:
    """
    Backtesting engine following TheTool architecture patterns.
    
    Simulates historical trades based on strategy-specific signals.
    Uses existing DataFetcher and IndicatorEngine to avoid code duplication.
    Supports all 5 strategies with appropriate validation methods.
    """
    
    def __init__(self, strategy_id: int = 5):
        """
        Initialize backtesting engine with strategy-specific configuration.
        
        Args:
            strategy_id: Strategy to backtest (1-5, default 5 = enhanced swing trading)
        """
        if strategy_id not in STRATEGY_CONFIGS:
            raise ValueError(f"Invalid strategy_id: {strategy_id}. Must be 1-5.")
        
        self.strategy_id = strategy_id
        self.config = STRATEGY_CONFIGS[strategy_id]
        self.data_fetcher = DataFetcher()
        self.strategy = get_strategy_class(strategy_id)
        
        # Load strategy-specific parameters from config
        self.TARGET_PCT = self.config['target_pct']
        self.MAX_BARS = self.config['max_bars']
        self.STOP_LOSS_PCT = self.config['stop_loss_pct']
        self.MAX_STOP_LOSS_PCT = self.config['max_stop_loss_pct']
        self.ATR_MULTIPLIER = self.config['atr_multiplier']
        self.USE_WIDER_STOP = True
        
        # RSI parameters
        self.RSI_MIN = self.config['rsi_min']
        self.RSI_MAX = self.config['rsi_max']
        
        # ADX parameters
        self.ADX_CHOPPY_THRESHOLD = self.config['adx_threshold']
        self.ADX_MAX = self.config.get('adx_max')  # Only for mean reversion
        self.USE_ADX_FILTER = True
        
        # Filters
        self.USE_TREND_FILTER = self.config['use_trend_filter']
        self.USE_LOSS_COOLDOWN = self.config['use_loss_cooldown']
        self.COOLDOWN_BARS = self.config['cooldown_bars']
        self.MIN_CONDITIONS = self.config['min_conditions']
        self.USE_STRATEGY5_VALIDATION = self.config['use_strategy_validation']
        
        # Volume requirements (for Strategy 4 breakout)
        self.REQUIRE_VOLUME_SURGE = self.config.get('require_volume_surge', False)
        self.MIN_VOLUME_RATIO = self.config.get('min_volume_ratio', 1.0)
        
        # Incomplete trade handling
        self.MIN_BARS_FOR_VALID_TRADE = 5
        self.SKIP_INCOMPLETE_TRADES = True
        
        # Volume sweet spot (disabled by default - use config to enable)
        self.USE_VOLUME_SWEET_SPOT = False
        self.MAX_VOLUME_RATIO = 100.0
        
        logger.info(f"[Backtest] Initialized with Strategy {strategy_id}: {self.config['name']}")
    
    def backtest_ticker(self, ticker: str, days: int = 90) -> Dict[str, Any]:
        """
        Run backtest for a single ticker.
        
        Uses TheTool patterns:
        - DataFetcher for data retrieval (respects demo/live modes)
        - IndicatorEngine for calculations (respects modular indicators)
        - Strategy-specific parameters and validation
        
        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')
            days: Historical days to analyze (30-365, default 90)
        
        Returns:
            {
                'ticker': 'RELIANCE.NS',
                'strategy_id': 5,
                'strategy_name': 'Weekly 4% Target',
                'backtest_period': '2025-11-01 to 2025-01-28',
                'total_signals': 45,
                'winning_trades': 32,
                'losing_trades': 13,
                'win_rate': 71.1,
                'profit_factor': 2.45,
                'total_profit_pct': 18.5,
                'avg_win': 4.2,
                'avg_loss': -3.1,
                'max_drawdown': -8.5,
                'consecutive_wins': 8,
                'trades_per_day': 0.5,
                'trades': [...]
            }
        """
        try:
            logger.info(f"[Backtest] Starting for {ticker} ({days} days, strategy_id={self.strategy_id})")
            
            # Validate inputs
            if days < 30 or days > 365:
                return {'error': 'days must be between 30 and 365', 'ticker': ticker}
            
            # Fetch historical data using TheTool's DataFetcher
            # Period should be longer than requested days to have data for indicators
            fetch_days = days + 50  # Extra data for indicator calculation
            
            df, source, is_valid, message, warnings = self.data_fetcher.fetch_and_validate(
                ticker=ticker,
                use_demo_data=False,  # Use real data
                period=f'{fetch_days}d'
            )
            
            if not is_valid or df is None or df.empty:
                logger.warning(f"[Backtest] No valid data for {ticker}: {message}")
                return {
                    'error': f'No valid data available: {message}',
                    'ticker': ticker,
                    'strategy_id': self.strategy_id,
                    'strategy_name': self.config['name']
                }
            
            logger.info(f"[Backtest] Fetched {len(df)} candles for {ticker} (source: {source})")
            
            # Trim to requested days
            if len(df) > days:
                df = df.iloc[-days:]
            
            # Normalize column names (DataFetcher returns capitalized names)
            df.columns = df.columns.str.lower()
            
            # Calculate indicators for entire dataframe
            df = self._calculate_indicators(df, ticker)
            
            # Generate buy signals based on strategy logic
            signals = self._generate_entry_signals(df)
            
            if not signals:
                logger.info(f"[Backtest] No signals generated for {ticker}")
                return {
                    'ticker': ticker,
                    'strategy_id': self.strategy_id,
                    'strategy_name': self.config['name'],
                    'strategy_description': self.config['description'],
                    'backtest_period': f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}",
                    'total_signals': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'message': 'No buy signals generated in this period'
                }
            
            logger.info(f"[Backtest] Generated {len(signals)} entry signals for {ticker}")
            
            # Simulate trades from each signal
            trades, incomplete_trades = self._simulate_trades(df, signals)
            
            # Calculate comprehensive metrics
            metrics = self._calculate_metrics(trades)
            metrics['ticker'] = ticker
            metrics['strategy_id'] = self.strategy_id
            metrics['strategy_name'] = self.config['name']
            metrics['strategy_description'] = self.config['description']
            metrics['strategy_params'] = {
                'target_pct': self.TARGET_PCT,
                'stop_loss_pct': self.STOP_LOSS_PCT,
                'max_bars': self.MAX_BARS,
                'rsi_range': f"{self.RSI_MIN}-{self.RSI_MAX}",
                'adx_threshold': self.ADX_CHOPPY_THRESHOLD,
                'use_trend_filter': self.USE_TREND_FILTER,
                'cooldown_bars': self.COOLDOWN_BARS,
            }
            metrics['backtest_period'] = f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
            metrics['trades'] = trades
            metrics['days_analyzed'] = days
            metrics['data_source'] = source
            
            # Add excluded trades info (Dec 2025)
            metrics['excluded_trades'] = len(incomplete_trades)
            metrics['excluded_trades_detail'] = incomplete_trades
            if incomplete_trades:
                metrics['exclusion_note'] = f"{len(incomplete_trades)} signal(s) excluded due to insufficient data at end of period"
            
            logger.info(f"[Backtest] Completed for {ticker}: {metrics['win_rate']}% win rate, {metrics['profit_factor']}x profit factor")
            
            return metrics
            
        except Exception as e:
            logger.error(f"[Backtest] Failed for {ticker}: {str(e)}", exc_info=True)
            return {'error': f'Backtest failed: {str(e)}', 'ticker': ticker}
    
    def backtest_multiple(self, tickers: List[str], days: int = 90) -> Dict[str, Dict]:
        """
        Run backtest on multiple tickers.
        
        Args:
            tickers: List of stock tickers
            days: Historical days to analyze
        
        Returns:
            Dict mapping tickers to their backtest results
        """
        results = {}
        
        for ticker in tickers:
            results[ticker] = self.backtest_ticker(ticker, days=days)
        
        return results
    
    def _calculate_indicators(self, df: pd.DataFrame, ticker: str = 'UNKNOWN') -> pd.DataFrame:
        """
        Calculate technical indicators needed for backtesting.
        
        For backtesting, we need rolling indicators (RSI, SMA, ATR) calculated
        for every row, not just the current bar like IndicatorEngine does.
        
        Note: We calculate these manually instead of using IndicatorEngine because
        IndicatorEngine is designed for real-time analysis (calculates for current bar),
        not historical backtesting (needs all rows).
        """
        try:
            df = df.copy()
            
            # 1. SMA (20-period)
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            
            # 1b. SMA (50-period) for trend filter - Synced with Strategy 5
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            
            # 2. RSI (14-period)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # 3. ATR (14-period)
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
            
            # 4. Volume moving average (for volume ratio)
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            # 5. ADX (14-period) for market regime detection
            # True Range
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # +DM and -DM
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            dm_plus = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
            dm_minus = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
            
            # Wilder smoothing (alpha = 1/14)
            # FIX: Use .values to ensure consistent indexing - tr has datetime index,
            # dm_plus/dm_minus are numpy arrays. Without .values, index mismatch causes NaN.
            alpha = 1.0 / 14
            tr_smooth = pd.Series(tr.values).ewm(alpha=alpha, adjust=False).mean()
            dm_plus_smooth = pd.Series(dm_plus).ewm(alpha=alpha, adjust=False).mean()
            dm_minus_smooth = pd.Series(dm_minus).ewm(alpha=alpha, adjust=False).mean()
            
            # DI+ and DI-
            di_plus = 100 * (dm_plus_smooth / tr_smooth)
            di_minus = 100 * (dm_minus_smooth / tr_smooth)
            
            # DX and ADX
            dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
            df['ADX'] = pd.Series(dx.values).ewm(alpha=alpha, adjust=False).mean().values
            df['DI_plus'] = di_plus.values
            df['DI_minus'] = di_minus.values
            
            # 6. MACD for Strategy 5 validation
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
            
            # 7. Stochastic (14-period) for Strategy 5 validation
            low14 = df['low'].rolling(window=14).min()
            high14 = df['high'].rolling(window=14).max()
            df['Stochastic'] = 100 * (df['close'] - low14) / (high14 - low14 + 1e-10)
            
            # 8. CCI (20-period) for Strategy 5 validation
            tp = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = tp.rolling(window=20).mean()
            mean_dev = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            df['CCI'] = (tp - sma_tp) / (0.015 * mean_dev + 1e-10)
            
            # 9. Williams %R (14-period) for Strategy 5 validation
            df['Williams'] = -100 * (high14 - df['close']) / (high14 - low14 + 1e-10)
            
            logger.debug(f"[Backtest] Calculated indicators for {len(df)} bars (ticker: {ticker})")
            return df
            
        except Exception as e:
            logger.warning(f"[Backtest] Indicator calculation error: {str(e)} - continuing without some indicators")
            return df
    
    def _generate_entry_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate buy signals based on strategy-specific logic.
        
        Each strategy has different entry criteria:
        - Strategy 1: Balanced - standard conditions (2/3 met)
        - Strategy 2: Trend Following - requires ADX > 25, focus on trend
        - Strategy 3: Mean Reversion - low RSI (oversold), low ADX (range-bound)
        - Strategy 4: Breakout - requires volume surge + momentum
        - Strategy 5: Enhanced - uses Strategy 5 validation methods
        
        Common filters applied:
        1. RSI within strategy-specific range
        2. ADX filter (varies by strategy)
        3. Trend filter (if enabled)
        4. Cooldown after loss
        5. Strategy-specific validation (if enabled)
        """
        signals = []
        
        try:
            # Ensure all indicators are calculated
            required_cols = ['SMA_20', 'SMA_50', 'RSI', 'ATR', 'ADX', 'MACD', 'MACD_signal', 'Stochastic', 'CCI', 'Williams']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.warning(f"[Backtest] Missing columns for validation: {missing_cols}")
            
            skipped_adx = 0
            skipped_momentum = 0
            skipped_trend = 0
            skipped_cooldown = 0
            skipped_volume = 0
            last_loss_bar = None  # Track when last loss occurred for cooldown
            
            # Start at bar 50 to ensure SMA_50 is valid
            start_bar = max(50, 20)
            
            for i in range(start_bar, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # Extract data
                close = row['close']
                prev_close = prev_row['close']
                sma_20 = row.get('SMA_20', close)
                sma_50 = row.get('SMA_50', close)
                rsi = row.get('RSI', 50)
                adx = row.get('ADX', 25)  # Default to 25 if missing
                
                # Volume analysis
                avg_volume = df['volume'].iloc[max(0, i-20):i].mean()
                current_volume = row['volume']
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                
                # Skip if RSI is invalid based on strategy
                if pd.isna(rsi) or rsi > self.RSI_MAX or rsi < self.RSI_MIN:
                    continue
                
                # ADX FILTER - Strategy-specific handling
                if self.USE_ADX_FILTER:
                    # Strategy 3 (Mean Reversion): Want LOW ADX (range-bound market)
                    if self.ADX_MAX is not None:
                        # Mean reversion: skip if ADX too HIGH (trending)
                        if adx > self.ADX_MAX:
                            skipped_adx += 1
                            continue
                    else:
                        # Other strategies: skip if ADX too LOW (choppy)
                        if adx < self.ADX_CHOPPY_THRESHOLD:
                            skipped_adx += 1
                            continue
                
                # TREND FILTER - Skip if in downtrend (unless mean reversion or breakout)
                if self.USE_TREND_FILTER:
                    # Strategy 4 (Breakout): Only require price above SMA 20, not SMA 50
                    # Breakouts can happen at the start of new trends before SMA 50 turns
                    if self.strategy_id == 4:
                        if pd.notna(sma_20) and close < sma_20:
                            skipped_trend += 1
                            continue
                    else:
                        # Other strategies: require both price > SMA 50 and SMA 20 > SMA 50
                        if pd.notna(sma_50) and (close < sma_50 or sma_20 < sma_50):
                            skipped_trend += 1
                            continue
                
                # COOLDOWN FILTER - Wait X bars after a loss
                if self.USE_LOSS_COOLDOWN and last_loss_bar is not None:
                    bars_since_loss = i - last_loss_bar
                    if bars_since_loss < self.COOLDOWN_BARS:
                        skipped_cooldown += 1
                        continue
                
                # VOLUME SURGE FILTER - Required for Strategy 4 (Breakout)
                if self.REQUIRE_VOLUME_SURGE:
                    if volume_ratio < self.MIN_VOLUME_RATIO:
                        skipped_volume += 1
                        continue
                
                # Volume Sweet Spot Filter (disabled by default)
                if self.USE_VOLUME_SWEET_SPOT:
                    if volume_ratio < self.MIN_VOLUME_RATIO or volume_ratio > self.MAX_VOLUME_RATIO:
                        continue
                
                # Build conditions based on strategy type
                if self.strategy_id == 3:
                    # Mean Reversion: Buy when oversold
                    conditions = {
                        'oversold_rsi': rsi < 40,  # RSI below 40 is oversold signal
                        'price_below_sma': close < sma_20,  # Price stretched below mean
                        'low_adx': adx < 25,  # Range-bound market
                    }
                elif self.strategy_id == 4:
                    # Breakout: Need momentum + volume confirmation
                    conditions = {
                        'price_above_sma': close > sma_20,
                        'strong_rsi': rsi > 50,  # Need momentum
                        'volume_surge': volume_ratio >= 1.2,  # Lowered from 1.5 for more signals
                    }
                else:
                    # Standard conditions for Strategy 1, 2, 5
                    conditions = {
                        'price_above_sma': close > sma_20,
                        'healthy_rsi': self.RSI_MIN <= rsi <= self.RSI_MAX,
                        'price_rising': close > prev_close,
                    }
                
                # Count conditions met
                conditions_met = sum(conditions.values())
                
                # Need at least MIN_CONDITIONS to proceed
                if conditions_met < self.MIN_CONDITIONS:
                    continue
                
                # Strategy 5 Momentum Validation (only for strategy 5)
                if self.USE_STRATEGY5_VALIDATION and self.strategy_id == 5:
                    # Build indicator dict for Strategy 5 validation
                    indicator_values = {
                        'RSI': rsi,
                        'MACD': row.get('MACD'),
                        'MACD_signal': row.get('MACD_signal'),
                        'MACD_histogram': row.get('MACD_histogram'),
                        'Stochastic': row.get('Stochastic'),
                        'CCI': row.get('CCI'),
                        'Williams %R': row.get('Williams'),
                        'ADX': adx,
                    }
                    
                    # Use Strategy 5's validation method
                    is_valid, reason = self.strategy.validate_buy_signal(indicator_values)
                    
                    if not is_valid:
                        skipped_momentum += 1
                        continue
                
                # Track volume for reporting but don't filter on it (unless breakout)
                has_volume_surge = volume_ratio >= 1.3
                
                # Check if in uptrend (for reporting)
                in_uptrend = pd.notna(sma_50) and close > sma_50 and sma_20 > sma_50
                
                # Calculate confidence based on validation results
                confidence = conditions_met / 3 * 100
                if adx >= 25:
                    confidence += 10  # Bonus for strong trend
                if in_uptrend:
                    confidence += 5   # Bonus for uptrend
                if has_volume_surge:
                    confidence += 5   # Bonus for volume
                
                signals.append({
                    'date': row.name,
                    'index': i,
                    'entry_price': close,
                    'volume_ratio': round(volume_ratio, 2),
                    'has_volume_surge': has_volume_surge,
                    'in_uptrend': in_uptrend,
                    'rsi': round(rsi, 1),
                    'adx': round(adx, 1),
                    'atr': round(row.get('ATR', 0), 2),
                    'conditions_met': conditions_met,
                    'conditions': conditions,
                    'confidence': round(min(confidence, 100), 1)
                })
            
            skip_summary = f"skipped: {skipped_adx} ADX, {skipped_momentum} momentum, {skipped_trend} trend, {skipped_cooldown} cooldown"
            if self.REQUIRE_VOLUME_SURGE:
                skip_summary += f", {skipped_volume} volume"
            logger.info(f"[Backtest] Strategy {self.strategy_id}: Generated {len(signals)} signals ({skip_summary})")
            return signals
            
        except Exception as e:
            logger.error(f"[Backtest] Error generating signals: {str(e)}")
            return []
    
    def _simulate_trades(self, df: pd.DataFrame, signals: List[Dict]) -> List[Dict]:
        """
        Simulate trades from entry signals using Strategy 5 SMART STOP LOSS.
        
        SMART STOP LOSS LOGIC:
        1. Base stop: 3% below entry
        2. ATR-based stop: entry - (ATR × 1.5) for volatile conditions
        3. Maximum cap: 4% (never lose more than 4%)
        4. Use WIDER stop when ATR indicates high volatility
           (reduces stop-and-reverse scenarios)
        
        IMPROVEMENTS (Dec 2025) - Synced with Strategy 5:
        - Skip incomplete trades (not enough bars to reach target/stop)
        - Track cooldown after losses
        
        For each signal:
        - Entry at signal close price
        - Target: 4% above entry (optimized from 5%)
        - Stop: Smart dynamic (3-4% based on volatility)
        - Holding: Up to 15 bars (~3 weeks)
        """
        trades = []
        incomplete_trades = []  # Track trades with insufficient data
        last_loss_bar = None    # For cooldown tracking in signals
        
        try:
            for signal in signals:
                entry_index = signal['index']
                entry_price = signal['entry_price']
                entry_date = signal['date']
                atr = signal.get('atr', 0)
                
                # COOLDOWN CHECK - Skip if within cooldown period after loss
                if self.USE_LOSS_COOLDOWN and last_loss_bar is not None:
                    bars_since_loss = entry_index - last_loss_bar
                    if bars_since_loss < self.COOLDOWN_BARS:
                        continue  # Skip this signal, still in cooldown
                
                # Calculate target (4%)
                target = entry_price * (1 + self.TARGET_PCT / 100)
                
                # SMART STOP LOSS CALCULATION
                # Base stop: 3%
                base_stop = entry_price * (1 - self.STOP_LOSS_PCT / 100)
                # Maximum stop: 4% (cap)
                max_stop = entry_price * (1 - self.MAX_STOP_LOSS_PCT / 100)
                
                if atr > 0 and self.USE_WIDER_STOP:
                    # ATR-based dynamic stop
                    atr_stop = entry_price - (self.ATR_MULTIPLIER * atr)
                    
                    # SMART LOGIC: Use WIDER stop in volatile conditions
                    # but cap at maximum (4%)
                    # wider stop = lower price = more room before stop hit
                    stop_loss = min(base_stop, max(atr_stop, max_stop))
                else:
                    stop_loss = base_stop
                
                # Calculate available bars for this trade
                available_bars = len(df) - entry_index - 1
                
                # INCOMPLETE TRADE CHECK (Dec 2025) - Synced with Strategy 5
                # Skip trades that don't have minimum bars to be valid
                if self.SKIP_INCOMPLETE_TRADES and available_bars < self.MIN_BARS_FOR_VALID_TRADE:
                    incomplete_trades.append({
                        'entry_date': entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date),
                        'entry_price': round(entry_price, 2),
                        'available_bars': available_bars,
                        'reason': f'Only {available_bars} bars available (need {self.MIN_BARS_FOR_VALID_TRADE})'
                    })
                    continue
                
                # Find exit point (look forward up to MAX_BARS)
                outcome = self._find_exit(df, entry_index, entry_price, target, stop_loss)
                
                if outcome:
                    outcome['entry_date'] = entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date)
                    outcome['entry_price'] = round(entry_price, 2)
                    outcome['target'] = round(target, 2)
                    outcome['stop_loss'] = round(stop_loss, 2)
                    outcome['confidence'] = signal['confidence']
                    outcome['rsi'] = signal.get('rsi', 'N/A')
                    outcome['volume_ratio'] = signal.get('volume_ratio', 'N/A')
                    outcome['in_uptrend'] = signal.get('in_uptrend', True)
                    
                    # Update last_loss_bar for cooldown tracking
                    if outcome['outcome'] == 'LOSS':
                        last_loss_bar = entry_index + outcome.get('bars_held', 0)
                    
                    trades.append(outcome)
            
            if incomplete_trades:
                logger.info(f"[Backtest] Excluded {len(incomplete_trades)} incomplete trades (insufficient bars)")
            logger.info(f"[Backtest] Simulated {len(trades)} valid trades")
            return trades, incomplete_trades
            
        except Exception as e:
            logger.error(f"[Backtest] Error simulating trades: {str(e)}")
            return [], []
    
    def _find_exit(self, df: pd.DataFrame, entry_index: int,
                   entry_price: float, target: float, stop_loss: float) -> Optional[Dict]:
        """
        Find exit point: did price hit target or stop loss first?
        
        Lookback: 10 bars (approximately 2 weeks of trading days)
        
        Returns:
            {
                'outcome': 'WIN' | 'LOSS',
                'exit_price': float,
                'pnl_pct': float,
                'bars_held': int,
                'exit_date': str,
                'reason': 'Hit 4% target' | 'Hit stop loss' | 'Time exit'
            }
        """
        max_bars = min(self.MAX_BARS, len(df) - entry_index - 1)  # Use class constant
        
        try:
            last_close = df.iloc[entry_index]['close']
            exit_date = df.iloc[entry_index].name
            
            for i in range(1, max_bars + 1):
                row = df.iloc[entry_index + i]
                high = row['high']
                low = row['low']
                last_close = row['close']
                exit_date = row.name
                
                # Check if target was hit (use high price)
                if high >= target:
                    pnl_pct = ((target - entry_price) / entry_price) * 100
                    return {
                        'outcome': 'WIN',
                        'exit_price': round(target, 2),
                        'exit_date': exit_date.strftime('%Y-%m-%d') if hasattr(exit_date, 'strftime') else str(exit_date),
                        'pnl_pct': round(pnl_pct, 2),
                        'bars_held': i,
                        'reason': f'Hit {self.TARGET_PCT}% target'
                    }
                
                # Check if stop loss was hit (use low price)
                if low <= stop_loss:
                    pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                    return {
                        'outcome': 'LOSS',
                        'exit_price': round(stop_loss, 2),
                        'exit_date': exit_date.strftime('%Y-%m-%d') if hasattr(exit_date, 'strftime') else str(exit_date),
                        'pnl_pct': round(pnl_pct, 2),
                        'bars_held': i,
                        'reason': 'Hit stop loss'
                    }
            
            # No exit found in lookback period, exit at last close
            pnl_pct = ((last_close - entry_price) / entry_price) * 100
            outcome = 'WIN' if pnl_pct > 0 else 'LOSS'
            
            # Determine reason based on actual bars held
            if max_bars >= self.MAX_BARS:
                reason = f'Time exit ({self.MAX_BARS} bars)'
            elif max_bars > 0:
                reason = f'End of data ({max_bars} bars)'
            else:
                reason = 'No data available'
            
            return {
                'outcome': outcome,
                'exit_price': round(last_close, 2),
                'exit_date': exit_date.strftime('%Y-%m-%d') if hasattr(exit_date, 'strftime') else str(exit_date),
                'pnl_pct': round(pnl_pct, 2),
                'bars_held': max_bars,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"[Backtest] Error finding exit: {str(e)}")
            return None
    
    def _calculate_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comprehensive backtesting metrics.
        
        Returns:
            {
                'total_signals': int,
                'winning_trades': int,
                'losing_trades': int,
                'win_rate': float (0-100),
                'profit_factor': float,
                'total_profit_pct': float,
                'avg_win': float,
                'avg_loss': float,
                'max_drawdown': float,
                'consecutive_wins': int,
                'trades_per_day': float
            }
        """
        if not trades:
            return {
                'total_signals': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_profit_pct': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_drawdown': 0,
                'consecutive_wins': 0,
                'trades_per_day': 0
            }
        
        # Separate wins and losses
        wins = [t for t in trades if t['outcome'] == 'WIN']
        losses = [t for t in trades if t['outcome'] == 'LOSS']
        
        total_trades = len(trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # Profit metrics
        # total_win_pct: sum of positive P&L from winning trades
        # total_loss_pct: sum of absolute values of negative P&L from losing trades
        total_win_pct = sum(t['pnl_pct'] for t in wins) if wins else 0
        total_loss_pct = sum(abs(t['pnl_pct']) for t in losses) if losses else 0
        
        # Net profit = wins - losses (since loss_pct is already positive via abs())
        net_profit_pct = total_win_pct - total_loss_pct
        
        # Profit factor: sum of wins / sum of losses (higher is better, >1 means profitable)
        if total_loss_pct > 0:
            profit_factor = total_win_pct / total_loss_pct
        elif total_win_pct > 0:
            profit_factor = 999.99  # No losses = excellent (cap at 999.99)
        else:
            profit_factor = 0
        
        # Average win/loss per trade
        avg_win = (total_win_pct / len(wins)) if wins else 0
        avg_loss = -(total_loss_pct / len(losses)) if losses else 0  # Negative for display
        
        # Maximum drawdown (peak-to-trough decline)
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in trades:
            cumulative += trade['pnl_pct']
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        # Consecutive wins (streak tracking)
        max_consecutive = 0
        current_consecutive = 0
        for trade in trades:
            if trade['outcome'] == 'WIN':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        # Expectancy: average profit per trade (key metric for strategy evaluation)
        expectancy = net_profit_pct / total_trades if total_trades > 0 else 0
        
        # Trades per day (from actual period)
        trades_per_day = round(total_trades / 90, 2) if total_trades > 0 else 0
        
        return {
            'total_signals': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'total_profit_pct': round(net_profit_pct, 2),  # FIXED: was incorrectly adding losses
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'expectancy': round(expectancy, 2),  # NEW: avg profit per trade
            'max_drawdown': round(-max_dd, 2),
            'consecutive_wins': max_consecutive,
            'trades_per_day': trades_per_day
        }
