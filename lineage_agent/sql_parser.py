"""
Parses the .sql model files in sql/ using sqlglot to extract, per model:
  - which upstream tables/models it reads from (table-level lineage)
  - which output columns it produces, and for simple cases which upstream
    column(s) each output column derives from (column-level lineage)

This is the same class of static-analysis approach tools like dbt's `dbt docs
generate` / sqllineage use under the hood -- no query execution required.
"""
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp

MODELS_ROOT = Path(__file__).resolve().parent.parent / "sql"


@dataclass
class ModelInfo:
    name: str
    layer: str
    path: Path
    sql: str
    upstream_tables: set[str] = field(default_factory=set)
    output_columns: dict[str, list[str]] = field(default_factory=dict)  # output_col -> [source expressions/cols]
    is_source: bool = False  # True for 01_raw models that read from a CSV, not another model
    source_csv: str | None = None


def _discover_model_files() -> list[Path]:
    return sorted(MODELS_ROOT.glob("*/*.sql"))


def _extract_column_lineage(select_expr: exp.Select) -> dict[str, list[str]]:
    """Best-effort mapping of output column name -> upstream column names it references."""
    output_columns: dict[str, list[str]] = {}
    for projection in select_expr.expressions:
        out_name = projection.alias_or_name
        source_cols = sorted({c.name for c in projection.find_all(exp.Column)})
        output_columns[out_name] = source_cols
    return output_columns


def parse_model(path: Path) -> ModelInfo:
    layer = path.parent.name
    name = path.stem
    sql = path.read_text()

    tree = sqlglot.parse_one(sql, read="duckdb")
    select_expr = tree if isinstance(tree, exp.Select) else tree.find(exp.Select)

    tables = {t.name for t in tree.find_all(exp.Table)}
    is_source = "__SOURCE_CSV__" in sql
    upstream_tables = set() if is_source else tables

    output_columns = _extract_column_lineage(select_expr) if select_expr else {}

    return ModelInfo(
        name=name,
        layer=layer,
        path=path,
        sql=sql,
        upstream_tables=upstream_tables,
        output_columns=output_columns,
        is_source=is_source,
        source_csv="__SOURCE_CSV__" if is_source else None,
    )


def parse_all_models() -> dict[str, ModelInfo]:
    return {m.stem: parse_model(m) for m in _discover_model_files()}
