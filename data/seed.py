"""Generate a fake sales dataset in data/sales.db.

Deterministic (fixed random seed), so every run produces the same data.
Covers four quarters: Q4 2025 through Q3 2026 (Oct 1 2025 - Sep 30 2026).

Planted anomalies, so the agent has something real to find:
  1. SPIKE   - Dana Whitfield (East): Q3 2026 deal sizes ~2x her usual, plus extra deals.
  2. STALL   - West region: Q3 2026 deals mostly stuck in early stages, very few Closed Won.
  3. OUTLIER - One $1,250,000 Enterprise Suite deal (Luis Ortega, Central), Closed Won Aug 2026.
  4. SILENT  - Priya Nair (South): no new deals created in Q3 2026.

Run:  python data/seed.py
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "sales.db"
RNG = random.Random(42)
DATA_END = date(2026, 9, 30)

QUARTERS = [
    ("Q4 2025", date(2025, 10, 1), date(2025, 12, 31)),
    ("Q1 2026", date(2026, 1, 1), date(2026, 3, 31)),
    ("Q2 2026", date(2026, 4, 1), date(2026, 6, 30)),
    ("Q3 2026", date(2026, 7, 1), date(2026, 9, 30)),
]
LATEST_Q = "Q3 2026"

REPS = [
    # name, region, quarterly quota
    ("Dana Whitfield", "East", 300_000),
    ("Marcus Lee", "East", 275_000),
    ("Sofia Romero", "East", 250_000),
    ("Tom Becker", "West", 325_000),
    ("Aisha Khan", "West", 300_000),
    ("Ryan Cho", "West", 275_000),
    ("Luis Ortega", "Central", 300_000),
    ("Hannah Price", "Central", 250_000),
    ("Ben Adler", "Central", 250_000),
    ("Priya Nair", "South", 275_000),
    ("Jamal Brooks", "South", 300_000),
    ("Emily Tran", "South", 250_000),
]

PRODUCTS = {
    "Core Platform": 40_000,
    "Analytics Add-on": 15_000,
    "Support Plus": 8_000,
    "Enterprise Suite": 120_000,
}
PRODUCT_WEIGHTS = [0.40, 0.25, 0.20, 0.15]

OPEN_STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]

ACCOUNT_PREFIXES = ["Acme", "Northwind", "Bluepeak", "Ironclad", "Summit", "Harbor",
                    "Vertex", "Redwood", "Lumen", "Cobalt", "Pioneer", "Silverline",
                    "Granite", "Brightway", "Keystone"]
ACCOUNT_SUFFIXES = ["Logistics", "Health", "Foods", "Systems", "Retail", "Energy",
                    "Partners", "Labs"]
ACCOUNTS = [f"{p} {s}" for p in ACCOUNT_PREFIXES for s in ACCOUNT_SUFFIXES]

SCHEMA = """
CREATE TABLE reps (
    rep_id          INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    region          TEXT NOT NULL,
    quarterly_quota REAL NOT NULL
);

CREATE TABLE deals (
    deal_id      INTEGER PRIMARY KEY,
    account      TEXT NOT NULL,
    rep_id       INTEGER NOT NULL REFERENCES reps(rep_id),
    product      TEXT NOT NULL,
    stage        TEXT NOT NULL,  -- Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost
    amount       REAL NOT NULL,  -- USD
    created_date TEXT NOT NULL,  -- ISO date, YYYY-MM-DD
    close_date   TEXT            -- ISO date; NULL while the deal is open
);
"""


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=RNG.randint(0, (end - start).days))


def make_deal(rep: str, region: str, q_label: str, q_start: date, q_end: date) -> dict:
    product = RNG.choices(list(PRODUCTS), weights=PRODUCT_WEIGHTS)[0]
    amount = PRODUCTS[product] * RNG.uniform(0.7, 1.3)
    created = random_date(q_start, q_end)

    is_latest = q_label == LATEST_Q
    won_p, lost_p = (0.35, 0.25) if is_latest else (0.45, 0.35)

    # Anomaly 1: spike in deal size
    if rep == "Dana Whitfield" and is_latest:
        amount *= 2.2
    # Anomaly 2: West stalls in the latest quarter
    if region == "West" and is_latest:
        won_p, lost_p = 0.05, 0.10

    roll = RNG.random()
    if roll < won_p:
        stage = "Closed Won"
    elif roll < won_p + lost_p:
        stage = "Closed Lost"
    elif region == "West" and is_latest:
        stage = RNG.choice(OPEN_STAGES[:2])  # stuck early
    else:
        stage = RNG.choice(OPEN_STAGES)

    close_date = None
    if stage.startswith("Closed"):
        closed = created + timedelta(days=RNG.randint(15, 75))
        if closed > DATA_END:
            stage = RNG.choice(OPEN_STAGES[2:])  # hasn't closed yet
        else:
            close_date = closed.isoformat()

    return {
        "account": RNG.choice(ACCOUNTS),
        "rep": rep,
        "product": product,
        "stage": stage,
        "amount": round(amount, -2),
        "created_date": created.isoformat(),
        "close_date": close_date,
    }


def generate_deals() -> list[dict]:
    deals = []
    for rep, region, _ in REPS:
        for q_label, q_start, q_end in QUARTERS:
            # Anomaly 4: silent rep
            if rep == "Priya Nair" and q_label == LATEST_Q:
                continue
            n = RNG.randint(8, 12)
            if rep == "Dana Whitfield" and q_label == LATEST_Q:
                n += 6
            deals += [make_deal(rep, region, q_label, q_start, q_end) for _ in range(n)]

    # Anomaly 3: one huge outlier deal
    deals.append({
        "account": "Keystone Energy",
        "rep": "Luis Ortega",
        "product": "Enterprise Suite",
        "stage": "Closed Won",
        "amount": 1_250_000,
        "created_date": "2026-06-20",
        "close_date": "2026-08-14",
    })

    deals.sort(key=lambda d: d["created_date"])
    return deals


def main() -> None:
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO reps (name, region, quarterly_quota) VALUES (?, ?, ?)", REPS
    )
    rep_ids = {name: rid for rid, name in conn.execute("SELECT rep_id, name FROM reps")}

    deals = generate_deals()
    conn.executemany(
        """INSERT INTO deals (account, rep_id, product, stage, amount, created_date, close_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [(d["account"], rep_ids[d["rep"]], d["product"], d["stage"], d["amount"],
          d["created_date"], d["close_date"]) for d in deals],
    )
    conn.commit()
    conn.close()
    print(f"Wrote {len(REPS)} reps and {len(deals)} deals to {DB_PATH}")


if __name__ == "__main__":
    main()
