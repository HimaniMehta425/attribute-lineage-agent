"""
Builds a directed lineage graph over all parsed SQL models: an edge
upstream -> downstream means "downstream reads from upstream". Also carries
column-level detail on each node so the agent can answer both
"what feeds fct_loans_enriched" (table-level) and
"where did fct_loans_enriched.dti_bucket come from" (column-level) questions.

This graph is the single source of truth used both to explain lineage to a
human (lineage_agent/agent.py) and to determine a safe execution order for
the pipeline (pipeline/run_pipeline.py) via topological sort -- one artifact,
two consumers.
"""
import networkx as nx

from lineage_agent.sql_parser import ModelInfo, parse_all_models


def build_graph(models: dict[str, ModelInfo] | None = None) -> nx.DiGraph:
    models = models or parse_all_models()
    g = nx.DiGraph()

    for name, model in models.items():
        g.add_node(
            name,
            layer=model.layer,
            is_source=model.is_source,
            output_columns=model.output_columns,
            sql=model.sql,
        )

    for name, model in models.items():
        for upstream in model.upstream_tables:
            if upstream in models:
                g.add_edge(upstream, name)
            else:
                # Referenced table isn't a model we parsed (shouldn't happen given
                # our fixed model set, but fail loud rather than silently drop it).
                raise ValueError(f"Model '{name}' references unknown upstream table '{upstream}'")

    if not nx.is_directed_acyclic_graph(g):
        cycle = next(iter(nx.simple_cycles(g)))
        raise ValueError(f"Lineage graph has a cycle: {cycle}")

    return g


def execution_order(g: nx.DiGraph) -> list[str]:
    """Topological order -- safe order to (re)materialize every model."""
    return list(nx.topological_sort(g))


def upstream_of(g: nx.DiGraph, model_name: str) -> list[str]:
    """All ancestor models (direct + transitive) feeding into model_name, in
    topological order -- the full end-to-end lineage trace."""
    ancestors = nx.ancestors(g, model_name)
    ordered = [n for n in nx.topological_sort(g) if n in ancestors]
    return ordered


def downstream_of(g: nx.DiGraph, model_name: str) -> list[str]:
    """Everything that would be impacted if model_name's schema/logic changed."""
    descendants = nx.descendants(g, model_name)
    ordered = [n for n in nx.topological_sort(g) if n in descendants]
    return ordered


def column_lineage_path(g: nx.DiGraph, model_name: str, column_name: str) -> list[tuple[str, str]]:
    """
    Walks backward from (model_name, column_name) through upstream models,
    following column-name matches, to produce a column-level trace:
    [(model, column), (model, column), ...] ending at a raw source column.

    This is a best-effort trace (matches by column name across joins/aliases),
    which is exactly the same limitation real dbt-ecosystem lineage tools have
    without full binder-level column resolution -- documented as such rather
    than silently overclaiming precision.
    """
    trace = [(model_name, column_name)]
    current_model, current_col = model_name, column_name

    while True:
        node = g.nodes[current_model]
        if node["is_source"]:
            break

        preds = list(g.predecessors(current_model))
        if not preds:
            break

        output_cols = node["output_columns"]
        source_cols_for_current = output_cols.get(current_col, [])

        next_hop = None
        for pred in preds:
            pred_cols = g.nodes[pred]["output_columns"]
            for src_col in source_cols_for_current:
                if src_col in pred_cols:
                    next_hop = (pred, src_col)
                    break
            if next_hop:
                break

        if not next_hop:
            # Couldn't resolve a specific upstream column -- stop the precise
            # trace here (still useful: caller sees where it ran out).
            break

        trace.append(next_hop)
        current_model, current_col = next_hop

    return trace
