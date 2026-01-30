---
description: Restructure project to reduce AI assistant overhead
---

# Project Cleanup Workflow

## Goal
Reduce the number of files the AI needs to scan and organize scripts by purpose.

## Steps

### 1. Archive Old/Experimental Scripts
Move one-off or deprecated scripts out of the main workspace:
```bash
mkdir -p scripts/archive/experiments
mkdir -p scripts/archive/old_versions

# Move experimental/test scripts
mv scripts/test_*.py scripts/archive/experiments/
mv scripts/verify_*.py scripts/archive/experiments/

# Move old backfill versions (keep only the latest)
# Review and move duplicates manually
```

### 2. Organize by Function
Create subdirectories for different purposes:
```bash
mkdir -p scripts/data_fetching
mkdir -p scripts/data_analysis
mkdir -p scripts/data_hydration
mkdir -p scripts/backtest
mkdir -p scripts/utilities

# Example moves:
mv scripts/fetch_*.py scripts/data_fetching/
mv scripts/analyze_*.py scripts/data_analysis/
mv scripts/audit_*.py scripts/data_analysis/
mv scripts/hydrate_*.py scripts/data_hydration/
mv scripts/backfill*.py scripts/data_fetching/
mv scripts/run_backtest.py scripts/backtest/
```

### 3. Move Data Outside Workspace (Optional)
If freezing persists, move the database outside the watched directory:
```bash
mkdir -p ~/HedgemonyData
mv data/*.db ~/HedgemonyData/
ln -s ~/HedgemonyData data/databases
```

Update `.gitignore`:
```
data/databases/
```

### 4. Create a Scripts Index
Create `scripts/README.md` documenting:
- Which scripts are part of the core pipeline
- Which are utilities
- Execution order for common tasks

### 5. Consolidate Similar Scripts
Review and merge scripts with overlapping functionality:
- Combine multiple fetch scripts into one with flags
- Merge similar analysis scripts
- Remove true duplicates

## Expected Benefits
- Faster AI workspace scanning
- Reduced file-watching overhead
- Clearer project structure
- Easier onboarding for new developers (or AI agents)
