"""
The lineage agent: given an attribute (a model + column), produces a
human-readable, end-to-end explanation of where it came from -- the exact
capability described as "developing an AI-powered attribute lineage tracking
agent ... to capture end-to-end data transformations, joins, and derivations
across complex multi-system loan data flows."

Two layers:
  1. Deterministic graph trace (lineage_agent.graph_builder) -- always works,
     no API key, no network call. This is the ground truth.
  2. An LLM narrative layer on top, which turns the raw trace + SQL snippets
     into a natural-language explanation a non-technical stakeholder (or a
     recruiter skimming a demo) can read in one paragraph. Requires
     ANTHROPIC_API_KEY; falls back to a clear templated summary without it,
     so the tool is always runnable, but the "AI-powered" layer is real when
     a key is present -- not a hardcoded string.
"""
import os
from dataclasses import dataclass

from lineage_agent.graph_builder import build_graph, column_lineage_path, upstream_of, downstream_of
from lineage_agent.sql_parser import parse_all_models

SYSTEM_PROMPT = """You are a data lineage analyst. You are given a step-by-step
technical trace of how one column in a data warehouse table was derived,
including the SQL of every model involved. Write a clear, concise explanation
(4-8 sentences) suitable for a data engineering manager or recruiter skimming
a demo: what the attribute means, which raw source(s) it ultimately comes
from, and what transformations/joins happened along the way. Be specific
about table and column names but avoid restating raw SQL verbatim."""


@dataclass
class LineageTrace:
    model: str
    column: str
    column_path: list[tuple[str, str]]
    upstream_models: list[str]
    downstream_models: list[str]


def trace(model: str, column: str) -> LineageTrace:
    models = parse_all_models()
    if model not in models:
        raise ValueError(f"Unknown model '{model}'. Known models: {sorted(models)}")

    graph = build_graph(models)
    return LineageTrace(
        model=model,
        column=column,
        column_path=column_lineage_path(graph, model, column),
        upstream_models=upstream_of(graph, model),
        downstream_models=downstream_of(graph, model),
    )


def deterministic_explanation(lt: LineageTrace) -> str:
    hops = lt.column_path
    if len(hops) == 1:
        return (
            f"'{lt.column}' on '{lt.model}' has no traceable upstream column "
            f"(it may be computed from multiple columns, e.g. a case expression "
            f"or arithmetic across fields -- see the model SQL for the full expression)."
        )

    lines = [f"Lineage trace for {lt.model}.{lt.column}:"]
    for i, (m, c) in enumerate(hops):
        arrow = "  <-  " if i > 0 else "      "
        lines.append(f"{arrow}{m}.{c}")

    origin_model, origin_col = hops[-1]
    lines.append("")
    lines.append(
        f"Ultimate source: '{origin_col}' on '{origin_model}' "
        f"({'a raw source table' if origin_model.startswith('raw_') else origin_model})."
    )
    lines.append(f"Full upstream dependency chain ({len(lt.upstream_models)} models): {', '.join(lt.upstream_models)}")
    return "\n".join(lines)


def _build_llm_context(lt: LineageTrace, models: dict) -> str:
    parts = [f"Trace for {lt.model}.{lt.column}, from downstream to the raw source:\n"]
    for m, c in lt.column_path:
        model = models[m]
        parts.append(f"--- {m} (layer: {model.layer}, column of interest: {c}) ---")
        parts.append(model.sql.strip())
        parts.append("")
    return "\n".join(parts)


def explain(model: str, column: str, use_llm: bool | None = None) -> str:
    """
    Returns a natural-language lineage explanation.

    use_llm=None (default): use the LLM if ANTHROPIC_API_KEY is set, otherwise
    fall back to the deterministic explanation automatically.
    """
    lt = trace(model, column)
    models = parse_all_models()

    want_llm = use_llm if use_llm is not None else bool(os.getenv("ANTHROPIC_API_KEY"))
    if not want_llm:
        return deterministic_explanation(lt)

    try:
        import anthropic
    except ImportError:
        return deterministic_explanation(lt) + "\n\n(Install the `anthropic` package to enable LLM narrative mode.)"

    client = anthropic.Anthropic()
    context = _build_llm_context(lt, models)
    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    narrative = "".join(block.text for block in response.content if hasattr(block, "text"))
    return narrative + "\n\n---\nRaw trace (for verification):\n" + deterministic_explanation(lt)
