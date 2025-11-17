"""
Utils Package - Part 3C Module-Level Rewrite Mode (MDLRM)

Organized by domain:
- analysis/: Analysis orchestration, vote aggregation, signal validation
- data/: Data fetching, validation, source management
- trading/: Entry calculation, trade validation, risk management
- infrastructure/: Logging, scheduling, configuration

Part 3C: MODULE_REWRITE_002 - Utils Module Decomposition
"""

# ============================================================================
# NEW STRUCTURE (Part 3C) - Domain-Based Organization
# ============================================================================

# Analysis Domain
from utils.analysis.orchestrator import analyze_ticker, aggregate_votes, get_verdict, export_to_excel
from utils.analysis.signal_validator import validate_buy_signal, validate_sell_signal
from utils.analysis.vote_aggregator import aggregate_strategies, select_best_strategy

# Data Domain
from utils.data.fetcher import fetch_ticker_data
from utils.data.validator import DataValidator

# Trading Domain
from utils.trading.entry_calculator import EntryCalculator
from utils.trading.trade_validator import TradeValidator
from utils.trading.risk_manager import RiskManager

# Infrastructure
from utils.infrastructure.logging import setup_logger
from utils.infrastructure.scheduler import start_scheduler

# ============================================================================
# BACKWARD COMPATIBILITY LAYER (Legacy Imports)
# ============================================================================

# Allow old import style: from utils.compute_score import analyze_ticker
# These are kept for backward compatibility with existing code
from utils.analysis import orchestrator as compute_score
from utils.analysis import signal_validator
from utils.analysis import vote_aggregator as strategy_aggregator
from utils.data import fetcher as fetch_data_module
from utils.data import validator as data_validator
from utils.trading import entry_calculator
from utils.trading import trade_validator
from utils.trading import risk_manager
from utils.infrastructure import logging as logger
from utils.infrastructure import scheduler as cron_tasks

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Analysis functions
    'analyze_ticker',
    'aggregate_votes',
    'get_verdict',
    'export_to_excel',
    'validate_buy_signal',
    'validate_sell_signal',
    'aggregate_strategies',
    'select_best_strategy',
    
    # Data functions
    'fetch_ticker_data',
    'validate_data',
    
    # Trading functions
    'calculate_entry',
    'validate_trade',
    'calculate_shares',
    'validate_risk',
    
    # Infrastructure functions
    'setup_logger',
    'start_scheduler',
    
    # Legacy module names (backward compatibility)
    'compute_score',
    'signal_validator',
    'strategy_aggregator',
    'fetch_data_module',
    'data_validator',
    'entry_calculator',
    'trade_validator',
    'risk_manager',
    'logger',
    'cron_tasks',
]
