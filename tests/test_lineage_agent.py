import networkx as nx
import pytest

from lineage_agent.sql_parser import parse_all_models
from lineage_agent.graph_builder import (
    build_graph,
    execution_order,
    upstream_of,
    downstream_of,
    column_lineage_path,
)
from lineage_agent.agent import trace, deterministic_explanation


@pytest.fixture(scope="module")
def models():
    return parse_all_models()


@pytest.fixture(scope="module")
def graph(models):
    return build_graph(models)


def test_all_expected_models_are_discovered(models):
    expected = {
        "raw_hmda_loans",
        "raw_institutions",
        "stg_loans",
        "stg_institutions",
        "attr_ltv_bucket",
        "attr_dti_bucket",
        "attr_rate_spread_tier",
        "attr_hoepa_flag",
        "attr_high_minority_tract_flag",
        "attr_affordability_index",
        "fct_loans_enriched",
        "rpt_lender_summary",
        "rpt_dti_ltv_matrix",
        "rpt_tract_equity_summary",
    }
    assert expected.issubset(models.keys())


def test_graph_is_a_dag(graph):
    assert nx.is_directed_acyclic_graph(graph)


def test_source_models_have_no_upstream(models):
    assert models["raw_hmda_loans"].upstream_tables == set()
    assert models["raw_institutions"].upstream_tables == set()


def test_fact_table_joins_all_derived_attributes(models):
    fact = models["fct_loans_enriched"]
    expected_upstream = {
        "stg_loans",
        "stg_institutions",
        "attr_ltv_bucket",
        "attr_dti_bucket",
        "attr_rate_spread_tier",
        "attr_hoepa_flag",
        "attr_high_minority_tract_flag",
        "attr_affordability_index",
    }
    assert fact.upstream_tables == expected_upstream


def test_execution_order_respects_dependencies(graph):
    order = execution_order(graph)
    position = {name: i for i, name in enumerate(order)}

    # every model must come after all of its upstream dependencies
    for u, v in graph.edges():
        assert position[u] < position[v], f"{u} should be built before {v}"

    assert position["raw_hmda_loans"] < position["stg_loans"]
    assert position["stg_loans"] < position["fct_loans_enriched"]
    assert position["fct_loans_enriched"] < position["rpt_dti_ltv_matrix"]


def test_upstream_and_downstream_are_consistent(graph):
    up = upstream_of(graph, "fct_loans_enriched")
    down = downstream_of(graph, "raw_hmda_loans")

    assert "raw_hmda_loans" in up
    assert "attr_dti_bucket" in up
    assert "fct_loans_enriched" in down
    assert "rpt_lender_summary" in down


def test_column_level_trace_reaches_true_raw_source(graph):
    path = column_lineage_path(graph, "fct_loans_enriched", "dti_bucket")

    assert path[0] == ("fct_loans_enriched", "dti_bucket")
    assert path[-1] == ("raw_hmda_loans", "debt_to_income_ratio")
    # every intermediate hop should be a real model on the path
    for model_name, _col in path:
        assert model_name in {
            "fct_loans_enriched",
            "attr_dti_bucket",
            "stg_loans",
            "raw_hmda_loans",
        }


def test_column_level_trace_for_ltv_bucket(graph):
    path = column_lineage_path(graph, "fct_loans_enriched", "ltv_bucket")
    assert path[-1] == ("raw_hmda_loans", "loan_to_value_ratio")


def test_deterministic_explanation_is_human_readable():
    lt = trace("fct_loans_enriched", "dti_bucket")
    text = deterministic_explanation(lt)
    assert "raw_hmda_loans" in text
    assert "debt_to_income_ratio" in text
    assert "Ultimate source" in text


def test_unknown_model_raises_clear_error():
    with pytest.raises(ValueError, match="Unknown model"):
        trace("does_not_exist", "some_column")
