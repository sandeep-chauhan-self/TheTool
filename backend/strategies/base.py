"""
Base Strategy Class

Abstract base class for all trading strategies.
Strategies define indicator weights and custom parameters.
Strategy logic lives in code - database only stores metadata.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    
    Each strategy defines:
    - Which indicators to use and their weights
    - Custom indicator parameters (thresholds, periods)
    - Default risk profile settings
    - Help content for user education
    """
    
    id: int
    name: str
    description: str
    
    @property
    def help_url(self) -> str:
        """URL path to strategy help page"""
        return f"/strategies/{self.id}"
    
    @abstractmethod
    def get_indicator_weights(self) -> Dict[str, float]:
        """
        Returns weight multiplier for each indicator.
        
        Weight meanings:
        - > 1.0 = More important (amplified influence)
        - 1.0 = Standard weight
        - < 1.0 = Less important (reduced influence)  
        - 0.0 = Disabled (excluded from analysis)
        
        Returns:
            Dict mapping indicator names to weight multipliers
        """
        pass
    
    @abstractmethod
    def get_category_weights(self) -> Dict[str, float]:
        """
        Returns weight multiplier for each indicator category.
        
        Categories: trend, momentum, volatility, volume
        
        Returns:
            Dict mapping category names to weight multipliers
        """
        pass
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns custom parameters for indicators.
        
        Override default indicator settings like periods, thresholds.
        Example: {'rsi': {'period': 14, 'overbought': 70, 'oversold': 30}}
        
        Returns:
            Dict mapping indicator names to parameter dicts
        """
        return {}
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """
        Returns default risk management settings for this strategy.
        
        Returns:
            Dict with stop_loss_pct, target_multiplier, max_position_pct
        """
        return {
            'default_stop_loss_pct': 2.0,
            'default_target_multiplier': 2.0,
            'max_position_size_pct': 20
        }
    
    def get_help_content(self) -> str:
        """
        Load help content from markdown file.
        
        Looks for file at: strategies/help/strategy_{id}.md
        
        Returns:
            Markdown string with strategy documentation
        """
        help_path = os.path.join(
            os.path.dirname(__file__), 
            'help', 
            f'strategy_{self.id}.md'
        )
        if os.path.exists(help_path):
            with open(help_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Fallback to basic description
        return f"# {self.name}\n\n{self.description}"
    
    def to_dict(self) -> dict:
        """
        Convert strategy to dictionary for API responses.
        
        Returns:
            Dict with strategy metadata and configuration
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'help_url': self.help_url,
            'indicator_weights': self.get_indicator_weights(),
            'category_weights': self.get_category_weights(),
            'risk_profile': self.get_risk_profile()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"
