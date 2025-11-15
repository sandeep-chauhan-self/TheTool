"""
Risk Manager Module
Manages position sizing and risk calculations

Based on NSE Stock Screener's risk management framework
- 2% maximum risk per trade
- Minimum 1.5:1 risk-reward ratio
- Position sizing based on stop loss
"""

import logging

logger = logging.getLogger('trading_analyzer')


class RiskManager:
    """Manages position sizing and risk validation for trades"""
    
    # Default capital for position sizing
    DEFAULT_CAPITAL = 100000  # ?1 lakh
    
    # Maximum risk per trade (2%)
    MAX_RISK_PCT = 0.02
    
    # Minimum risk-reward ratio
    MIN_RR_RATIO = 1.5
    
    # Ideal risk-reward ratio
    IDEAL_RR_RATIO = 2.5
    
    # Maximum position size as % of capital
    MAX_POSITION_PCT = 0.20  # 20% max in single stock
    
    @staticmethod
    def calculate_position_size(entry, stop, capital=None):
        """
        Calculate number of shares to buy based on risk management
        
        Formula: Position Size = (Capital * Risk%) / (Entry - Stop)
        
        Args:
            entry: Entry price per share
            stop: Stop loss price per share
            capital: Total capital available (default: 100000)
        
        Returns:
            shares: Number of shares to buy
        """
        if capital is None:
            capital = RiskManager.DEFAULT_CAPITAL
        
        if not all([entry, stop, capital]) or any(x <= 0 for x in [entry, stop, capital]):
            return 0
        
        if stop >= entry:
            logger.warning("Stop loss must be below entry for BUY signal")
            return 0
        
        # Calculate risk amount (2% of capital)
        risk_amount = capital * RiskManager.MAX_RISK_PCT
        
        # Calculate risk per share
        risk_per_share = entry - stop
        
        # Calculate shares
        shares = int(risk_amount / risk_per_share)
        
        # Check max position size constraint
        position_value = shares * entry
        if position_value > capital * RiskManager.MAX_POSITION_PCT:
            # Adjust shares to meet max position constraint
            max_shares = int((capital * RiskManager.MAX_POSITION_PCT) / entry)
            shares = min(shares, max_shares)
            logger.debug(f"Position size limited by max position constraint: {shares} shares")
        
        return max(shares, 0)
    
    @staticmethod
    def calculate_position_metrics(entry, stop, target, capital=None):
        """
        Calculate comprehensive position metrics
        
        Args:
            entry: Entry price
            stop: Stop loss price
            target: Target price
            capital: Available capital
        
        Returns:
            dict with all position metrics
        """
        if capital is None:
            capital = RiskManager.DEFAULT_CAPITAL
        
        shares = RiskManager.calculate_position_size(entry, stop, capital)
        
        if shares == 0:
            return {
                'shares': 0,
                'position_value': 0,
                'risk_amount': 0,
                'reward_amount': 0,
                'rr_ratio': 0,
                'risk_pct': 0,
                'reward_pct': 0,
                'max_loss': 0,
                'max_profit': 0,
                'position_pct': 0
            }
        
        # Calculate values
        position_value = shares * entry
        risk_per_share = entry - stop
        reward_per_share = target - entry
        
        risk_amount = shares * risk_per_share
        reward_amount = shares * reward_per_share
        
        rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        risk_pct = (risk_amount / capital) * 100
        reward_pct = (reward_amount / capital) * 100
        
        position_pct = (position_value / capital) * 100
        
        return {
            'shares': shares,
            'position_value': round(position_value, 2),
            'risk_amount': round(risk_amount, 2),
            'reward_amount': round(reward_amount, 2),
            'rr_ratio': round(rr_ratio, 2),
            'risk_pct': round(risk_pct, 2),
            'reward_pct': round(reward_pct, 2),
            'max_loss': round(risk_amount, 2),
            'max_profit': round(reward_amount, 2),
            'position_pct': round(position_pct, 2)
        }
    
    @staticmethod
    def validate_trade_risk(entry, stop, target, signal='BUY'):
        """
        Validate if trade meets risk management criteria
        
        Args:
            entry: Entry price
            stop: Stop loss price
            target: Target price
            signal: Trade signal
        
        Returns:
            (is_valid: bool, errors: list, metrics: dict)
        """
        errors = []
        
        if not all([entry, stop, target]) or any(x <= 0 for x in [entry, stop, target]):
            errors.append("Missing or invalid prices")
            return False, errors, {}
        
        if signal == 'BUY':
            # BUY signal validations
            if stop >= entry:
                errors.append(f"Stop ({stop:.2f}) must be below entry ({entry:.2f})")
            
            if target <= entry:
                errors.append(f"Target ({target:.2f}) must be above entry ({entry:.2f})")
            
            if stop < entry and target > entry:
                risk = entry - stop
                reward = target - entry
                rr_ratio = reward / risk
                
                if rr_ratio < RiskManager.MIN_RR_RATIO:
                    errors.append(f"R:R ratio {rr_ratio:.2f} below minimum {RiskManager.MIN_RR_RATIO}")
                
                # Calculate stop loss percentage
                stop_pct = (risk / entry) * 100
                if stop_pct < 2:
                    errors.append(f"Stop loss too tight ({stop_pct:.1f}%) - risk of premature stop")
                
                if stop_pct > 15:
                    errors.append(f"Stop loss too wide ({stop_pct:.1f}%) - excessive risk")
        
        is_valid = len(errors) == 0
        
        # Calculate metrics even if invalid (for analysis)
        metrics = RiskManager.calculate_position_metrics(entry, stop, target)
        
        return is_valid, errors, metrics
    
    @staticmethod
    def get_recommended_capital_allocation(num_positions):
        """
        Get recommended capital allocation per position
        
        Args:
            num_positions: Number of open positions planned
        
        Returns:
            pct_per_position: Recommended % per position
        """
        if num_positions <= 0:
            return 0
        
        # Never allocate more than 100% total
        # Leave some buffer (80% max total allocation)
        max_total_allocation = 0.80
        
        pct_per_position = min(
            max_total_allocation / num_positions,
            RiskManager.MAX_POSITION_PCT
        )
        
        return pct_per_position
    
    @staticmethod
    def calculate_portfolio_risk(positions, capital=None):
        """
        Calculate total portfolio risk
        
        Args:
            positions: list of dicts with 'entry', 'stop', 'shares'
            capital: Total capital
        
        Returns:
            dict with portfolio risk metrics
        """
        if capital is None:
            capital = RiskManager.DEFAULT_CAPITAL
        
        if not positions:
            return {
                'total_risk_amount': 0,
                'total_risk_pct': 0,
                'position_count': 0,
                'avg_risk_per_position': 0,
                'max_drawdown_pct': 0
            }
        
        total_risk = 0
        
        for pos in positions:
            entry = pos.get('entry', 0)
            stop = pos.get('stop', 0)
            shares = pos.get('shares', 0)
            
            if all([entry, stop, shares]) and entry > stop:
                risk_per_share = entry - stop
                position_risk = shares * risk_per_share
                total_risk += position_risk
        
        total_risk_pct = (total_risk / capital) * 100
        avg_risk = total_risk / len(positions) if positions else 0
        
        return {
            'total_risk_amount': round(total_risk, 2),
            'total_risk_pct': round(total_risk_pct, 2),
            'position_count': len(positions),
            'avg_risk_per_position': round(avg_risk, 2),
            'max_drawdown_pct': round(total_risk_pct, 2)  # If all stops hit
        }
    
    @staticmethod
    def adjust_for_risk(entry, stop, target, capital=None):
        """
        Adjust prices to meet risk management criteria
        
        If R:R ratio too low, adjusts target upward
        If stop too wide, suggests tighter stop
        
        Args:
            entry: Entry price
            stop: Stop loss price
            target: Target price
            capital: Available capital
        
        Returns:
            (adjusted_entry, adjusted_stop, adjusted_target, adjustments_made)
        """
        adjusted = {
            'entry': entry,
            'stop': stop,
            'target': target
        }
        adjustments = []
        
        if not all([entry, stop, target]) or any(x <= 0 for x in [entry, stop, target]):
            return adjusted['entry'], adjusted['stop'], adjusted['target'], adjustments
        
        # Adjustment 1: Ensure stop < entry
        if stop >= entry:
            adjusted['stop'] = entry * 0.95  # 5% below entry
            adjustments.append(f"Adjusted stop from {stop:.2f} to {adjusted['stop']:.2f}")
        
        # Adjustment 2: Ensure target > entry
        if target <= entry:
            adjusted['target'] = entry * 1.10  # 10% above entry
            adjustments.append(f"Adjusted target from {target:.2f} to {adjusted['target']:.2f}")
        
        # Adjustment 3: Ensure minimum R:R ratio
        risk = adjusted['entry'] - adjusted['stop']
        reward = adjusted['target'] - adjusted['entry']
        rr_ratio = reward / risk if risk > 0 else 0
        
        if rr_ratio < RiskManager.MIN_RR_RATIO:
            # Adjust target to meet minimum R:R
            new_target = adjusted['entry'] + (risk * RiskManager.MIN_RR_RATIO)
            adjustments.append(f"Adjusted target from {adjusted['target']:.2f} to {new_target:.2f} to meet min R:R {RiskManager.MIN_RR_RATIO}")
            adjusted['target'] = new_target
        
        # Adjustment 4: Warn if stop too wide
        stop_pct = (risk / adjusted['entry']) * 100
        if stop_pct > 12:
            suggested_stop = adjusted['entry'] * 0.92  # 8% stop
            adjustments.append(f"Warning: Stop loss is {stop_pct:.1f}% (wide). Consider tighter stop: {suggested_stop:.2f}")
        
        return adjusted['entry'], adjusted['stop'], adjusted['target'], adjustments


# Convenience functions
def calculate_shares(entry, stop, capital=None):
    """Calculate shares to buy"""
    return RiskManager.calculate_position_size(entry, stop, capital)

def validate_risk(entry, stop, target):
    """Quick risk validation"""
    is_valid, errors, _ = RiskManager.validate_trade_risk(entry, stop, target)
    return is_valid, errors
