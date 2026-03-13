"""Lab 14: Fraud Rule Engine — marimo notebook."""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        """
        # Lab 14: Fraud Rule Engine

        **Role**: Fintech Backend / Risk Engineering

        Fraud detection is core to every payment company. This lab builds a
        pluggable rule engine used to decide whether to APPROVE, REVIEW, or
        REJECT a transaction in milliseconds.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## Why Fraud Detection Matters

        Imagine a stolen card is used to buy $50,000 of electronics:

        1. Payment goes through — merchant ships the goods
        2. Real cardholder notices fraud — files a chargeback
        3. Bank reverses the charge — **merchant loses the $50,000**
        4. On top: chargeback fee ($15–$100), possible dispute penalty
        5. Too many chargebacks → payment processor terminates the account

        Without fraud rules you lose money *and* your ability to accept payments.
        With rules the transaction is flagged and blocked **before** it settles.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## Rule-Based vs ML Approaches

        | Aspect | Rule-Based | ML Model |
        |--------|-----------|----------|
        | Speed | Microseconds | Milliseconds to seconds |
        | Interpretability | Full — "blocked because country=NK" | Partial / black-box |
        | Maintenance | Manual rule tuning | Retraining pipeline |
        | Cold-start | Works immediately | Needs training data |
        | Compliance | Easy to audit | Harder to explain to regulators |

        **Rule engines are not obsolete.** Most real systems layer both:
        rules for hard blocklist/threshold logic, ML for subtle pattern detection.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## Three Built-In Rules

        ### 1. Amount Threshold
        Flags transactions over a dollar limit (default $10,000 — aligns with
        US Bank Secrecy Act reporting thresholds).

        ```
        score = 0.8  if amount > threshold
        score = 0.0  otherwise
        ```

        ### 2. Velocity Check
        Counts how many times the *same customer* transacted within the last
        hour. Stolen credentials often trigger rapid-fire purchases.

        ```
        score = 0.9  if count_in_window >= max_count
        score = 0.0  otherwise
        ```

        ### 3. Country Blocklist
        Hard-blocks transactions originating from OFAC-sanctioned countries
        (NK = North Korea, IR = Iran, SY = Syria by default).

        ```
        score = 1.0  if country in blocked_set
        score = 0.0  otherwise
        ```
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## Risk Scoring & Decision Logic

        Each rule returns a score in [0.0, 1.0].
        The engine takes the **maximum** across all rules:

        ```
        max_score >= 0.9  →  REJECT
        max_score >= 0.5  →  REVIEW
        otherwise         →  APPROVE
        ```

        Why max instead of sum? A single hard signal (blocked country) should
        override a clean velocity check — additive scoring can dilute blocklist hits.
        """
    )
    return


@app.cell
def __():
    import sys
    sys.path.insert(0, ".")

    from decimal import Decimal

    from models import Transaction
    from rule_engine import RuleEngine

    engine = RuleEngine()
    return Decimal, RuleEngine, Transaction, engine, sys


@app.cell
def __(Decimal, Transaction, engine, mo):
    mo.md("## Live Demo")

    normal_tx = Transaction(
        id="tx_normal",
        amount=Decimal("250.00"),
        currency="USD",
        country="US",
        customer_id="cust_001",
        timestamp=1_000_000.0,
    )
    d1, r1 = engine.evaluate(normal_tx)
    mo.md(
        f"""
        ### Normal transaction — ${normal_tx.amount} from {normal_tx.country}

        **Decision: {d1}**

        | Rule | Score | Reason |
        |------|-------|--------|
        {"".join(f"| {r.rule_name} | {r.score} | {r.reason} |" + chr(10) for r in r1)}
        """
    )
    return d1, normal_tx, r1


@app.cell
def __(Decimal, Transaction, engine, mo):
    high_tx = Transaction(
        id="tx_high",
        amount=Decimal("15000.00"),
        currency="USD",
        country="US",
        customer_id="cust_002",
        timestamp=1_000_000.0,
    )
    d2, r2 = engine.evaluate(high_tx)
    mo.md(
        f"""
        ### High-amount transaction — ${high_tx.amount} from {high_tx.country}

        **Decision: {d2}**

        | Rule | Score | Reason |
        |------|-------|--------|
        {"".join(f"| {r.rule_name} | {r.score} | {r.reason} |" + chr(10) for r in r2)}
        """
    )
    return d2, high_tx, r2


@app.cell
def __(Decimal, Transaction, engine, mo):
    blocked_tx = Transaction(
        id="tx_blocked",
        amount=Decimal("50.00"),
        currency="USD",
        country="NK",
        customer_id="cust_003",
        timestamp=1_000_000.0,
    )
    d3, r3 = engine.evaluate(blocked_tx)
    mo.md(
        f"""
        ### Blocked-country transaction — ${blocked_tx.amount} from {blocked_tx.country}

        **Decision: {d3}**

        | Rule | Score | Reason |
        |------|-------|--------|
        {"".join(f"| {r.rule_name} | {r.score} | {r.reason} |" + chr(10) for r in r3)}
        """
    )
    return blocked_tx, d3, r3


@app.cell
def __(mo):
    mo.md(
        """
        ## False Positives — The UX Tension

        Every fraud rule creates false positives: **legitimate transactions blocked**.

        Examples:
        - A frequent business traveller hits the velocity limit
        - A US expat living in a border region triggers a country flag
        - A large one-time purchase for a wedding gets stuck in REVIEW

        The cost of false positives:
        - Lost revenue from declined sales
        - Customer churn — frustrated users go to a competitor
        - Support cost — manual review queues

        **Tuning is the real skill.** Lower thresholds = fewer fraudsters through,
        more good customers blocked. Higher thresholds = more fraud leaks, better UX.
        Real systems use A/B testing and chargeback rate as the feedback signal.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## Reflection

        **What this proves**: "Built configurable fraud rule engine with velocity
        checks and risk scoring — 15 passing tests covering boundary conditions,
        customer isolation, and pluggable custom rules."

        **Confidence score: 8/10**

        Comfortable explaining:
        - Why max score over sum for hard-block signals
        - Boundary condition at exactly $10,000 (not flagged — `>` not `>=`)
        - Velocity window uses wall-clock delta, not calendar day
        - How to add a new rule (one function, register in RuleEngine)

        Next step: add an ML score as a fourth rule feeding from a scikit-learn
        model, keeping the same RuleResult interface.
        """
    )
    return


@app.cell
def __():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
