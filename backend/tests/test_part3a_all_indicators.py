"""
Part 3A MLRM - Comprehensive Validation Test for All 13 Indicators

Tests that all indicators have:
1. Named constants (MLRM-001)
2. Boundary validation (MLRM-002)
3. NaN/Inf handling
4. Type checking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import all indicators using new Part 3C structure
from indicators.momentum.rsi import RSIIndicator
from indicators.trend.macd import MACDIndicator
from indicators.volatility.bollinger import BollingerIndicator
from indicators.volatility.atr import ATRIndicator
from indicators.volume.obv import OBVIndicator
from indicators.volume.cmf import CMFIndicator
from indicators.momentum.cci import CCIIndicator
from indicators.momentum.williams import WilliamsIndicator
from indicators.trend.ema import EMAIndicator
from indicators.momentum.stochastic import StochasticIndicator
from indicators.trend.supertrend import SupertrendIndicator
from indicators.trend.adx import ADXIndicator
from indicators.trend.psar import PSARIndicator


def create_test_data(rows=100):
    """Create sample OHLCV data"""
    dates = [datetime.now() - timedelta(days=i) for i in range(rows)]
    dates.reverse()
    
    data = {
        'Date': dates,
        'Open': np.random.uniform(100, 110, rows),
        'High': np.random.uniform(110, 120, rows),
        'Low': np.random.uniform(90, 100, rows),
        'Close': np.random.uniform(95, 115, rows),
        'Volume': np.random.uniform(1000000, 5000000, rows)
    }
    
    return pd.DataFrame(data)


class TestPart3AValidation:
    """Test Part 3A improvements across all indicators"""
    
    def test_rsi_empty_dataframe(self):
        """RSI should reject empty DataFrame"""
        indicator = RSIIndicator()
        try:
            indicator.calculate(pd.DataFrame())
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "DataFrame cannot be empty" in str(e)
    
    def test_macd_invalid_period(self):
        """MACD should reject invalid periods"""
        indicator = MACDIndicator()
        df = create_test_data()
        try:
            indicator.calculate(df, fast=26, slow=12)  # Fast > slow
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Fast period" in str(e) and "must be less than slow period" in str(e)
    
    def test_bollinger_missing_column(self):
        """Bollinger should reject DataFrame without Close column"""
        indicator = BollingerIndicator()
        df = pd.DataFrame({'Open': [100, 101, 102]})
        try:
            indicator.calculate(df)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "must contain" in str(e) and "Close" in str(e)
    
    def test_atr_insufficient_data(self):
        """ATR should reject insufficient data"""
        indicator = ATRIndicator()
        df = create_test_data(rows=5)
        try:
            indicator.calculate(df, period=14)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Insufficient data" in str(e)
    
    def test_obv_type_error(self):
        """OBV should require proper DataFrame"""
        indicator = OBVIndicator()
        try:
            indicator.calculate(None)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "DataFrame cannot be None" in str(e)
    
    def test_cmf_valid_calculation(self):
        """CMF should calculate successfully with valid data"""
        indicator = CMFIndicator()
        df = create_test_data(rows=50)
        result = indicator.calculate(df, period=20)
        assert isinstance(result, float)
        assert not np.isnan(result)
        assert not np.isinf(result)
    
    def test_cci_period_range(self):
        """CCI should enforce period range"""
        indicator = CCIIndicator()
        df = create_test_data()
        try:
            indicator.calculate(df, period=1)
            raise AssertionError("Should have raised ValueError for period < 2")
        except ValueError as e:
            assert "Period must be >= 2" in str(e)
        
        try:
            indicator.calculate(df, period=300)
            raise AssertionError("Should have raised ValueError for period > 200")
        except ValueError as e:
            assert "Period must be <= 200" in str(e)
    
    def test_williams_valid_calculation(self):
        """Williams %R should calculate successfully"""
        indicator = WilliamsIndicator()
        df = create_test_data(rows=50)
        result = indicator.calculate(df, period=14)
        assert isinstance(result, float)
        assert -100 <= result <= 0  # Williams %R range
    
    def test_ema_fast_slow_validation(self):
        """EMA should validate fast < slow"""
        indicator = EMAIndicator()
        df = create_test_data(rows=300)
        try:
            indicator.calculate(df, fast=200, slow=50)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Fast period" in str(e) and "must be less than slow period" in str(e)
    
    def test_stochastic_valid_calculation(self):
        """Stochastic should calculate K and D successfully"""
        indicator = StochasticIndicator()
        df = create_test_data(rows=50)
        result = indicator.calculate(df, k_period=14, d_period=3, smooth=3)
        assert isinstance(result, dict)
        assert 'k' in result and 'd' in result
        assert 0 <= result['k'] <= 100
        assert 0 <= result['d'] <= 100
    
    def test_supertrend_multiplier_range(self):
        """Supertrend should enforce multiplier range"""
        indicator = SupertrendIndicator()
        df = create_test_data(rows=50)
        try:
            result = indicator.calculate(df, period=10, multiplier=0.1)
            # If no exception, check if it returned an error dict
            if isinstance(result, dict):
                if 'signal_desc' in result and 'error' in result['signal_desc'].lower():
                    assert "Multiplier must be >= 0.5" in result['signal_desc']
                    return  # Test passed - error detected
            raise AssertionError("Should have raised ValueError or returned error dict")
        except ValueError as e:
            assert "Multiplier must be >= 0.5" in str(e)
    
    def test_adx_valid_calculation(self):
        """ADX should calculate ADX, DI+, DI- successfully"""
        indicator = ADXIndicator()
        df = create_test_data(rows=50)
        result = indicator.calculate(df, period=14)
        assert isinstance(result, dict)
        assert 'adx' in result
        assert 'di_plus' in result
        assert 'di_minus' in result
        assert not np.isnan(result['adx'])
        assert not np.isinf(result['adx'])
    
    def test_psar_af_validation(self):
        """PSAR should validate acceleration factor parameters"""
        indicator = PSARIndicator()
        df = create_test_data()
        try:
            indicator.calculate(df, af_start=0.05, af_max=0.02)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "AF max" in str(e) and "must be >= AF start" in str(e)
    
    def test_all_indicators_constants_exist(self):
        """Verify all indicators have defined constants"""
        # Import constants from each module
        from indicators import rsi, macd, bollinger, atr, obv, cmf
        from indicators import cci, williams, ema, stochastic, supertrend, adx, psar
        
        # Check RSI constants
        assert hasattr(rsi, 'RSI_DEFAULT_PERIOD')
        assert hasattr(rsi, 'RSI_OVERSOLD_THRESHOLD')
        assert hasattr(rsi, 'VOTE_BUY')
        
        # Check MACD constants
        assert hasattr(macd, 'MACD_FAST_PERIOD')
        assert hasattr(macd, 'MACD_SLOW_PERIOD')
        
        # Check Bollinger constants
        assert hasattr(bollinger, 'BB_DEFAULT_PERIOD')
        assert hasattr(bollinger, 'BB_DEFAULT_STD_DEV')
        
        # Check ATR constants
        assert hasattr(atr, 'ATR_DEFAULT_PERIOD')
        
        # Check OBV constants
        assert hasattr(obv, 'VOTE_BUY')
        
        # Check CMF constants
        assert hasattr(cmf, 'CMF_DEFAULT_PERIOD')
        
        # Check CCI constants
        assert hasattr(cci, 'CCI_CONSTANT')
        assert hasattr(cci, 'CCI_OVERSOLD_THRESHOLD')
        
        # Check Williams constants
        assert hasattr(williams, 'WILLIAMS_DEFAULT_PERIOD')
        assert hasattr(williams, 'WILLIAMS_OVERSOLD_THRESHOLD')
        
        # Check EMA constants
        assert hasattr(ema, 'EMA_FAST_PERIOD')
        assert hasattr(ema, 'EMA_SLOW_PERIOD')
        
        # Check Stochastic constants
        assert hasattr(stochastic, 'STOCH_K_PERIOD')
        assert hasattr(stochastic, 'STOCH_OVERSOLD_THRESHOLD')
        
        # Check Supertrend constants
        assert hasattr(supertrend, 'ST_DEFAULT_PERIOD')
        assert hasattr(supertrend, 'ST_DEFAULT_MULTIPLIER')
        
        # Check ADX constants
        assert hasattr(adx, 'ADX_DEFAULT_PERIOD')
        assert hasattr(adx, 'ADX_STRONG_TREND_THRESHOLD')
        
        # Check PSAR constants
        assert hasattr(psar, 'PSAR_AF_START')
        assert hasattr(psar, 'PSAR_AF_MAX')
    
    def test_all_indicators_vote_confidence(self):
        """Verify all indicators can calculate vote and confidence"""
        df = create_test_data(rows=100)
        
        indicators = [
            RSIIndicator(),
            MACDIndicator(),
            BollingerIndicator(),
            ATRIndicator(),
            OBVIndicator(),
            CMFIndicator(),
            CCIIndicator(),
            WilliamsIndicator(),
            EMAIndicator(),
            StochasticIndicator(),
            SupertrendIndicator(),
            ADXIndicator(),
            PSARIndicator()
        ]
        
        for indicator in indicators:
            try:
                result = indicator.vote_and_confidence(df)
                assert isinstance(result, dict), f"{indicator.name}: Should return dict"
                assert 'vote' in result, f"{indicator.name}: Missing 'vote' key"
                assert 'confidence' in result, f"{indicator.name}: Missing 'confidence' key"
                vote = result['vote']
                confidence = result['confidence']
                assert vote in [-1, 0, 1], f"{indicator.name}: Invalid vote {vote}"
                assert 0.0 <= confidence <= 1.0, f"{indicator.name}: Invalid confidence {confidence}"
                print(f"? {indicator.name}: vote={vote}, confidence={confidence:.2f}")
            except Exception as e:
                raise AssertionError(f"{indicator.name} failed: {e}")


if __name__ == "__main__":
    # Run tests
    print("Part 3A MLRM - Comprehensive Indicator Validation")
    print("=" * 60)
    
    test = TestPart3AValidation()
    
    # Run individual tests
    tests = [
        ("RSI empty DataFrame", test.test_rsi_empty_dataframe),
        ("MACD invalid period", test.test_macd_invalid_period),
        ("Bollinger missing column", test.test_bollinger_missing_column),
        ("ATR insufficient data", test.test_atr_insufficient_data),
        ("OBV type error", test.test_obv_type_error),
        ("CMF valid calculation", test.test_cmf_valid_calculation),
        ("CCI period range", test.test_cci_period_range),
        ("Williams valid calculation", test.test_williams_valid_calculation),
        ("EMA fast/slow validation", test.test_ema_fast_slow_validation),
        ("Stochastic valid calculation", test.test_stochastic_valid_calculation),
        ("Supertrend multiplier range", test.test_supertrend_multiplier_range),
        ("ADX valid calculation", test.test_adx_valid_calculation),
        ("PSAR AF validation", test.test_psar_af_validation),
        ("All constants exist", test.test_all_indicators_constants_exist),
        ("All vote/confidence", test.test_all_indicators_vote_confidence),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"? PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"? FAIL: {name} - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
