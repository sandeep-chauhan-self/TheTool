"""
Strategic Entry Calculator
Calculates optimal entry points instead of always using current price

Based on NSE Stock Screener's hybrid entry system
Target: ?30% of entries should equal current price
"""

import pandas as pd
import logging

logger = logging.getLogger('trading_analyzer')


class EntryCalculator:
    """Calculate strategic entry points using technical analysis"""
    
    @staticmethod
    def calculate_strategic_entry(df, current_price, signal, indicators=None):
        """
        Calculate strategic entry point using multiple methods
        
        Priority:
        1. Technical Level Entry (support/resistance)
        2. Moving Average Entry (pullback to MAs)
        3. Breakout Entry (above resistance)
        4. Current Price (fallback)
        
        Args:
            df: DataFrame with OHLCV data
            current_price: Current market price
            signal: Trade signal (BUY/HOLD/SELL)
            indicators: dict with calculated indicators (optional)
        
        Returns:
            (entry_price, method_used, confidence)
        """
        if signal != "BUY":
            return current_price, "CURRENT_PRICE", "N/A"
        
        if df is None or df.empty or len(df) < 50:
            return current_price, "CURRENT_PRICE", "LOW"
        
        try:
            # Method 1: Technical Level Entry
            tech_entry = EntryCalculator._technical_level_entry(df, current_price)
            if tech_entry:
                entry, reason = tech_entry
                # Ensure entry is within reasonable range (�15%)
                if 0.85 * current_price <= entry <= 1.15 * current_price:
                    return entry, f"TECHNICAL_LEVEL: {reason}", "HIGH"
            
            # Method 2: Moving Average Entry
            ma_entry = EntryCalculator._moving_average_entry(df, current_price)
            if ma_entry:
                entry, reason = ma_entry
                if 0.85 * current_price <= entry <= 1.15 * current_price:
                    return entry, f"MOVING_AVERAGE: {reason}", "MEDIUM"
            
            # Method 3: ATR-based Entry (if indicators provided)
            if indicators and 'atr' in indicators:
                atr_entry = EntryCalculator._atr_based_entry(current_price, indicators['atr'])
                if atr_entry:
                    entry, reason = atr_entry
                    if 0.90 * current_price <= entry <= 1.10 * current_price:
                        return entry, f"ATR_BASED: {reason}", "MEDIUM"
            
            # Method 4: Volatility-adjusted Entry
            vol_entry = EntryCalculator._volatility_entry(df, current_price)
            if vol_entry:
                entry, reason = vol_entry
                if 0.90 * current_price <= entry <= 1.05 * current_price:
                    return entry, f"VOLATILITY_ADJUSTED: {reason}", "LOW"
            
        except Exception as e:
            logger.warning(f"Error calculating strategic entry: {e}")
        
        # Fallback: Current Price
        return current_price, "CURRENT_PRICE", "LOW"
    
    @staticmethod
    def _technical_level_entry(df, current_price):
        """
        Calculate entry based on support/resistance levels
        
        Returns: (entry_price, reason) or None
        """
        try:
            # Calculate support and resistance levels
            support_20 = df['Low'].rolling(window=20).min().iloc[-1]
            support_50 = df['Low'].rolling(window=50).min().iloc[-1]
            resistance_20 = df['High'].rolling(window=20).max().iloc[-1]
            
            # Recent high/low (5 days)
            recent_high = df['High'].tail(5).max()
            recent_low = df['Low'].tail(5).min()
            
            # Strategy 1: If price near resistance, wait for breakout
            if current_price >= resistance_20 * 0.98:
                # Enter on breakout confirmation (1% above resistance)
                entry = resistance_20 * 1.01
                return entry, "Breakout above resistance"
            
            # Strategy 2: If price well above support, enter on pullback
            if current_price > support_20 * 1.05:
                # Enter at support level plus small buffer
                entry = support_20 * 1.02
                if entry < current_price:  # Only if it's a better entry
                    return entry, "Pullback to support"
            
            # Strategy 3: If consolidating, enter at bottom of range
            range_size = recent_high - recent_low
            if range_size / current_price < 0.05:  # Tight range (<5%)
                entry = recent_low * 1.01
                if entry <= current_price:
                    return entry, "Bottom of consolidation range"
            
            # Strategy 4: Enter between support and current (safer)
            # Only if price is meaningfully above support and market is not too tight
            range_size = recent_high - recent_low
            price_gap = current_price - support_50
            gap_percentage = price_gap / current_price
            consolidation_ratio = range_size / current_price
            
            # Require at least 2-3% gap above support and at least 5% range (not tight consolidation)
            if gap_percentage >= 0.025 and consolidation_ratio >= 0.05:
                entry = (support_50 + current_price) / 2
                return entry, "Mid-point between support and current"
            
            return None
            
        except Exception as e:
            logger.debug(f"Technical level entry calculation failed: {e}")
            return None
    
    @staticmethod
    def _moving_average_entry(df, current_price):
        """
        Calculate entry based on moving average levels
        
        Returns: (entry_price, reason) or None
        """
        try:
            # Calculate moving averages
            sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
            
            # Check trend direction
            if sma_20 > sma_50:
                # Uptrend: Enter on pullback to SMA20
                if current_price > sma_20:
                    entry = sma_20 * 1.005  # Slightly above SMA20
                    if entry < current_price:
                        return entry, "Pullback to SMA20 in uptrend"
                
                # If price below SMA20, enter at current (opportunity)
                elif current_price < sma_20 * 0.98:
                    return current_price, "Below SMA20 - opportunity"
            
            # Golden cross setup
            if sma_20 > sma_50 * 1.01:  # Clear uptrend
                if current_price > sma_50:
                    entry = sma_50 * 1.01
                    if entry < current_price:
                        return entry, "Golden cross - enter above SMA50"
            
            return None
            
        except Exception as e:
            logger.debug(f"Moving average entry calculation failed: {e}")
            return None
    
    @staticmethod
    def _atr_based_entry(current_price, atr):
        """
        Calculate entry based on ATR (Average True Range)
        
        Returns: (entry_price, reason) or None
        """
        try:
            if atr <= 0:
                return None
            
            # Enter at current price minus half ATR (wait for small dip)
            entry = current_price - (atr * 0.5)
            
            # Ensure entry is reasonable
            if entry > 0 and entry < current_price:
                return entry, "ATR-based pullback entry"
            
            return None
            
        except Exception as e:
            logger.debug(f"ATR entry calculation failed: {e}")
            return None
    
    @staticmethod
    def _volatility_entry(df, current_price):
        """
        Calculate entry based on recent volatility
        
        Returns: (entry_price, reason) or None
        """
        try:
            # Calculate recent volatility (standard deviation of returns)
            returns = df['Close'].pct_change().tail(20)
            volatility = returns.std()
            
            if volatility <= 0:
                return None
            
            # For low volatility, enter near current price
            if volatility < 0.02:  # <2% daily volatility
                entry = current_price * 0.995  # Just 0.5% below
                return entry, "Low volatility - minimal discount"
            
            # For medium volatility, wait for small pullback
            elif volatility < 0.04:  # 2-4% daily volatility
                entry = current_price * 0.98  # 2% below
                return entry, "Medium volatility - 2% pullback"
            
            # For high volatility, wait for larger pullback
            else:  # >4% daily volatility
                entry = current_price * 0.95  # 5% below
                return entry, "High volatility - 5% pullback"
            
        except Exception as e:
            logger.debug(f"Volatility entry calculation failed: {e}")
            return None
    
    @staticmethod
    def calculate_entry_with_reason(df, current_price, signal, indicators=None):
        """
        Extended function that returns detailed reasoning
        
        Returns:
            dict with entry_price, method, confidence, reason, analysis
        """
        entry, method, confidence = EntryCalculator.calculate_strategic_entry(
            df, current_price, signal, indicators
        )
        
        # Determine if this is strategic or fallback
        is_strategic = method != "CURRENT_PRICE"
        discount_pct = ((current_price - entry) / current_price * 100) if entry < current_price else 0
        
        return {
            'entry_price': entry,
            'method': method,
            'confidence': confidence,
            'is_strategic': is_strategic,
            'discount_pct': discount_pct,
            'reason': f"Entry at {entry:.2f} ({method}) - {confidence} confidence"
        }


# Convenience function
def calculate_entry(df, current_price, signal):
    """Simple function to get entry price"""
    entry, _, _ = EntryCalculator.calculate_strategic_entry(df, current_price, signal)
    return entry
