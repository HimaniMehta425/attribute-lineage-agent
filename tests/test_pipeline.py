"""
Integration test: runs the full pipeline against the checked-in sample data
on a throwaway in-memory-ish DuckDB file and sanity-checks the output.
"""
import os
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    os.environ["PIPELINE_ENGINE"] = "duckdb"
    db_path = tmp_path_factory.mktemp("wh") / "test_warehouse.duckdb"
    os.environ["DUCKDB_PATH"] = str(db_path)

    from pipeline.run_pipeline import run

    run(
        loans_csv=ROOT / "data" / "sample" / "hmda_il_sample.csv",
        institutions_csv=ROOT / "data" / "sample" / "institutions_il_2024.csv",
    )
    conn = duckdb.connect(str(db_path), read_only=True)
    yield conn
    conn.close()


def test_raw_layer_loaded(warehouse):
    count = warehouse.execute("select count(*) from raw_hmda_loans").fetchone()[0]
    assert count > 0


def test_staging_cleans_sentinel_values(warehouse):
    # 'Exempt' and 'NA' strings should never survive into the staging layer's
    # numeric columns.
    bad = warehouse.execute(
        "select count(*) from stg_loans where try_cast(loan_to_value_ratio as varchar) in ('Exempt', 'NA')"
    ).fetchone()[0]
    assert bad == 0


def test_fact_table_row_count_matches_staging(warehouse):
    stg_count = warehouse.execute("select count(*) from stg_loans").fetchone()[0]
    fact_count = warehouse.execute("select count(*) from fct_loans_enriched").fetchone()[0]
    assert stg_count == fact_count  # left joins must not fan out rows


def test_fact_table_has_lender_names_joined(warehouse):
    matched = warehouse.execute(
        "select count(*) from fct_loans_enriched where lender_name is not null"
    ).fetchone()[0]
    total = warehouse.execute("select count(*) from fct_loans_enriched").fetchone()[0]
    assert matched > 0
    assert matched <= total


def test_reporting_layer_produces_rows(warehouse):
    for table in ("rpt_lender_summary", "rpt_dti_ltv_matrix", "rpt_tract_equity_summary"):
        count = warehouse.execute(f"select count(*) from {table}").fetchone()[0]
        assert count > 0, f"{table} produced no rows"
