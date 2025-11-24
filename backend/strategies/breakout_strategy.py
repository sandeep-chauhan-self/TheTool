"""
Breakout Trading Strategy (Enhanced)

Description:
Detects price breakouts from consolidation ranges using support/resistance levels
with multiple confirmation filters including volume, Supertrend, RSI, and MACD.

Entry/Exit Logic:
- Consolidation: Identifies support (min lows) and resistance (max highs) over rolling window
- Breakout: Price closes above resistance (bullish) or below support (bearish)
- Volume: Requires volume > average volume � 1.25 for confirmation
- Supertrend Filter: Only takes trades aligned with Supertrend direction
- RSI Filter: BULLISH requires RSI > 50, BEARISH requires RSI < 50
- MACD Filter: BULLISH requires MACD > Signal, BEARISH requires MACD < Signal
- Entry: Market price after breakout close + small offset
- Stop Loss: Below/above breakout level + ATR buffer
- Target: Consolidation height projected from entry

Configuration:
- Lookback period: 20 bars (configurable)
- Volume factor: 1.25� average (configurable)
- ATR multiplier: 1.0 for stop loss (configurable)
- Supertrend: period=10, multiplier=3 (from indicators)
- RSI threshold: 50 (configurable)
- Risk-reward: 2:1 default target

Filters (All Configurable):
- use_supertrend_filter: True/False (default: True)
- use_rsi_filter: True/False (default: True)
- use_macd_filter: True/False (default: True)

Author: TheTool Trading System
Version: 2.0.0 (Enhanced with multi-indicator filters)
"""

import pandas as pd
import numpy as np
import logging

