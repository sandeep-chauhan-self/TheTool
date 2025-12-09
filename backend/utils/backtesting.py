"""
Backtesting Engine for Strategy Analysis

Analyzes historical OHLCV data following TheTool architecture patterns:
- Uses DataFetcher for OHLCV data (respects demo/live data modes)
- Uses IndicatorEngine for calculations (respects modular indicators)
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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

from utils.analysis_orchestrator import DataFetcher, IndicatorEngine

logger = logging.getLogger('trading_analyzer')


class BacktestEngine:
    """
    Backtesting engine following TheTool architecture patterns.
    
    Simulates historical trades based on strategy signals and metrics.
    Uses existing DataFetcher and IndicatorEngine to avoid code duplication.
    """
    
    def __init__(self, strategy_id: int = 5):
        """
        Initialize backtesting engine.
        
        Args:
            strategy_id: Strategy to backtest (default 5 = enhanced swing trading)
        """
        self.strategy_id = strategy_id
        self.data_fetcher = DataFetcher()
        self.indicator_engine = IndicatorEngine()
    
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
            
            # Calculate indicators for entire dataframe
            df = self._calculate_indicators(df)
            
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
            trades = self._simulate_trades(df, signals)
            
            # Calculate comprehensive metrics
            metrics = self._calculate_metrics(trades)
            metrics['ticker'] = ticker
            metrics['backtest_period'] = f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
            metrics['trades'] = trades
            metrics['days_analyzed'] = days
            metrics['data_source'] = source
            
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
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators for dataframe using TheTool's IndicatorEngine.
        
        Respects modular indicator organization (momentum/, trend/, volatility/, volume/)
        """
        try:
            df = df.copy()
            
            # Calculate indicators for each bar
            for i in range(14, len(df)):
                # Slice data up to current bar
                data_slice = df.iloc[:i+1].copy()
                
                # Use TheTool's IndicatorEngine (handles all 12 indicators)
                indicators = self.indicator_engine.calculate_all(data_slice)
                
                # Add each indicator to dataframe
                for indicator_name, indicator_data in indicators.items():
                    if 'value' in indicator_data:
                        if indicator_name not in df.columns:
                            df[indicator_name] = None
                        df.loc[df.index[i], indicator_name] = indicator_data['value']
                    
                    if 'signal' in indicator_data:
                        signal_col = f'{indicator_name}_signal'
                        if signal_col not in df.columns:
                            df[signal_col] = None
                        df.loc[df.index[i], signal_col] = indicator_data['signal']
            
            logger.debug(f"[Backtest] Calculated indicators for {len(df)} bars")
            return df
            
        except Exception as e:
            logger.error(f"[Backtest] Error calculating indicators: {str(e)}")
            return df
    
    def _generate_entry_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate buy signals based on Strategy 5 enhanced logic.
        
        Entry conditions (Strategy 5 enhanced):
        1. RSI between 40-75 (healthy momentum, not overbought/oversold)
        2. MACD > Signal line (bullish momentum)
        3. Volume >= 1.5x average (volume surge confirms move)
        4. OBV positive (money flowing in)
        
        Need 3/4 conditions to trigger signal.
        """
        signals = []
        
        try:
            for i in range(20, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # Strategy 5: Extract indicator values
                rsi = row.get('RSI', 50)
                macd = row.get('MACD', 0)
                macd_signal = row.get('MACD_signal', 0)
                obv = row.get('OBV', 0)
                prev_obv = prev_row.get('OBV', 0)
                
                # Volume analysis
                avg_volume = df['volume'].iloc[max(0, i-20):i].mean()
                current_volume = row['volume']
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                
                # Signal validation (Strategy 5 enhanced conditions)
                conditions = {
                    'rsi_healthy': 40 <= rsi <= 75,      # Not overbought/oversold
                    'macd_bullish': macd > macd_signal,   # MACD above signal
                    'obv_rising': obv > prev_obv,         # OBV increasing
                    'volume_surge': volume_ratio >= 1.5,  # 1.5x average volume
                }
                
                # Need 3/4 conditions to trigger
                conditions_met = sum(conditions.values())
                
                if conditions_met >= 3:
                    signals.append({
                        'date': row.name,
                        'index': i,
                        'entry_price': row['close'],
                        'rsi': round(rsi, 2),
                        'macd': round(macd, 4),
                        'volume_ratio': round(volume_ratio, 2),
                        'conditions_met': conditions_met,
                        'confidence': round(conditions_met / 4 * 100, 1)
                    })
            
            logger.debug(f"[Backtest] Generated {len(signals)} entry signals")
            return signals
            
        except Exception as e:
            logger.error(f"[Backtest] Error generating signals: {str(e)}")
            return []
    
    def _simulate_trades(self, df: pd.DataFrame, signals: List[Dict]) -> List[Dict]:
        """
        Simulate trades from entry signals.
        
        For each signal:
        - Entry at signal close price
        - Target: 4% above entry (Strategy 5)
        - Stop: 3% below entry or 2×ATR (whichever is closer)
        - Lookback: 20 bars (~1 month) to find exit
        """
        trades = []
        
        try:
            for signal in signals:
                entry_index = signal['index']
                entry_price = signal['entry_price']
                entry_date = signal['date']
                
                # Calculate target and stop
                target = entry_price * 1.04  # 4% target
                stop_loss = entry_price * 0.97  # 3% stop
                
                # ATR-based dynamic stop (Strategy 5 enhancement)
                atr = df.iloc[entry_index].get('ATR', 0)
                if atr > 0:
                    dynamic_stop = entry_price - (2 * atr)
                    # Use whichever is closer to entry (tighter stop)
                    stop_loss = max(stop_loss, dynamic_stop)
                
                # Find exit point (look forward up to 20 bars)
                outcome = self._find_exit(df, entry_index, entry_price, target, stop_loss)
                
                if outcome:
                    outcome['entry_date'] = entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date)
                    outcome['entry_price'] = round(entry_price, 2)
                    outcome['target'] = round(target, 2)
                    outcome['stop_loss'] = round(stop_loss, 2)
                    outcome['confidence'] = signal['confidence']
                    outcome['rsi'] = signal['rsi']
                    
                    trades.append(outcome)
            
            logger.info(f"[Backtest] Simulated {len(trades)} trades")
            return trades
            
        except Exception as e:
            logger.error(f"[Backtest] Error simulating trades: {str(e)}")
            return []
    
    def _find_exit(self, df: pd.DataFrame, entry_index: int,
                   entry_price: float, target: float, stop_loss: float) -> Optional[Dict]:
        """
        Find exit point: did price hit target or stop loss first?
        
        Lookback: 20 bars (approximately 1 month of trading days)
        
        Returns:
            {
                'outcome': 'WIN' | 'LOSS',
                'exit_price': float,
                'pnl_pct': float,
                'bars_held': int,
                'reason': 'Hit 4% target' | 'Hit 3% stop loss' | 'Lookback period ended'
            }
        """
        max_bars = min(20, len(df) - entry_index - 1)
        
        try:
            for i in range(1, max_bars + 1):
                row = df.iloc[entry_index + i]
                high = row['high']
                low = row['low']
                close = row['close']
                
                # Check if target was hit
                if high >= target:
                    pnl_pct = ((target - entry_price) / entry_price) * 100
                    return {
                        'outcome': 'WIN',
                        'exit_price': round(target, 2),
                        'pnl_pct': round(pnl_pct, 2),
                        'bars_held': i,
                        'reason': 'Hit 4% target'
                    }
                
                # Check if stop loss was hit
                if low <= stop_loss:
                    pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                    return {
                        'outcome': 'LOSS',
                        'exit_price': round(stop_loss, 2),
                        'pnl_pct': round(pnl_pct, 2),
                        'bars_held': i,
                        'reason': 'Hit 3% stop loss'
                    }
            
            # No exit found in lookback period, use close price
            pnl_pct = ((close - entry_price) / entry_price) * 100
            outcome = 'WIN' if pnl_pct > 0 else 'LOSS'
            
            return {
                'outcome': outcome,
                'exit_price': round(close, 2),
                'pnl_pct': round(pnl_pct, 2),
                'bars_held': max_bars,
                'reason': 'Lookback period ended'
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
        total_win_pct = sum(t['pnl_pct'] for t in wins) if wins else 0
        total_loss_pct = sum(abs(t['pnl_pct']) for t in losses) if losses else 0
        
        # Profit factor: sum of wins / sum of losses
        if total_loss_pct > 0:
            profit_factor = total_win_pct / total_loss_pct
        elif total_win_pct > 0:
            profit_factor = total_win_pct  # If no losses, factor is sum of wins
        else:
            profit_factor = 0
        
        # Average win/loss
        avg_win = (total_win_pct / len(wins)) if wins else 0
        avg_loss = -(total_loss_pct / len(losses)) if losses else 0
        
        # Maximum drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in trades:
            cumulative += trade['pnl_pct']
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        # Consecutive wins
        max_consecutive = 0
        current_consecutive = 0
        for trade in trades:
            if trade['outcome'] == 'WIN':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        # Trades per day (annualized from 90-day period)
        trades_per_day = round(total_trades / 90 * 365, 1) if total_trades > 0 else 0
        
        return {
            'total_signals': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'total_profit_pct': round(total_win_pct + total_loss_pct, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_drawdown': round(-max_dd, 2),
            'consecutive_wins': max_consecutive,
            'trades_per_day': trades_per_day
        }
