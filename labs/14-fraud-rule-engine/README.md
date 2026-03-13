# Lab 14: Fraud Rule Engine

## Role Relevance
Fintech Backend / Risk Engineering — fraud detection is core to every payment company.

## Business Problem
Stolen card used to make $50,000 purchase from a sanctioned country. Without fraud rules: payment goes through, chargeback hits, you lose the money plus fees. With rules: flagged and blocked in milliseconds.

## First Principles
- **Rules**: Simple conditions that flag risky transactions
- **Scoring**: Each rule returns a risk score (0.0-1.0)
- **Decision**: Max score determines APPROVE / REVIEW / REJECT
- **Pluggable**: Add new rules without changing the engine

## How to Test
```bash
pytest labs/14-fraud-rule-engine/ -v
```

## Edge Cases Covered
- Normal transaction approved
- High amount triggers REVIEW
- Blocked country triggers REJECT
- Velocity spike triggers REJECT
- At-threshold amount (boundary test)
- Different customer history isolation
- Empty rules → APPROVE
- Custom pluggable rule

## What This Proves
"Built configurable fraud rule engine with velocity checks and risk scoring."