from constants import (
    DEFAULT_LOOKBACK_PERIOD,
    DEFAULT_ATR_PERIOD,
    DEFAULT_EMA_PERIOD,
    DEFAULT_VOLUME_FACTOR,
    DEFAULT_ATR_MULTIPLIER,
    DEFAULT_RISK_REWARD_RATIO,
    DEFAULT_ENTRY_OFFSET_PCT,
    MIN_CONSOLIDATION_PCT,
    RSI_NEUTRAL_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Strategy configuration (using extracted constants)
CONFIG = {
    'lookback_period': DEFAULT_LOOKBACK_PERIOD,      # Bars to analyze for consolidation
    'volume_factor': DEFAULT_VOLUME_FACTOR,          # Volume must be > avg � this factor
    'atr_multiplier': DEFAULT_ATR_MULTIPLIER,        # Stop loss buffer (ATR � multiplier)
    'risk_reward_ratio': DEFAULT_RISK_REWARD_RATIO,  # Target = risk � this ratio
    'entry_offset_pct': DEFAULT_ENTRY_OFFSET_PCT,    # 0.5% above/below breakout close
    'min_consolidation_pct': MIN_CONSOLIDATION_PCT,  # Min 2% range for valid consolidation
    
    # Filter configuration
    'use_supertrend_filter': True,   # Filter trades by Supertrend trend
    'use_rsi_filter': True,           # Filter trades by RSI momentum
    'use_macd_filter': True,          # Filter trades by MACD trend
    'use_multitimeframe_filter': True,  # Check weekly timeframe alignment
    'rsi_bullish_threshold': RSI_NEUTRAL_THRESHOLD,   # RSI > 50 for BULLISH
    'rsi_bearish_threshold': RSI_NEUTRAL_THRESHOLD,   # RSI < 50 for BEARISH
}


def calculate_atr(df, period=DEFAULT_ATR_PERIOD):
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period (default from constant)
    
    Returns:
        float: Current ATR value
    """
    try:
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(tr[-period:]) if len(tr) >= period else np.mean(tr)
        
        return atr
    except Exception as e:
        logger.error(f"ATR calculation error: {e}")
        return 0.0


def calculate_ema(df, period=DEFAULT_EMA_PERIOD):
    """
    Calculate Exponential Moving Average
    
    Args:
        df: DataFrame with Close prices
        period: EMA period (default from constant)
    
    Returns:
        float: Current EMA value
    """
    try:
        return df['Close'].ewm(span=period, adjust=False).mean().iloc[-1]
    except Exception as e:
        logger.error(f"EMA calculation error: {e}")
        return df['Close'].iloc[-1] if len(df) > 0 else 0.0


def detect_consolidation(df, lookback=DEFAULT_LOOKBACK_PERIOD):
    """
    Detect consolidation range (support and resistance)
    
    Args:
        df: DataFrame with OHLC data
        lookback: Number of bars to analyze (default from constant)
    
    Returns:
        dict: {
            'support': float,
            'resistance': float,
            'height': float,
            'is_valid': bool
        }
    """
    try:
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.tail(lookback)
        
        support = recent_data['Low'].min()
        resistance = recent_data['High'].max()
        height = resistance - support
        
        # Check if consolidation is valid (not too tight)
        current_price = df['Close'].iloc[-1]
        height_pct = height / current_price
        is_valid = height_pct >= CONFIG['min_consolidation_pct']
        
        return {
            'support': support,
            'resistance': resistance,
            'height': height,
            'height_pct': height_pct,
            'is_valid': is_valid
        }
    except Exception as e:
        logger.error(f"Consolidation detection error: {e}")
        return {
            'support': 0.0,
            'resistance': 0.0,
            'height': 0.0,
            'height_pct': 0.0,
            'is_valid': False
        }


def check_volume_confirmation(df, lookback=20):
    """
    Check if current volume exceeds average volume
    
    Args:
        df: DataFrame with Volume data
        lookback: Number of bars for average calculation
    
    Returns:
        dict: {
            'current_volume': float,
            'avg_volume': float,
            'is_confirmed': bool,
            'volume_ratio': float
        }
    """
    try:
        if len(df) < lookback:
            lookback = len(df)
        
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].tail(lookback).mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0.0
        is_confirmed = volume_ratio >= CONFIG['volume_factor']
        
        return {
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'is_confirmed': is_confirmed
        }
    except Exception as e:
        logger.error(f"Volume confirmation error: {e}")
        return {
            'current_volume': 0.0,
            'avg_volume': 0.0,
            'volume_ratio': 0.0,
            'is_confirmed': False
        }


def detect_breakout(df, consolidation):
    """
    Detect if price has broken out of consolidation range
    
    Args:
        df: DataFrame with OHLC data
        consolidation: Consolidation range dict
    
    Returns:
        dict: {
            'breakout_type': 'BULLISH' | 'BEARISH' | 'NONE',
            'close_price': float,
            'breakout_level': float
        }
    """
    try:
        close_price = df['Close'].iloc[-1]
        support = consolidation['support']
        resistance = consolidation['resistance']
        
        if close_price > resistance:
            return {
                'breakout_type': 'BULLISH',
                'close_price': close_price,
                'breakout_level': resistance
            }
        elif close_price < support:
            return {
                'breakout_type': 'BEARISH',
                'close_price': close_price,
                'breakout_level': support
            }
        else:
            return {
                'breakout_type': 'NONE',
                'close_price': close_price,
                'breakout_level': 0.0
            }
    except Exception as e:
        logger.error(f"Breakout detection error: {e}")
        return {
            'breakout_type': 'NONE',
            'close_price': 0.0,
            'breakout_level': 0.0
        }


def calculate_entry_stop_target(df, breakout, consolidation, atr):
    """
    Calculate entry price, stop loss, and target
    
    Args:
        df: DataFrame with OHLC data
        breakout: Breakout detection dict
        consolidation: Consolidation range dict
        atr: ATR value
    
    Returns:
        dict: {
            'entry_price': float,
            'stop_loss': float,
            'target': float,
            'risk': float,
            'reward': float,
            'risk_reward_ratio': float
        }
    """
    try:
        close_price = breakout['close_price']
        breakout_level = breakout['breakout_level']
        breakout_type = breakout['breakout_type']
        height = consolidation['height']
        
        if breakout_type == 'BULLISH':
            # Entry: Slightly above breakout close
            entry_price = close_price * (1 + CONFIG['entry_offset_pct'])
            
            # Stop Loss: Below breakout level with ATR buffer
            stop_loss = breakout_level - (atr * CONFIG['atr_multiplier'])
            
            # Target: Entry + consolidation height (projected breakout)
            target = entry_price + height
            
        elif breakout_type == 'BEARISH':
            # Entry: Slightly below breakout close
            entry_price = close_price * (1 - CONFIG['entry_offset_pct'])
            
            # Stop Loss: Above breakout level with ATR buffer
            stop_loss = breakout_level + (atr * CONFIG['atr_multiplier'])
            
            # Target: Entry - consolidation height (projected breakdown)
            target = entry_price - height
            
        else:
            return {
                'entry_price': close_price,
                'stop_loss': close_price,
                'target': close_price,
                'risk': 0.0,
                'reward': 0.0,
                'risk_reward_ratio': 0.0
            }
        
        # Calculate risk and reward
        risk = abs(entry_price - stop_loss)
        reward = abs(target - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0.0
        
        return {
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'risk': round(risk, 2),
            'reward': round(reward, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2)
        }
    except Exception as e:
        logger.error(f"Entry/Stop/Target calculation error: {e}")
        close_price = df['Close'].iloc[-1] if len(df) > 0 else 0.0
        return {
            'entry_price': close_price,
            'stop_loss': close_price,
            'target': close_price,
            'risk': 0.0,
            'reward': 0.0,
            'risk_reward_ratio': 0.0
        }


def calculate_confidence(breakout, volume_check, consolidation, risk_reward_ratio, filters_passed=None):
    """
    Calculate strategy confidence score (0.0 - 1.0)
    
    Factors:
    - Valid consolidation: +0.20
    - Volume confirmation: +0.20
    - Good risk-reward (>1.5): +0.20
    - Breakout strength: +0.10
    - Supertrend alignment: +0.10 (NEW)
    - RSI confirmation: +0.05 (NEW)
    - MACD confirmation: +0.05 (NEW)
    - Multi-timeframe alignment: +0.10 (NEW)
    
    Args:
        breakout: Breakout detection dict
        volume_check: Volume confirmation dict
        consolidation: Consolidation range dict
        risk_reward_ratio: Calculated risk-reward ratio
        filters_passed: Dict with filter results (NEW)
    
    Returns:
        float: Confidence score (0.0 - 1.0)
    """
    confidence = 0.0
    
    # Valid consolidation
    if consolidation['is_valid']:
        confidence += 0.20
    
    # Volume confirmation
    if volume_check['is_confirmed']:
        confidence += 0.20
    
    # Good risk-reward ratio (> 1.5)
    if risk_reward_ratio >= 1.5:
        confidence += 0.20
    
    # Breakout strength (based on how far price moved beyond level)
    if breakout['breakout_type'] != 'NONE':
        breakout_strength = abs(breakout['close_price'] - breakout['breakout_level']) / breakout['breakout_level']
        confidence += min(breakout_strength * 10, 0.10)  # Max 0.10
    
    # NEW: Additional filters
    if filters_passed:
        if filters_passed.get('supertrend', False):
            confidence += 0.10
        if filters_passed.get('rsi', False):
            confidence += 0.05
        if filters_passed.get('macd', False):
            confidence += 0.05
        if filters_passed.get('multitimeframe', False):
            confidence += 0.10
    
    return round(min(confidence, 1.0), 2)


def analyze(data, indicators_result=None):
    """
    Analyze stock data and generate breakout trading signal
    
    Args:
        data: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
        indicators_result: Dict with pre-calculated indicator values (optional)
                          Expected keys: 'supertrend', 'rsi', 'macd' indicators
    
    Returns:
        dict: {
            'signal': 'BUY' | 'SELL' | 'NEUTRAL',
            'entry_price': float,
            'stop_loss': float,
            'target': float,
            'confidence': float (0.0-1.0),
            'reason': str,
            'strategy_name': str
        }
    """
    try:
        # Validate data
        if data is None or len(data) < CONFIG['lookback_period']:
            return {
                'signal': 'NEUTRAL',
                'entry_price': None,
                'stop_loss': None,
                'target': None,
                'confidence': 0.0,
                'reason': f'Insufficient data (need {CONFIG["lookback_period"]} bars minimum)',
                'strategy_name': 'Breakout Strategy'
            }
        
        # Step 1: Calculate indicators
        atr = calculate_atr(data)
        
        # Step 2: Detect consolidation range
        consolidation = detect_consolidation(data, CONFIG['lookback_period'])
        
        if not consolidation['is_valid']:
            return {
                'signal': 'NEUTRAL',
                'entry_price': None,
                'stop_loss': None,
                'target': None,
                'confidence': 0.0,
                'reason': f'No valid consolidation (range too tight: {consolidation["height_pct"]*100:.1f}%)',
                'strategy_name': 'Breakout Strategy'
            }
        
        # Step 3: Check volume confirmation
        volume_check = check_volume_confirmation(data, CONFIG['lookback_period'])
        
        # Step 4: Detect breakout
        breakout = detect_breakout(data, consolidation)
        
        if breakout['breakout_type'] == 'NONE':
            return {
                'signal': 'NEUTRAL',
                'entry_price': None,
                'stop_loss': None,
                'target': None,
                'confidence': 0.0,
                'reason': f'No breakout detected (price within {consolidation["support"]:.2f} - {consolidation["resistance"]:.2f})',
                'strategy_name': 'Breakout Strategy'
            }
        
        # NEW: Step 4.5: Apply filters
        filters_passed = {}
        filter_reasons = []
        
        # Extract indicator data if provided
        supertrend_data = None
        rsi_value = None
        macd_line = None
        macd_signal = None
        
        if indicators_result:
            # Find Supertrend indicator
            for ind in indicators_result:
                if ind.get('name') == 'Supertrend':
                    supertrend_data = ind
                elif ind.get('name') == 'RSI':
                    # RSI value should be in the data DataFrame
                    if 'RSI' in data.columns:
                        rsi_value = data['RSI'].iloc[-1]
                elif ind.get('name') == 'MACD':
                    # MACD values should be in the data DataFrame
                    if 'MACD' in data.columns and 'MACD_signal' in data.columns:
                        macd_line = data['MACD'].iloc[-1]
                        macd_signal = data['MACD_signal'].iloc[-1]
        
        # Supertrend filter
        if CONFIG['use_supertrend_filter'] and supertrend_data:
            current_price = data['Close'].iloc[-1]
            supertrend_value = supertrend_data.get('value', 0)
            
            if breakout['breakout_type'] == 'BULLISH':
                # For BULLISH breakout, price should be above Supertrend
                if current_price > supertrend_value:
                    filters_passed['supertrend'] = True
                    filter_reasons.append(f"? Supertrend uptrend (price {current_price:.2f} > ST {supertrend_value:.2f})")
                else:
                    filters_passed['supertrend'] = False
                    filter_reasons.append(f"? Supertrend downtrend (price {current_price:.2f} < ST {supertrend_value:.2f})")
                    # Reject trade if against trend
                    return {
                        'signal': 'NEUTRAL',
                        'entry_price': None,
                        'stop_loss': None,
                        'target': None,
                        'confidence': 0.0,
                        'reason': f'BULLISH breakout rejected: {filter_reasons[-1]}',
                        'strategy_name': 'Breakout Strategy'
                    }
            elif breakout['breakout_type'] == 'BEARISH':
                # For BEARISH breakout, price should be below Supertrend
                if current_price < supertrend_value:
                    filters_passed['supertrend'] = True
                    filter_reasons.append(f"? Supertrend downtrend (price {current_price:.2f} < ST {supertrend_value:.2f})")
                else:
                    filters_passed['supertrend'] = False
                    filter_reasons.append(f"? Supertrend uptrend (price {current_price:.2f} > ST {supertrend_value:.2f})")
                    # Reject trade if against trend
                    return {
                        'signal': 'NEUTRAL',
                        'entry_price': None,
                        'stop_loss': None,
                        'target': None,
                        'confidence': 0.0,
                        'reason': f'BEARISH breakout rejected: {filter_reasons[-1]}',
                        'strategy_name': 'Breakout Strategy'
                    }
        
        # RSI filter
        if CONFIG['use_rsi_filter'] and rsi_value is not None:
            if breakout['breakout_type'] == 'BULLISH':
                # For BULLISH, RSI should be > 50
                if rsi_value > CONFIG['rsi_bullish_threshold']:
                    filters_passed['rsi'] = True
                    filter_reasons.append(f"? RSI bullish ({rsi_value:.1f} > {CONFIG['rsi_bullish_threshold']})")
                else:
                    filters_passed['rsi'] = False
                    filter_reasons.append(f"? RSI weak ({rsi_value:.1f} < {CONFIG['rsi_bullish_threshold']})")
            elif breakout['breakout_type'] == 'BEARISH':
                # For BEARISH, RSI should be < 50
                if rsi_value < CONFIG['rsi_bearish_threshold']:
                    filters_passed['rsi'] = True
                    filter_reasons.append(f"? RSI bearish ({rsi_value:.1f} < {CONFIG['rsi_bearish_threshold']})")
                else:
                    filters_passed['rsi'] = False
                    filter_reasons.append(f"? RSI weak ({rsi_value:.1f} > {CONFIG['rsi_bearish_threshold']})")
        
        # MACD filter
        if CONFIG['use_macd_filter'] and macd_line is not None and macd_signal is not None:
            if breakout['breakout_type'] == 'BULLISH':
                # For BULLISH, MACD line should be > Signal line
                if macd_line > macd_signal:
                    filters_passed['macd'] = True
                    filter_reasons.append(f"? MACD bullish ({macd_line:.2f} > {macd_signal:.2f})")
                else:
                    filters_passed['macd'] = False
                    filter_reasons.append(f"? MACD bearish ({macd_line:.2f} < {macd_signal:.2f})")
            elif breakout['breakout_type'] == 'BEARISH':
                # For BEARISH, MACD line should be < Signal line
                if macd_line < macd_signal:
                    filters_passed['macd'] = True
                    filter_reasons.append(f"? MACD bearish ({macd_line:.2f} < {macd_signal:.2f})")
                else:
                    filters_passed['macd'] = False
                    filter_reasons.append(f"? MACD bullish ({macd_line:.2f} > {macd_signal:.2f})")
        
        # Multi-timeframe filter (check weekly trend if daily breakout)
        if CONFIG['use_multitimeframe_filter']:
            try:
                # Validate that data.index is a DatetimeIndex before resampling
                if not isinstance(data.index, pd.DatetimeIndex):
                    logger.warning("Data index is not DatetimeIndex, attempting conversion")
                    try:
                        # Attempt to convert index to datetime
                        converted_index = pd.to_datetime(data.index, errors='coerce')
                        # Count valid datetime values after conversion
                        valid_datetimes = converted_index.notna().sum()
                        
                        if valid_datetimes < len(data) * 0.8:  # Less than 80% valid
                            logger.warning(
                                f"Index conversion failed: only {valid_datetimes}/{len(data)} rows convertible to datetime. "
                                "Skipping multi-timeframe check."
                            )
                            filters_passed['multitimeframe'] = False
                            filter_reasons.append("? Multi-timeframe check skipped (invalid index)")
                        else:
                            # Replace index with converted datetime and drop NaT rows
                            data = data.copy()
                            data.index = converted_index
                            data = data.dropna(how='any', axis=0)
                            
                            if len(data) < 20:
                                logger.warning(
                                    f"After NaT removal, insufficient data for weekly analysis ({len(data)} rows < 20). "
                                    "Skipping multi-timeframe check."
                                )
                                filters_passed['multitimeframe'] = False
                                filter_reasons.append("? Multi-timeframe check skipped (insufficient data after NaT removal)")
                            else:
                                # Proceed with resampling
                                weekly_data = data.resample('W').agg({
                                    'Open': 'first',
                                    'High': 'max',
                                    'Low': 'min',
                                    'Close': 'last',
                                    'Volume': 'sum'
                                }).dropna()
                                
                                if len(weekly_data) >= 20:
                                    # Calculate weekly EMA20
                                    weekly_ema20 = weekly_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                                    weekly_close = weekly_data['Close'].iloc[-1]
                                    
                                    if breakout['breakout_type'] == 'BULLISH':
                                        if weekly_close > weekly_ema20:
                                            filters_passed['multitimeframe'] = True
                                            filter_reasons.append(f"? Weekly uptrend (close {weekly_close:.2f} > EMA {weekly_ema20:.2f})")
                                        else:
                                            filters_passed['multitimeframe'] = False
                                            filter_reasons.append(f"? Weekly downtrend (close {weekly_close:.2f} < EMA {weekly_ema20:.2f})")
                                    elif breakout['breakout_type'] == 'BEARISH':
                                        if weekly_close < weekly_ema20:
                                            filters_passed['multitimeframe'] = True
                                            filter_reasons.append(f"? Weekly downtrend (close {weekly_close:.2f} < EMA {weekly_ema20:.2f})")
                                        else:
                                            filters_passed['multitimeframe'] = False
                                            filter_reasons.append(f"? Weekly uptrend (close {weekly_close:.2f} > EMA {weekly_ema20:.2f})")
                                else:
                                    logger.warning("Insufficient weekly data for multi-timeframe analysis")
                                    filters_passed['multitimeframe'] = False
                                    filter_reasons.append("? Multi-timeframe check skipped (insufficient weekly data)")
                    except Exception as conversion_error:
                        logger.error(f"Failed to convert index to datetime: {conversion_error}")
                        filters_passed['multitimeframe'] = False
                        filter_reasons.append("? Multi-timeframe check skipped (index conversion error)")
                else:
                    # Index is already DatetimeIndex, proceed with resampling
                    weekly_data = data.resample('W').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                    
                    if len(weekly_data) >= 20:
                        # Calculate weekly EMA20
                        weekly_ema20 = weekly_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                        weekly_close = weekly_data['Close'].iloc[-1]
                        
                        if breakout['breakout_type'] == 'BULLISH':
                            # For BULLISH, weekly price should be above weekly EMA
                            if weekly_close > weekly_ema20:
                                filters_passed['multitimeframe'] = True
                                filter_reasons.append(f"? Weekly uptrend (close {weekly_close:.2f} > EMA {weekly_ema20:.2f})")
                            else:
                                filters_passed['multitimeframe'] = False
                                filter_reasons.append(f"? Weekly downtrend (close {weekly_close:.2f} < EMA {weekly_ema20:.2f})")
                        elif breakout['breakout_type'] == 'BEARISH':
                            # For BEARISH, weekly price should be below weekly EMA
                            if weekly_close < weekly_ema20:
                                filters_passed['multitimeframe'] = True
                                filter_reasons.append(f"? Weekly downtrend (close {weekly_close:.2f} < EMA {weekly_ema20:.2f})")
                            else:
                                filters_passed['multitimeframe'] = False
                                filter_reasons.append(f"? Weekly uptrend (close {weekly_close:.2f} > EMA {weekly_ema20:.2f})")
                    else:
                        logger.warning("Insufficient weekly data for multi-timeframe analysis")
                        filters_passed['multitimeframe'] = False
                        filter_reasons.append("? Multi-timeframe check skipped (insufficient weekly data)")
            except Exception as e:
                logger.error(f"Multi-timeframe analysis error: {e}")
                filters_passed['multitimeframe'] = False
                filter_reasons.append("? Multi-timeframe check skipped (analysis error)")
        
        # Step 5: Calculate entry, stop, target
        trade_params = calculate_entry_stop_target(data, breakout, consolidation, atr)
        
        # Step 6: Calculate confidence (with filters)
        confidence = calculate_confidence(
            breakout, 
            volume_check, 
            consolidation, 
            trade_params['risk_reward_ratio'],
            filters_passed
        )
        
        # Step 7: Generate signal
        signal = 'BUY' if breakout['breakout_type'] == 'BULLISH' else 'SELL'
        
        # Step 8: Build reason string (with filters)
        volume_status = "? Volume confirmed" if volume_check['is_confirmed'] else "? Low volume"
        
        reason_parts = [
            f"{breakout['breakout_type'].capitalize()} breakout at {breakout['breakout_level']:.2f} (close: {breakout['close_price']:.2f})",
            f"Range: {consolidation['height']:.2f} ({consolidation['height_pct']*100:.1f}%)",
            f"{volume_status} (ratio: {volume_check['volume_ratio']:.2f})",
            f"R:R = {trade_params['risk_reward_ratio']:.2f}"
        ]
        
        # Add filter results to reason
        if filter_reasons:
            reason_parts.extend(filter_reasons)
        
        reason = ". ".join(reason_parts)
        
        return {
            'signal': signal,
            'entry_price': trade_params['entry_price'],
            'stop_loss': trade_params['stop_loss'],
            'target': trade_params['target'],
            'confidence': confidence,
            'reason': reason,
            'strategy_name': 'Breakout Strategy'
        }
        
    except Exception as e:
        logger.error(f"Breakout strategy analysis error: {e}")
        return {
            'signal': 'NEUTRAL',
            'entry_price': None,
            'stop_loss': None,
            'target': None,
            'confidence': 0.0,
            'reason': f'Error: {str(e)}',
            'strategy_name': 'Breakout Strategy'
        }
