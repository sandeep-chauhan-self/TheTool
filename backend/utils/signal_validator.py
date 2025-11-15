"""
Signal Validator Module
Detects contradictions between signals and indicators

Based on NSE Stock Screener's signal validation framework
- Prevents BUY with overbought indicators (RSI > 75)
- Checks MACD alignment with signal
- Multi-factor confidence scoring
"""

import logging

logger = logging.getLogger('trading_analyzer')


class SignalValidator:
    """Validates signals against technical indicators for contradictions"""
    
    # Threshold values
    RSI_OVERBOUGHT = 75
    RSI_OVERSOLD = 25
    RSI_NEUTRAL_LOW = 40
    RSI_NEUTRAL_HIGH = 60
    
    # Confidence levels
    CONFIDENCE_HIGH = "high"
    CONFIDENCE_MEDIUM = "medium"
    CONFIDENCE_LOW = "low"
    
    @staticmethod
    def validate_signal(signal, indicators):
        """
        Main validation - detect signal vs indicator contradictions
        
        Args:
            signal: 'BUY' or 'SELL'
            indicators: dict with RSI, MACD, trend, etc.
        
        Returns:
            (is_valid: bool, contradictions: list, confidence: str, score: int)
        """
        contradictions = []
        alignment_score = 0  # 0-100
        
        if not signal or not indicators:
            return True, [], SignalValidator.CONFIDENCE_LOW, 0
        
        # Extract indicators
        rsi = indicators.get('RSI')
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_signal')
        macd_histogram = indicators.get('MACD_histogram')
        trend = indicators.get('trend')
        
        if signal == 'BUY':
            # Check 1: RSI overbought (critical)
            if rsi is not None and rsi > SignalValidator.RSI_OVERBOUGHT:
                contradictions.append(f"CRITICAL: BUY signal with RSI overbought ({rsi:.1f})")
            elif rsi is not None and rsi > SignalValidator.RSI_NEUTRAL_HIGH:
                contradictions.append(f"WARNING: BUY signal with elevated RSI ({rsi:.1f})")
                alignment_score += 15  # Partial credit
            elif rsi is not None:
                alignment_score += 30  # Good RSI for BUY
            
            # Check 2: MACD alignment
            if macd is not None and macd_signal is not None:
                if macd < macd_signal:
                    contradictions.append(f"MACD bearish (MACD {macd:.2f} < Signal {macd_signal:.2f}) conflicts with BUY")
                else:
                    alignment_score += 25  # MACD bullish
                
                if macd_histogram is not None:
                    if macd_histogram < 0:
                        contradictions.append(f"MACD histogram negative ({macd_histogram:.2f}) conflicts with BUY")
                    else:
                        alignment_score += 15  # Histogram positive
            
            # Check 3: Trend alignment
            if trend is not None:
                if trend.lower() in ['bearish', 'downtrend']:
                    contradictions.append(f"Bearish trend conflicts with BUY signal")
                elif trend.lower() in ['bullish', 'uptrend']:
                    alignment_score += 20  # Trend aligned
                else:  # Sideways/neutral
                    alignment_score += 10  # Neutral okay for BUY
            
        elif signal == 'SELL':
            # Check 1: RSI oversold
            if rsi is not None and rsi < SignalValidator.RSI_OVERSOLD:
                contradictions.append(f"CRITICAL: SELL signal with RSI oversold ({rsi:.1f})")
            elif rsi is not None and rsi < SignalValidator.RSI_NEUTRAL_LOW:
                contradictions.append(f"WARNING: SELL signal with low RSI ({rsi:.1f})")
                alignment_score += 15
            elif rsi is not None:
                alignment_score += 30  # Good RSI for SELL
            
            # Check 2: MACD alignment
            if macd is not None and macd_signal is not None:
                if macd > macd_signal:
                    contradictions.append(f"MACD bullish (MACD {macd:.2f} > Signal {macd_signal:.2f}) conflicts with SELL")
                else:
                    alignment_score += 25  # MACD bearish
                
                if macd_histogram is not None:
                    if macd_histogram > 0:
                        contradictions.append(f"MACD histogram positive ({macd_histogram:.2f}) conflicts with SELL")
                    else:
                        alignment_score += 15  # Histogram negative
            
            # Check 3: Trend alignment
            if trend is not None:
                if trend.lower() in ['bullish', 'uptrend']:
                    contradictions.append(f"Bullish trend conflicts with SELL signal")
                elif trend.lower() in ['bearish', 'downtrend']:
                    alignment_score += 20  # Trend aligned
                else:  # Sideways/neutral
                    alignment_score += 10
        
        # Determine confidence based on score and contradictions
        has_critical = any('CRITICAL' in c for c in contradictions)
        has_warnings = any('WARNING' in c for c in contradictions)
        
        if has_critical or alignment_score < 40:
            confidence = SignalValidator.CONFIDENCE_LOW
        elif has_warnings or alignment_score < 70:
            confidence = SignalValidator.CONFIDENCE_MEDIUM
        else:
            confidence = SignalValidator.CONFIDENCE_HIGH
        
        is_valid = not has_critical
        
        return is_valid, contradictions, confidence, alignment_score
    
    @staticmethod
    def check_multi_timeframe_alignment(signals_by_timeframe):
        """
        Check if signals align across timeframes
        
        Args:
            signals_by_timeframe: dict like {'1d': 'BUY', '1wk': 'SELL'}
        
        Returns:
            (is_aligned: bool, conflicts: list)
        """
        if not signals_by_timeframe or len(signals_by_timeframe) < 2:
            return True, []
        
        signals = list(signals_by_timeframe.values())
        conflicts = []
        
        # Check if all signals agree
        unique_signals = set(s for s in signals if s in ['BUY', 'SELL'])
        
        if len(unique_signals) > 1:
            # Conflicting signals
            for tf, signal in signals_by_timeframe.items():
                conflicts.append(f"{tf}: {signal}")
            
            return False, [f"Multi-timeframe conflict: {', '.join(conflicts)}"]
        
        return True, []
    
    @staticmethod
    def validate_price_action(signal, current_price, support, resistance):
        """
        Validate signal against support/resistance levels
        
        Args:
            signal: 'BUY' or 'SELL'
            current_price: Current price
            support: Support level
            resistance: Resistance level
        
        Returns:
            (is_valid: bool, issues: list)
        """
        issues = []
        
        if not all([signal, current_price, support, resistance]):
            return True, []
        
        if current_price < support:
            issues.append(f"Price ({current_price:.2f}) below support ({support:.2f})")
        
        if current_price > resistance:
            issues.append(f"Price ({current_price:.2f}) above resistance ({resistance:.2f})")
        
        if signal == 'BUY':
            # BUY near resistance is risky
            proximity_to_resistance = ((resistance - current_price) / current_price) * 100
            if proximity_to_resistance < 2:
                issues.append(f"BUY too close to resistance ({proximity_to_resistance:.1f}% away)")
            
            # BUY far from support is risky
            proximity_to_support = ((current_price - support) / current_price) * 100
            if proximity_to_support > 10:
                issues.append(f"BUY far from support ({proximity_to_support:.1f}% away)")
        
        elif signal == 'SELL':
            # SELL near support is risky
            proximity_to_support = ((current_price - support) / current_price) * 100
            if proximity_to_support < 2:
                issues.append(f"SELL too close to support ({proximity_to_support:.1f}% away)")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def calculate_signal_confidence(indicators, weights=None):
        """
        Calculate overall signal confidence from multiple indicators
        
        Args:
            indicators: dict of indicator values
            weights: dict of indicator weights (optional)
        
        Returns:
            confidence_pct: 0-100 confidence score
        """
        if weights is None:
            weights = {
                'RSI': 0.25,
                'MACD': 0.25,
                'trend': 0.20,
                'volume': 0.15,
                'support_resistance': 0.15
            }
        
        confidence = 0
        total_weight = 0
        
        # RSI contribution
        rsi = indicators.get('RSI')
        if rsi is not None:
            # RSI in neutral zone (40-60) is good
            if SignalValidator.RSI_NEUTRAL_LOW <= rsi <= SignalValidator.RSI_NEUTRAL_HIGH:
                confidence += weights['RSI'] * 100
            elif SignalValidator.RSI_OVERSOLD < rsi < SignalValidator.RSI_OVERBOUGHT:
                confidence += weights['RSI'] * 70  # Moderate confidence
            else:
                confidence += weights['RSI'] * 30  # Low confidence in extremes
            total_weight += weights['RSI']
        
        # MACD contribution
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_signal')
        if macd is not None and macd_signal is not None:
            # Strong signal if MACD crossed above/below signal recently
            macd_diff = abs(macd - macd_signal)
            if macd_diff < 0.5:
                confidence += weights['MACD'] * 90  # Recent cross
            elif macd_diff < 1.0:
                confidence += weights['MACD'] * 70
            else:
                confidence += weights['MACD'] * 50
            total_weight += weights['MACD']
        
        # Trend contribution
        trend = indicators.get('trend')
        if trend is not None:
            if trend.lower() in ['bullish', 'uptrend', 'bearish', 'downtrend']:
                confidence += weights['trend'] * 90  # Clear trend
            else:
                confidence += weights['trend'] * 50  # Sideways
            total_weight += weights['trend']
        
        # Volume contribution
        volume_trend = indicators.get('volume_trend')
        if volume_trend is not None:
            if volume_trend.lower() in ['increasing', 'high']:
                confidence += weights['volume'] * 90
            else:
                confidence += weights['volume'] * 60
            total_weight += weights['volume']
        
        # Support/Resistance contribution
        near_support = indicators.get('near_support', False)
        near_resistance = indicators.get('near_resistance', False)
        if near_support or near_resistance:
            confidence += weights['support_resistance'] * 80
            total_weight += weights['support_resistance']
        
        # Normalize by total weight
        if total_weight > 0:
            confidence = (confidence / total_weight)
        else:
            confidence = 50  # Default if no indicators
        
        return min(max(confidence, 0), 100)  # Clamp 0-100
    
    @staticmethod
    def get_validation_summary(signal, indicators, prices):
        """
        Get comprehensive validation summary
        
        Args:
            signal: 'BUY' or 'SELL'
            indicators: dict of technical indicators
            prices: dict with entry, stop, target, support, resistance
        
        Returns:
            dict with complete validation results
        """
        # Core signal validation
        is_valid, contradictions, confidence, alignment_score = SignalValidator.validate_signal(
            signal, indicators
        )
        
        # Price action validation
        current_price = prices.get('entry')
        support = prices.get('support')
        resistance = prices.get('resistance')
        
        price_valid, price_issues = SignalValidator.validate_price_action(
            signal, current_price, support, resistance
        )
        
        # Calculate overall confidence
        confidence_score = SignalValidator.calculate_signal_confidence(indicators)
        
        # Combine all validations
        all_issues = contradictions + price_issues
        overall_valid = is_valid and price_valid
        
        return {
            'is_valid': overall_valid,
            'confidence': confidence,
            'confidence_score': round(confidence_score, 1),
            'alignment_score': alignment_score,
            'contradictions': contradictions,
            'price_issues': price_issues,
            'all_issues': all_issues,
            'recommendation': 'PROCEED' if overall_valid and confidence_score > 60 else 'REVIEW' if confidence_score > 40 else 'REJECT'
        }


# Convenience functions
def validate_buy_signal(indicators):
    """Quick BUY signal validation"""
    is_valid, contradictions, confidence, score = SignalValidator.validate_signal('BUY', indicators)
    return is_valid, contradictions

def validate_sell_signal(indicators):
    """Quick SELL signal validation"""
    is_valid, contradictions, confidence, score = SignalValidator.validate_signal('SELL', indicators)
    return is_valid, contradictions
