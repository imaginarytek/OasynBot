# HedgemonyBot Documentation Archive

This directory contains **historical progress logs and status documents** from the development of HedgemonyBot. These files represent completed milestones, research findings, and interim reports that are no longer actively referenced but are preserved for historical context.

**Archive Date:** January 31, 2026

---

## Why These Files Were Archived

These documents served as progress tracking, decision logs, and status reports during active development phases. They have been archived because:

1. **Completion:** The work they describe has been completed and integrated into the main system
2. **Superseded:** Information is now documented in permanent architecture/design docs
3. **Organization:** Keeping them in the root directory created clutter

**Important:** These files are **preserved, not deleted** - they contain valuable historical context about design decisions and evolution of the project.

---

## Archive Index

### Dataset Development & Quality

**BACKTEST_RESULTS.md**
- Final backtest results from dataset validation
- Performance metrics on curated events
- Trade-by-trade analysis

**CLEANUP_SUMMARY.md**
- Database cleanup operations completed
- Schema migrations and data corrections
- Quality improvements implemented

**CRITICAL_FINDINGS_EVENT_DATASET.md**
- Critical issues discovered during event dataset audit
- Data quality problems and solutions
- Timestamp accuracy findings

**CURATED_100_EVENTS.md**
- Documentation of first 100 curated high-quality events
- Selection criteria and quality gates
- Initial dataset milestone

**DATASET_FINAL_REPORT.md**
- Comprehensive final report on event dataset
- Statistics, quality metrics, coverage analysis
- Recommendations for future expansion

**DATASET_ORGANIZATION.md**
- Database schema design decisions
- Table structure rationale (master_events, curated_events, etc.)
- Migration path from legacy schema

**DATA_QUALITY_AUDIT.md**
- Detailed audit of all event data quality
- Timestamp precision analysis
- Source tier verification results

### Event Discovery Methodology

**EVENT_DISCOVERY_PROGRESS.md**
- Milestone tracking for event discovery system
- Spike-first methodology development
- Twitter integration progress

**FETCH_COMPLETE_REPORT.md**
- Results from bulk historical data fetching
- API usage, rate limiting lessons learned
- Data coverage achieved

**HYBRID_DISCOVERY_GUIDE.md**
- Guide for combining spike-first + manual discovery
- Workflow documentation
- Best practices established

**MASTER_EVENTS_CLEANUP.md**
- Cleanup operations on master_events table
- Duplicate removal, quality fixes
- Schema standardization

**TIER1_SOURCE_RESEARCH.md**
- Research into tier-1 news sources
- API capabilities, rate limits
- Source priority recommendations

**TWITTER_SEARCH_PROTOCOL.md** *(Moved back to root - active reference)*
- Protocol for finding events with precise timestamps
- Twitter Advanced Search techniques
- Best kept as active reference document

### Backtesting & Optimization

**FINAL_RESULTS_OPTION3.md**
- Results from strategy optimization experiments
- Parameter tuning findings
- Option 3 performance analysis

**FINAL_STATUS.md**
- Status snapshot from a major milestone
- Completed features, pending work
- Decision points documented

**OPTIMIZATION_RESULTS.md**
- Strategy optimization iterations
- Parameter sensitivity analysis
- Performance improvements achieved

### Infrastructure & Architecture

**PROJECT_SUMMARY.md**
- High-level project summary from development phase
- Architecture decisions snapshot
- Component overview

**VERIFICATION_LOG.md**
- System verification and validation log
- Testing results, edge cases
- Quality assurance findings

**VERBATIM_TEXT_ACTION_PLAN.md**
- Plan for implementing verbatim text extraction
- Why exact news text matters for sentiment
- Implementation roadmap

**VERBATIM_TEXT_TEMPLATE.md**
- Template for storing verbatim event text
- Schema design for exact quotes
- Source attribution requirements

**WHERE_WE_ARE.md**
- Status checkpoint document
- What's working, what needs work
- Next steps documented at that point in time

---

## How to Use This Archive

### For Historical Context
If you need to understand **why** a decision was made:
1. Check the relevant archive document
2. Look for "Decision:" or "Rationale:" sections
3. Review findings that led to current architecture

### For Dataset Expansion
When adding new events, reference:
- `CURATED_100_EVENTS.md` - Quality standards
- `TIER1_SOURCE_RESEARCH.md` - Source priorities
- `HYBRID_DISCOVERY_GUIDE.md` - Discovery workflow

### For Performance Baselines
When optimizing strategies, reference:
- `BACKTEST_RESULTS.md` - Baseline performance
- `OPTIMIZATION_RESULTS.md` - What was already tried
- `FINAL_RESULTS_OPTION3.md` - Best performing configuration

---

## Active Documentation

For current, actively maintained documentation, see:

**Main Project Docs:**
- [Root README.md](../../README.md) - Project overview
- [Architecture](../architecture.md) - System design
- [Backtesting Methodology](../backtesting_methodology.md) - How backtesting works
- [Database Separation](../DATABASE_SEPARATION.md) - Bias prevention

**Module-Specific:**
- [Backtest Module](../../src/backtest/README.md) - API reference
- [Event Scraping Skill](../../.agent/skills/event_scraping/SKILL.md) - Spike-first methodology

**Development:**
- [Roadmap](../ROADMAP.md) - Future plans
- [Known Issues](../known_issues.md) - Current limitations

---

## Recovery

These files are kept in archive (not deleted) in case you need to:
- Understand the evolution of the system
- Reference past experiments and their results
- Recover context about design decisions
- Review historical quality standards

**Note:** Information in these files may reference **outdated schemas** (e.g., `news` table instead of `master_events`) or **deprecated features**. Always verify against current active documentation.

---

**Archived:** January 31, 2026
**Reason:** Documentation consolidation and organization
**Status:** Preserved for historical reference
