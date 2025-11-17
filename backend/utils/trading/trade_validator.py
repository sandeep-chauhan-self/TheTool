"""
Trade Validator Module
Validates analysis results before sending to frontend

Based on NSE Stock Screener's mandatory validation framework
Ensures 100% of BUY signals have valid entry/stop/target with proper R:R ratios
"""

import logging

logger = logging.getLogger('trading_analyzer')


class TradeValidator:
    """Validates trade recommendations for mathematical consistency"""
    
    # Minimum acceptable risk-reward ratio
    MIN_RR_RATIO = 1.5
    
    # Ideal risk-reward ratio
    IDEAL_RR_RATIO = 2.5
    
    # Maximum allowed deviation from current price (20%)
    MAX_PRICE_DEVIATION = 0.20
    
    @staticmethod
    def validate_analysis_result(result):
        """
        Validate a single stock analysis result
        
        Args:
            result: dict with analysis results
        
        Returns:
            (is_valid: bool, errors: list, warnings: list)
        """
        errors = []
        warnings = []
        
        signal = result.get('signal', '')
        ticker = result.get('ticker', 'Unknown')
        
        # For BUY signals, enforce strict validation
        if signal == 'BUY':
            entry = result.get('entry_price')
            stop = result.get('stop_loss')
            target = result.get('target_price')
            current = result.get('current_price')
            
            # Validation 1: All prices must exist and be positive
            if entry is None or entry <= 0:
                errors.append(f"{ticker}: Missing or invalid entry price")
            
            if stop is None or stop <= 0:
                errors.append(f"{ticker}: Missing or invalid stop loss")
            
            if target is None or target <= 0:
                errors.append(f"{ticker}: Missing or invalid target price")
            
            if current is None or current <= 0:
                errors.append(f"{ticker}: Missing or invalid current price")
            
            # If basic validation passed, do mathematical validation
            if entry and stop and target and current and all(p > 0 for p in [entry, stop, target, current]):
                
                # Validation 2: Stop loss must be below entry for BUY
                if stop >= entry:
                    errors.append(f"{ticker}: Stop loss ({stop:.2f}) must be below entry ({entry:.2f})")
                
                # Validation 3: Target must be above entry for BUY
                if target <= entry:
                    errors.append(f"{ticker}: Target ({target:.2f}) must be above entry ({entry:.2f})")
                
                # Validation 4: Risk-reward ratio validation
                if stop < entry and target > entry:
                    risk = entry - stop
                    reward = target - entry
                    rr_ratio = reward / risk if risk > 0 else 0
                    
                    if rr_ratio < TradeValidator.MIN_RR_RATIO:
                        errors.append(f"{ticker}: R:R ratio {rr_ratio:.2f} too low (minimum {TradeValidator.MIN_RR_RATIO})")
                    elif rr_ratio < TradeValidator.IDEAL_RR_RATIO:
                        warnings.append(f"{ticker}: R:R ratio {rr_ratio:.2f} below ideal {TradeValidator.IDEAL_RR_RATIO}")
                
                # Validation 5: Entry price within reasonable range of current price
                if entry > 0 and current > 0:
                    entry_deviation = abs(entry - current) / current
                    if entry_deviation > TradeValidator.MAX_PRICE_DEVIATION:
                        warnings.append(f"{ticker}: Entry price deviates {entry_deviation*100:.1f}% from current (>20%)")
                
                # Validation 6: Stop loss not too tight (at least 2%)
                if stop > 0 and entry > 0:
                    stop_distance = (entry - stop) / entry
                    if stop_distance < 0.02:
                        warnings.append(f"{ticker}: Stop loss very tight ({stop_distance*100:.1f}%), risk of premature stop")
                
                # Validation 7: Stop loss not too wide (more than 15%)
                if stop > 0 and entry > 0:
                    stop_distance = (entry - stop) / entry
                    if stop_distance > 0.15:
                        warnings.append(f"{ticker}: Stop loss very wide ({stop_distance*100:.1f}%), high risk per trade")
        
        # For SELL signals
        elif signal == 'SELL':
            # SELL signals should not have entry/stop/target in our system
            # But if they do, validate them inversely
            entry = result.get('entry_price')
            stop = result.get('stop_loss')
            target = result.get('target_price')
            
            if entry and stop and target:
                if stop <= entry:
                    errors.append(f"{ticker}: SELL - Stop loss ({stop:.2f}) must be above entry ({entry:.2f})")
                
                if target >= entry:
                    errors.append(f"{ticker}: SELL - Target ({target:.2f}) must be below entry ({entry:.2f})")
        
        # Validate score
        score = result.get('score')
        if score is None:
            errors.append(f"{ticker}: Missing score")
        elif not (0 <= score <= 100):
            errors.append(f"{ticker}: Invalid score: {score} (must be 0-100)")
        
        # Validate signal value
        valid_signals = ['BUY', 'HOLD', 'SELL', 'AVOID']
        if signal not in valid_signals:
            errors.append(f"{ticker}: Invalid signal '{signal}' (must be one of {valid_signals})")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.debug(f"Trade validation passed for {ticker}: {signal} @ {result.get('entry_price')}")
        else:
            logger.warning(f"Trade validation failed for {ticker}: {', '.join(errors)}")
        
        return is_valid, errors, warnings
    
    @staticmethod
    def validate_batch_results(results):
        """
        Validate entire batch of analysis results
        
        Args:
            results: list of analysis result dicts
        
        Returns:
            dict with validation summary
        """
        if not results:
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'success_rate': 0,
                'invalid_details': [],
                'all_warnings': []
            }
        
        total = len(results)
        valid = 0
        invalid_details = []
        all_warnings = []
        
        for result in results:
            is_valid, errors, warnings = TradeValidator.validate_analysis_result(result)
            
            if is_valid:
                valid += 1
            else:
                invalid_details.append({
                    'ticker': result.get('ticker'),
                    'signal': result.get('signal'),
                    'errors': errors
                })
            
            if warnings:
                all_warnings.extend(warnings)
        
        success_rate = (valid / total * 100) if total > 0 else 0
        
        logger.info(f"Batch validation: {valid}/{total} valid ({success_rate:.1f}%), {len(all_warnings)} warnings")
        
        return {
            'total': total,
            'valid': valid,
            'invalid': total - valid,
            'success_rate': success_rate,
            'invalid_details': invalid_details,
            'all_warnings': all_warnings,
            'summary': f"{valid}/{total} valid ({success_rate:.1f}%)"
        }
    
    @staticmethod
    def calculate_risk_reward_ratio(entry, stop, target, signal='BUY'):
        """
        Calculate risk-reward ratio
        
        Args:
            entry: Entry price
            stop: Stop loss price
            target: Target price
            signal: Trade signal (BUY/SELL)
        
        Returns:
            rr_ratio: float or None if invalid
        """
        if not all([entry, stop, target]) or any(p <= 0 for p in [entry, stop, target]):
            return None
        
        if signal == 'BUY':
            if stop >= entry or target <= entry:
                return None
            
            risk = entry - stop
            reward = target - entry
        else:  # SELL
            if stop <= entry or target >= entry:
                return None
            
            risk = stop - entry
            reward = entry - target
        
        rr_ratio = reward / risk if risk > 0 else None
        return rr_ratio
    
    @staticmethod
    def validate_and_fix(result):
        """
        Attempt to fix common validation errors
        
        Args:
            result: dict with analysis results
        
        Returns:
            (fixed_result: dict, was_fixed: bool, fixes_applied: list)
        """
        fixed_result = result.copy()
        fixes_applied = []
        
        signal = fixed_result.get('signal', '')
        entry = fixed_result.get('entry_price')
        stop = fixed_result.get('stop_loss')
        target = fixed_result.get('target_price')
        current = fixed_result.get('current_price')
        
        if signal == 'BUY' and all([entry, stop, target, current]) and all(p > 0 for p in [entry, stop, target, current]):
            
            # Fix 1: If stop >= entry, set stop to entry - 5%
            if stop >= entry:
                fixed_result['stop_loss'] = entry * 0.95
                fixes_applied.append(f"Adjusted stop loss from {stop:.2f} to {fixed_result['stop_loss']:.2f}")
            
            # Fix 2: If target <= entry, set target to entry + 10%
            if target <= entry:
                fixed_result['target_price'] = entry * 1.10
                fixes_applied.append(f"Adjusted target from {target:.2f} to {fixed_result['target_price']:.2f}")
            
            # Fix 3: If R:R ratio too low, adjust target
            stop_val = fixed_result['stop_loss']
            target_val = fixed_result['target_price']
            
            if stop_val < entry and target_val > entry:
                risk = entry - stop_val
                reward = target_val - entry
                rr_ratio = reward / risk
                
                if rr_ratio < TradeValidator.MIN_RR_RATIO:
                    # Adjust target to meet minimum R:R
                    new_target = entry + (risk * TradeValidator.MIN_RR_RATIO)
                    fixed_result['target_price'] = new_target
                    fixes_applied.append(f"Adjusted target to meet min R:R ratio {TradeValidator.MIN_RR_RATIO}: {new_target:.2f}")
        
        was_fixed = len(fixes_applied) > 0
        
        if was_fixed:
            logger.info(f"Fixed {result.get('ticker')}: {', '.join(fixes_applied)}")
        
        return fixed_result, was_fixed, fixes_applied


# Convenience function
def validate_trade(result):
    """Quick validation function"""
    is_valid, errors, warnings = TradeValidator.validate_analysis_result(result)
    return is_valid, errors
