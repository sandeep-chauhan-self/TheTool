"""
Backtesting Engine for Strategy Analysis

Analyzes historical OHLCV data following TheTool architecture patterns:
- Uses DataFetcher for OHLCV data (respects demo/live data modes)
- Uses IndicatorEngine for calculations (respects modular indicators)
- Integrates with Strategy 5 enhanced validation methods
- Thread-safe with get_db_session() for background job compatibility
- Uses _convert_query_params() for PostgreSQL/SQLite database abstraction
- Centralized logging via utils.logger.get_logger()

Architecture Pattern:
- Single Responsibility: Only handles trade simulation and metrics
- Modular: Uses existing DataFetcher and IndicatorEngine, doesn't duplicate
- Database agnostic: No direct SQL, uses db layer abstractions
- Thread-safe: Suitable for background job processing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

from utils.analysis_orchestrator import DataFetcher
from strategies.strategy_5 import Strategy5

logger = logging.getLogger('trading_analyzer')


class BacktestEngine:
    """
    Backtesting engine following TheTool architecture patterns.
    
    Simulates historical trades based on Strategy 5 enhanced signals.
    Uses existing DataFetcher and IndicatorEngine to avoid code duplication.
    Integrates Strategy 5 validation methods for accurate backtesting.
    """
    
    # Strategy 5 parameters (synchronized with strategy_5.py)
    # OPTIMIZED based on 15-stock backtest analysis (Dec 2025)
    # Key findings from comprehensive_backtest_analysis.py:
    # 1. Volume 1.3-1.5x is SWEET SPOT (80% win rate vs 65% for others)
    # 2. RSI 50-75 performs better (64-72% win rate)
    # 3. 15-bar holding captures more gains (time exits have 72.3% win rate)
    # 4. Lower confidence signals actually perform better (67% vs 61%)
    TARGET_PCT = 4.0       # 4% target - 44.9% hit rate is good
    MAX_BARS = 15          # 15 bars holding - 72.3% time exit win rate
    STOP_LOSS_PCT = 3.0    # Base stop: 3%
    MAX_STOP_LOSS_PCT = 4.0  # Maximum stop: 4% (cap)
    ATR_MULTIPLIER = 1.5   # Dynamic stop = Entry - (ATR x 1.5)
    USE_WIDER_STOP = True  # Use wider stop in volatile conditions
    
    # VOLUME SWEET SPOT FILTER (NEW - Dec 2025)
    # Analysis showed: 1.3-1.5x volume = 80% win rate, 2.34% avg P&L
    # But hard filter is too restrictive (only 21 signals vs 392)
    # Alternative: Disable hard filter, use volume as confidence boost only
    USE_VOLUME_SWEET_SPOT = False  # DISABLED - too restrictive
    MIN_VOLUME_RATIO = 1.0         # No minimum (was 1.3)
    MAX_VOLUME_RATIO = 100.0       # No maximum (was 1.5)
    VOLUME_SWEET_SPOT_MIN = 1.3    # For confidence boost calculation
    VOLUME_SWEET_SPOT_MAX = 1.5    # For confidence boost calculation
    
    # RSI OPTIMIZATION (Dec 2025)
    # Analysis showed: RSI 50-75 has 64-72% win rate
    # RSI 40-50 only 48% win rate - too weak
    RSI_MIN = 50           # Raised from 30 - stronger momentum required
    RSI_MAX = 75           # Maximum RSI (avoid overbought)
    
    MIN_CONDITIONS = 2     # Need at least 2 of 3 conditions
    ADX_CHOPPY_THRESHOLD = 20  # ADX below this = choppy market, skip signal
    USE_ADX_FILTER = True  # Enable ADX regime filtering
    
    # VALIDATION LOOSENING (Dec 2025)
    # Analysis showed lower confidence signals perform BETTER (67% vs 61%)
    # But disabling validation reduced expectancy from 1.18% to 1.02%
    # Keep validation ON for quality, rely on RSI 50-75 for filtering weak signals
    USE_STRATEGY5_VALIDATION = True  # RE-ENABLED - quality over quantity
    
    # TREND FILTER (Dec 2025) - Synced with Strategy 5
    # Avoid buying in downtrends - major cause of losses
    USE_TREND_FILTER = True          # Enable SMA 50 trend filter
    SMA_TREND_PERIOD = 50            # 50-day SMA for trend direction
    
    # COOLDOWN AFTER LOSS (Dec 2025) - Synced with Strategy 5
    # Avoid rapid re-entry after stop loss (Nov 3-5 clustering issue)
    USE_LOSS_COOLDOWN = True         # Enable cooldown after loss
    COOLDOWN_BARS = 3                # Wait 3 bars after a loss
    
    # INCOMPLETE TRADE HANDLING (Dec 2025)
    # Don't count trades that didn't have enough bars to reach target/stop
    MIN_BARS_FOR_VALID_TRADE = 5     # Need at least 5 bars for valid trade
    SKIP_INCOMPLETE_TRADES = True    # Exclude trades with insufficient data
    
    def __init__(self, strategy_id: int = 5):
        """
        Initialize backtesting engine.
        
        Args:
            strategy_id: Strategy to backtest (default 5 = enhanced swing trading)
        """
        self.strategy_id = strategy_id
        self.data_fetcher = DataFetcher()
        self.strategy_5 = Strategy5()  # For validation methods
    
    def backtest_ticker(self, ticker: str, days: int = 90) -> Dict[str, Any]:
        """
        Run backtest for a single ticker.
        
        Uses TheTool patterns:
        - DataFetcher for data retrieval (respects demo/live modes)
        - IndicatorEngine for calculations (respects modular indicators)
        
        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')
            days: Historical days to analyze (30-365, default 90)
        
        Returns:
            {
                'ticker': 'RELIANCE.NS',
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
                    'ticker': ticker
                }
            
            logger.info(f"[Backtest] Fetched {len(df)} candles for {ticker} (source: {source})")
            
            # Trim to requested days
            if len(df) > days:
                df = df.iloc[-days:]
            
            # Normalize column names (DataFetcher returns capitalized names)
            df.columns = df.columns.str.lower()
            
            # Calculate indicators for entire dataframe
            df = self._calculate_indicators(df, ticker)
            
            # Generate buy signals based on Strategy 5 logic
            signals = self._generate_entry_signals(df)
            
            if not signals:
                logger.info(f"[Backtest] No signals generated for {ticker}")
                return {
                    'ticker': ticker,
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
            alpha = 1.0 / 14
            tr_smooth = pd.Series(tr).ewm(alpha=alpha, adjust=False).mean()
            dm_plus_smooth = pd.Series(dm_plus).ewm(alpha=alpha, adjust=False).mean()
            dm_minus_smooth = pd.Series(dm_minus).ewm(alpha=alpha, adjust=False).mean()
            
            # DI+ and DI-
            di_plus = 100 * (dm_plus_smooth / tr_smooth)
            di_minus = 100 * (dm_minus_smooth / tr_smooth)
            
            # DX and ADX
            dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
            df['ADX'] = pd.Series(dx).ewm(alpha=alpha, adjust=False).mean()
            df['DI_plus'] = di_plus
            df['DI_minus'] = di_minus
            
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
        Generate buy signals based on Strategy 5 enhanced logic.
        
        IMPROVED: Now integrates Strategy 5 validation methods:
        1. Price is above 20-day SMA (uptrend confirmation)
        2. RSI between 50-75 (healthy momentum, not overbought/oversold)
        3. ADX > 20 (trending market, skip choppy conditions)
        4. Strategy 5 momentum validation (MACD bullish, 3+ indicators aligned)
        5. Price rising (close > previous close)
        6. TREND FILTER: Price > SMA(50) and SMA(20) > SMA(50) (Dec 2025)
        7. COOLDOWN: Wait 3 bars after a loss before next signal (Dec 2025)
        
        Uses Strategy 5's validate_buy_signal() for additional filtering.
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
                
                # Skip if RSI is invalid (overbought or too weak)
                if pd.isna(rsi) or rsi > self.RSI_MAX or rsi < self.RSI_MIN:
                    continue
                
                # TREND FILTER (Dec 2025) - Synced with Strategy 5
                # Skip if in downtrend: both price and SMA_20 must be above SMA_50
                if self.USE_TREND_FILTER:
                    if pd.notna(sma_50) and (close < sma_50 or sma_20 < sma_50):
                        skipped_trend += 1
                        continue
                
                # COOLDOWN FILTER (Dec 2025) - Synced with Strategy 5
                # Wait X bars after a loss before taking another signal
                if self.USE_LOSS_COOLDOWN and last_loss_bar is not None:
                    bars_since_loss = i - last_loss_bar
                    if bars_since_loss < self.COOLDOWN_BARS:
                        skipped_cooldown += 1
                        continue
                
                # ADX Market Regime Filter: Skip choppy markets
                if self.USE_ADX_FILTER and adx < self.ADX_CHOPPY_THRESHOLD:
                    skipped_adx += 1
                    continue
                
                # Volume Sweet Spot Filter: Only take trades with optimal volume
                # Analysis showed 1.3-1.5x volume has 80% win rate vs 53-66% for others
                if self.USE_VOLUME_SWEET_SPOT:
                    if volume_ratio < self.MIN_VOLUME_RATIO or volume_ratio > self.MAX_VOLUME_RATIO:
                        continue  # Skip non-sweet-spot volume
                
                # Strategy 5 conditions
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
                
                # Strategy 5 Momentum Validation (optional but recommended)
                if self.USE_STRATEGY5_VALIDATION:
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
                    is_valid, reason = self.strategy_5.validate_buy_signal(indicator_values)
                    
                    if not is_valid:
                        skipped_momentum += 1
                        continue
                
                # Track volume for reporting but don't filter on it
                has_volume_surge = volume_ratio >= 1.3  # Track but don't require
                
                # Check if in uptrend (for reporting)
                in_uptrend = pd.notna(sma_50) and close > sma_50 and sma_20 > sma_50
                
                # Calculate confidence based on validation results
                confidence = conditions_met / 3 * 100
                if adx >= 25:
                    confidence += 10  # Bonus for strong trend
                if in_uptrend:
                    confidence += 5   # Bonus for uptrend
                
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
            
            logger.info(f"[Backtest] Generated {len(signals)} signals (skipped: {skipped_adx} ADX, {skipped_momentum} momentum, {skipped_trend} trend, {skipped_cooldown} cooldown)")
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
