"""Create an evaluation dataset for the joke prompt in Unity Catalog.

Usage:
    python scripts/create_joke_eval_dataset.py

Requires DATABRICKS_PROFILE env var or ~/.databrickscfg with a [prod-shadow] profile.
"""

import os
from databricks.sdk import WorkspaceClient

CATALOG = "prod_shadow_ai"
SCHEMA = "aipc_scrap"
TABLE = "joke_eval_dataset"
FULL_NAME = f"`{CATALOG}`.`{SCHEMA}`.`{TABLE}`"

# Diverse set of topics and languages for evaluation
ROWS = [
    ("cats", "English"),
    ("programming", "English"),
    ("coffee", "French"),
    ("dentists", "English"),
    ("time travel", "Spanish"),
    ("pizza", "Italian"),
    ("mondays", "English"),
    ("robots", "English"),
    ("gardening", "German"),
    ("procrastination", "English"),
    ("sharks", "English"),
    ("math", "Japanese"),
    ("cooking disasters", "English"),
    ("pirates", "English"),
    ("artificial intelligence", "English"),
    ("flat tires", "French"),
    ("penguins", "English"),
    ("job interviews", "English"),
    ("gravity", "Spanish"),
    ("dad jokes", "English"),
]


def main():
    profile = os.environ.get("DATABRICKS_PROFILE", "prod-shadow")
    w = WorkspaceClient(profile=profile)

    sql = f"""
    CREATE OR REPLACE TABLE {FULL_NAME} (
        topic STRING,
        language STRING
    ) USING DELTA
    """
    print(f"Creating table {FULL_NAME} ...")
    w.statement_execution.execute_statement(
        warehouse_id=get_warehouse_id(w),
        statement=sql,
        wait_timeout="30s",
    )

    values = ", ".join(f"('{t}', '{l}')" for t, l in ROWS)
    insert_sql = f"INSERT INTO {FULL_NAME} VALUES {values}"
    print(f"Inserting {len(ROWS)} rows ...")
    w.statement_execution.execute_statement(
        warehouse_id=get_warehouse_id(w),
        statement=insert_sql,
        wait_timeout="30s",
    )

    print(f"Done! Table {FULL_NAME} created with {len(ROWS)} rows.")
    print(f"\nColumns: topic, language")
    print(f"  - v3 mapping: topic → topic")
    print(f"  - v4 mapping: topic → topic, language → language")


def get_warehouse_id(w: WorkspaceClient) -> str:
    """Find first running SQL warehouse."""
    for wh in w.warehouses.list():
        if wh.state and wh.state.value == "RUNNING" and wh.id:
            return wh.id
    raise RuntimeError("No running SQL warehouse found")


if __name__ == "__main__":
    main()
