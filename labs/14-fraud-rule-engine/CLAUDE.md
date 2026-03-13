# labs/14-fraud-rule-engine/ — Fraud Rule Engine

**Purpose:** Evaluate transactions against configurable risk rules.

## Depends on
- Nothing (standalone lab)

## Key files
- rule_engine.py: RuleEngine + 3 built-in rules
- models.py: Transaction, Decision, RuleResult
- test_rule_engine.py: 15 tests covering individual rules + engine integration

## Test
`pytest labs/14-fraud-rule-engine/ -v`
