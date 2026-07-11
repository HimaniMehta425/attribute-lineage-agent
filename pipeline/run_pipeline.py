"""
Materializes every model in sql/ into the warehouse (DuckDB by default, or
Snowflake if PIPELINE_ENGINE=snowflake), in dependency order determined by
the same lineage graph the lineage agent uses to explain lineage to humans.

Usage:
    python -m pipeline.run_pipeline
    python -m pipeline.run_pipeline --csv data/raw/hmda_il_17031_2024.csv --institutions data/raw/institutions_il_2024.csv
"""
import argparse
from pathlib import Path

from pipeline.db import execute, get_connection, get_engine_name
from lineage_agent.graph_builder import build_graph, execution_order
from lineage_agent.sql_parser import parse_all_models

ROOT = Path(__file__).resolve().parent.parent


def run(loans_csv: Path, institutions_csv: Path) -> None:
    models = parse_all_models()
    graph = build_graph(models)
    order = execution_order(graph)

    conn = get_connection()
    engine = get_engine_name()
    print(f"Engine: {engine}")

    csv_for_source = {
        "raw_hmda_loans": loans_csv,
        "raw_institutions": institutions_csv,
    }

    for model_name in order:
        model = models[model_name]
        print(f"-> building {model.layer}/{model_name} ...", end=" ")

        if model.is_source:
            csv_path = csv_for_source[model_name]
            sql = model.sql.replace("__SOURCE_CSV__", str(csv_path))
        else:
            sql = model.sql

        create_stmt = f"CREATE OR REPLACE TABLE {model_name} AS (\n{sql}\n)"
        execute(conn, create_stmt)

        count = execute(conn, f"SELECT COUNT(*) FROM {model_name}").fetchone()[0]
        print(f"{count:,} rows")

    if engine == "duckdb":
        conn.close()
    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=str(ROOT / "data" / "sample" / "hmda_il_sample.csv"))
    parser.add_argument("--institutions", default=str(ROOT / "data" / "sample" / "institutions_il_2024.csv"))
    args = parser.parse_args()

    run(Path(args.csv), Path(args.institutions))
