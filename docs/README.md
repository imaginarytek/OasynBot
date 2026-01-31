# HedgemonyBot Documentation

Welcome to the HedgemonyBot documentation! This index helps you find what you need.

---

## Getting Started

- [**Architecture Overview**](architecture.md) - System design, components, and data flow
- [**Quick Start Checklist**](../QUICK_START_CHECKLIST.md) - Step-by-step setup guide
- [**Main README**](../README.md) - Project overview and features

---

## Core Systems

### Backtesting
- [**Backtesting Methodology**](backtesting_methodology.md) - How bias-free backtesting works
- [**Backtest Audit**](BACKTEST_AUDIT.md) - Professional setup verification (Jan 2026)
- [**Backtest Module README**](../src/backtest/README.md) - Complete API reference

### Data & Events
- [**Database Separation**](DATABASE_SEPARATION.md) - Why we use two databases (bias prevention)
- [**Event Data Schemas**](event_data_schemas.md) - Database structure and tables
- [**Event Scraping Skill**](../.agent/skills/event_scraping/SKILL.md) - Spike-first methodology

### Trading (In Development)
- [**Twitter Search Protocol**](../TWITTER_SEARCH_PROTOCOL.md) - Finding events with precise timestamps

---

## Development

- [**Roadmap**](ROADMAP.md) - Future enhancements and priorities
- [**Known Issues**](known_issues.md) - Current limitations and planned fixes
- [**Source Priority Upgrade**](SOURCE_PRIORITY_UPGRADE.md) - Tier-1 source requirements

---

## Archives

- [**Historical Progress Logs**](archive/README.md) - Completed work and milestones

---

## Quick Links by Topic

**Want to understand the Three Brains Council?**
→ [Architecture: Brain Layer](architecture.md#2-brain-layer---the-three-brains-council)

**Want to know how we prevent look-ahead bias?**
→ [Database Separation](DATABASE_SEPARATION.md)
→ [Backtest Audit: Bias Prevention](BACKTEST_AUDIT.md)

**Want to add new events to the dataset?**
→ [Event Scraping Skill](../.agent/skills/event_scraping/SKILL.md)
→ [Twitter Search Protocol](../TWITTER_SEARCH_PROTOCOL.md)

**Want to create a custom trading strategy?**
→ [Backtest Module README](../src/backtest/README.md#creating-custom-strategies)

**Want to run a backtest?**
→ [Quick Start](../QUICK_START_CHECKLIST.md)
→ [Main README: Quick Start](../README.md#quick-start)

---

**Last Updated:** 2026-01-31
