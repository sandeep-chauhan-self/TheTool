#!/usr/bin/env python
"""Test milestone status indicator fix"""

from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project_management.progress_tracker import ProgressTracker, Milestone

# Create a tracker and add milestones
tracker = ProgressTracker()
tracker.add_phase("Phase 1", "2025-01-01", 30)
tracker.add_task("Phase 1", "Task 1", effort_days=5, status="completed")

# Add achieved milestone
tracker.add_milestone("M1 Achieved", "2025-01-15", ["criteria 1"])
tracker.achieve_milestone("M1 Achieved")

# Add not-achieved milestone  
tracker.add_milestone("M2 Pending", "2025-02-01", ["criteria 2"])

# Generate report to see milestones
report = tracker.generate_report()

# Check for correct indicators
lines = report.split('\n')
milestone_section = False
achieved_line = None
pending_line = None

for line in lines:
    if 'MILESTONES:' in line:
        milestone_section = True
    elif milestone_section:
        if 'M1 Achieved' in line:
            achieved_line = line
        elif 'M2 Pending' in line:
            pending_line = line

print("Milestone Status Indicators Test")
print("=" * 50)

if achieved_line:
    print(f"Achieved milestone line: {achieved_line}")
    if achieved_line.startswith("✓"):
        print("  ✓ PASS: Achieved milestone shows ✓")
    else:
        print(f"  ✗ FAIL: Expected ✓ at start, got: {achieved_line[0]}")
else:
    print("  ✗ FAIL: Could not find achieved milestone line")

if pending_line:
    print(f"Pending milestone line: {pending_line}")
    if pending_line.startswith("?"):
        print("  ✓ PASS: Pending milestone shows ?")
    else:
        print(f"  ✗ FAIL: Expected ? at start, got: {pending_line[0]}")
else:
    print("  ✗ FAIL: Could not find pending milestone line")

# Verify they're different
if achieved_line and pending_line:
    if achieved_line[0] != pending_line[0]:
        print("\n✓ SUCCESS: Milestone indicators are distinct!")
    else:
        print(f"\n✗ FAILURE: Both indicators are the same: {achieved_line[0]}")
