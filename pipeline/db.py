"""
Database connection abstraction.

Defaults to DuckDB: local, embedded, zero setup -- so anyone can clone this
repo and run the pipeline with one command, no credentials required.

Set PIPELINE_ENGINE=snowflake (plus the SNOWFLAKE_* env vars below) to point
the exact same SQL models in sql/ at a live Snowflake warehouse instead. The
models are written in plain ANSI-ish SQL (no DuckDB-only syntax beyond
read_csv_auto, which is only used in the raw layer) so they run unchanged on
both engines.
"""
import os


def get_engine_name() -> str:
    return os.getenv("PIPELINE_ENGINE", "duckdb").lower()


def get_connection():
    engine = get_engine_name()

    if engine == "duckdb":
        import duckdb

        db_path = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
        return duckdb.connect(db_path)

    if engine == "snowflake":
        try:
            import snowflake.connector
        except ImportError as e:
            raise ImportError(
                "PIPELINE_ENGINE=snowflake requires the snowflake-connector-python "
                "package: pip install snowflake-connector-python"
            ) from e

        required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise EnvironmentError(f"Missing required Snowflake env vars: {', '.join(missing)}")

        return snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ.get("SNOWFLAKE_PASSWORD"),
            authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
        )

    raise ValueError(f"Unknown PIPELINE_ENGINE: {engine!r} (expected 'duckdb' or 'snowflake')")


def execute(conn, sql: str):
    """Run a statement across either engine's slightly different cursor API."""
    if get_engine_name() == "duckdb":
        return conn.execute(sql)
    cur = conn.cursor()
    cur.execute(sql)
    return cur
