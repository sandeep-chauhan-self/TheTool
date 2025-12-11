from strategies import StrategyManager

print('Available strategies:')
for s in StrategyManager.list_summary():
    print(f'  - {s[\"id\"]}: {s[\"name\"]}')

print('\nStrategy 5 Details:')
s5 = StrategyManager.get(5)
print(f'  Stop Loss: {s5.get_risk_profile()[\"default_stop_loss_pct\"]}%')
print(f'  Target Multiplier: {s5.get_risk_profile()[\"default_target_multiplier\"]}x')
print(f'  Indicator Weights (Momentum): {s5.get_indicator_weights()}')
