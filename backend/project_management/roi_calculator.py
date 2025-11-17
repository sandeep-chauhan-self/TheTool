"""
ROI Calculator - Calculate business value and investment returns

This module calculates Return on Investment (ROI) for refactoring projects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Investment:
    """Project investment"""
    total: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.now)
    currency: str = "USD"
    
    def validate(self):
        """Validate that breakdown sums to total"""
        if self.breakdown:
            breakdown_sum = sum(self.breakdown.values())
            if abs(breakdown_sum - self.total) > 0.01:
                raise ValueError(
                    f"Investment breakdown ({breakdown_sum}) doesn't match total ({self.total})"
                )


@dataclass
class Benefit:
    """Annual benefit from refactoring"""
    name: str
    annual_value: float
    description: str
    category: str = "other"
    confidence: float = 1.0
    
    def get_adjusted_value(self) -> float:
        """Get value adjusted by confidence"""
        return self.annual_value * self.confidence


@dataclass
class ROIReport:
    """ROI analysis report"""
    investment: float
    annual_benefits: float
    payback_period_months: float
    roi_percentage: float
    roi_years: int = 3
    npv: Optional[float] = None
    irr: Optional[float] = None
    
    def is_positive_roi(self) -> bool:
        """Check if ROI is positive"""
        return self.roi_percentage > 0
    
    def is_good_investment(self, threshold_months: float = 24) -> bool:
        """Check if investment pays back within threshold"""
        return self.payback_period_months <= threshold_months


class ROICalculator:
    """Calculate ROI for refactoring project"""
    
    def __init__(self):
        self.investment: Optional[Investment] = None
        self.benefits: List[Benefit] = []
        self.ongoing_costs: float = 0.0
    
    def set_investment(self, total: float, breakdown: Optional[Dict[str, float]] = None,
                      currency: str = "USD"):
        """Set initial investment"""
        self.investment = Investment(
            total=total,
            breakdown=breakdown or {},
            currency=currency
        )
        self.investment.validate()
    
    def add_benefit(self, name: str, annual_value: float, description: str,
                   category: str = "other", confidence: float = 1.0):
        """Add an annual benefit"""
        if confidence < 0 or confidence > 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        benefit = Benefit(
            name=name,
            annual_value=annual_value,
            description=description,
            category=category,
            confidence=confidence
        )
        self.benefits.append(benefit)
    
    def set_ongoing_costs(self, monthly_cost: float):
        """Set monthly ongoing costs"""
        self.ongoing_costs = monthly_cost
    
    def calculate_total_annual_benefits(self, adjusted: bool = True) -> float:
        """Calculate total annual benefits"""
        if adjusted:
            return sum(b.get_adjusted_value() for b in self.benefits)
        else:
            return sum(b.annual_value for b in self.benefits)
    
    def calculate_net_annual_benefit(self) -> float:
        """Calculate net annual benefit"""
        annual_benefit = self.calculate_total_annual_benefits()
        annual_cost = self.ongoing_costs * 12
        return annual_benefit - annual_cost
    
    def calculate_payback_period(self) -> float:
        """Calculate payback period in months"""
        if self.investment is None:
            raise ValueError("Investment not set. Call set_investment() first.")
        
        if not self.benefits:
            raise ValueError("No benefits added. Call add_benefit() first.")
        
        net_annual = self.calculate_net_annual_benefit()
        if net_annual <= 0:
            return float('inf')
        
        monthly_benefit = net_annual / 12
        return self.investment.total / monthly_benefit
    
    def calculate_roi_percentage(self, years: int = 3) -> float:
        """Calculate ROI percentage over specified years"""
        if self.investment is None:
            raise ValueError("Investment not set")
        
        net_annual = self.calculate_net_annual_benefit()
        total_benefit = net_annual * years
        net_gain = total_benefit - self.investment.total
        
        return (net_gain / self.investment.total) * 100
    
    def calculate_npv(self, years: int = 3, discount_rate: float = 0.10) -> float:
        """Calculate Net Present Value"""
        if self.investment is None:
            raise ValueError("Investment not set")
        
        net_annual = self.calculate_net_annual_benefit()
        
        npv = -self.investment.total
        for year in range(1, years + 1):
            npv += net_annual / ((1 + discount_rate) ** year)
        
        return npv
    
    def generate_report(self, years: int = 3, discount_rate: float = 0.10) -> ROIReport:
        """Generate comprehensive ROI report"""
        if self.investment is None:
            raise ValueError("Investment not set")
        
        payback = self.calculate_payback_period()
        roi_pct = self.calculate_roi_percentage(years)
        npv = self.calculate_npv(years, discount_rate)
        
        return ROIReport(
            investment=self.investment.total,
            annual_benefits=self.calculate_net_annual_benefit(),
            payback_period_months=payback,
            roi_percentage=roi_pct,
            roi_years=years,
            npv=npv
        )
    
    def generate_detailed_report(self, years: int = 3) -> str:
        """Generate detailed text report"""
        if self.investment is None:
            raise ValueError("Investment not set")
        
        lines = []
        lines.append("=" * 80)
        lines.append("ROI ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Investment breakdown
        lines.append("INITIAL INVESTMENT:")
        lines.append("-" * 80)
        lines.append(f"Total: ${self.investment.total:,.2f} {self.investment.currency}")
        if self.investment.breakdown:
            for category, amount in self.investment.breakdown.items():
                pct = (amount / self.investment.total) * 100
                lines.append(f"  {category.capitalize()}: ${amount:,.2f} ({pct:.1f}%)")
        lines.append("")
        
        # Benefits breakdown
        lines.append("ANNUAL BENEFITS:")
        lines.append("-" * 80)
        
        benefits_by_category = {}
        for benefit in self.benefits:
            if benefit.category not in benefits_by_category:
                benefits_by_category[benefit.category] = []
            benefits_by_category[benefit.category].append(benefit)
        
        for category, benefits in benefits_by_category.items():
            category_total = sum(b.get_adjusted_value() for b in benefits)
            lines.append(f"{category.upper()}: ${category_total:,.2f}/year")
            for benefit in benefits:
                adj_value = benefit.get_adjusted_value()
                conf_str = f" ({benefit.confidence*100:.0f}% confidence)" if benefit.confidence < 1 else ""
                lines.append(f"  - {benefit.name}: ${adj_value:,.2f}{conf_str}")
                lines.append(f"    {benefit.description}")
            lines.append("")
        
        total_benefits = self.calculate_total_annual_benefits()
        lines.append(f"Total Annual Benefits: ${total_benefits:,.2f}")
        lines.append("")
        
        # Ongoing costs
        if self.ongoing_costs > 0:
            annual_costs = self.ongoing_costs * 12
            lines.append(f"Ongoing Costs: ${self.ongoing_costs:,.2f}/month (${annual_costs:,.2f}/year)")
            lines.append(f"Net Annual Benefit: ${self.calculate_net_annual_benefit():,.2f}")
            lines.append("")
        
        # ROI calculations
        lines.append("ROI CALCULATIONS:")
        lines.append("-" * 80)
        
        payback = self.calculate_payback_period()
        roi_pct = self.calculate_roi_percentage(years)
        npv = self.calculate_npv(years)
        
        lines.append(f"Payback Period: {payback:.1f} months ({payback/12:.1f} years)")
        lines.append(f"{years}-Year ROI: {roi_pct:+.1f}%")
        lines.append(f"Net Present Value: ${npv:,.2f}")
        lines.append("")
        
        # Year-by-year breakdown
        lines.append(f"YEAR-BY-YEAR BREAKDOWN ({years} years):")
        lines.append("-" * 80)
        
        net_annual = self.calculate_net_annual_benefit()
        cumulative = -self.investment.total
        
        lines.append(f"Year 0: -${self.investment.total:,.2f} (Initial Investment)")
        for year in range(1, years + 1):
            cumulative += net_annual
            lines.append(f"Year {year}: +${net_annual:,.2f} (Cumulative: ${cumulative:,.2f})")
        lines.append("")
        
        # Assessment
        lines.append("ASSESSMENT:")
        lines.append("-" * 80)
        
        if payback <= 12:
            assessment = "EXCELLENT - Pays back within 1 year"
        elif payback <= 24:
            assessment = "GOOD - Pays back within 2 years"
        elif payback <= 36:
            assessment = "ACCEPTABLE - Pays back within 3 years"
        else:
            assessment = "POOR - Takes >3 years to pay back"
        
        lines.append(f"Investment Quality: {assessment}")
        lines.append(f"Recommendation: {'PROCEED' if payback <= 36 else 'RECONSIDER'}")
        lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def calculate_payback_period(investment: float, annual_benefit: float) -> float:
    """Calculate simple payback period"""
    if annual_benefit <= 0:
        return float('inf')
    monthly_benefit = annual_benefit / 12
    return investment / monthly_benefit


def calculate_roi_percentage(investment: float, annual_benefit: float, years: int = 3) -> float:
    """Calculate ROI percentage"""
    total_benefit = annual_benefit * years
    net_gain = total_benefit - investment
    return (net_gain / investment) * 100
