"""
CLI for the attribute lineage agent.

    python -m lineage_agent.cli trace fct_loans_enriched dti_bucket
    python -m lineage_agent.cli trace fct_loans_enriched dti_bucket --llm
    python -m lineage_agent.cli list
    python -m lineage_agent.cli graph > docs/lineage_graph.mmd
"""
import argparse
import sys

from lineage_agent.agent import explain
from lineage_agent.sql_parser import parse_all_models
from lineage_agent.diagram import to_mermaid


def cmd_trace(args):
    use_llm = True if args.llm else (False if args.no_llm else None)
    print(explain(args.model, args.column, use_llm=use_llm))


def cmd_list(_args):
    models = parse_all_models()
    for name, model in sorted(models.items(), key=lambda kv: (kv[1].layer, kv[0])):
        cols = ", ".join(model.output_columns.keys())
        print(f"[{model.layer}] {name}")
        print(f"    columns: {cols}\n")


def cmd_graph(_args):
    print(to_mermaid())


def main(argv=None):
    parser = argparse.ArgumentParser(description="Attribute lineage agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_trace = sub.add_parser("trace", help="Explain the end-to-end lineage of one column")
    p_trace.add_argument("model", help="Model name, e.g. fct_loans_enriched")
    p_trace.add_argument("column", help="Column name, e.g. dti_bucket")
    p_trace.add_argument("--llm", action="store_true", help="Force LLM narrative (requires ANTHROPIC_API_KEY)")
    p_trace.add_argument("--no-llm", action="store_true", help="Force deterministic trace, skip LLM even if key is set")
    p_trace.set_defaults(func=cmd_trace)

    p_list = sub.add_parser("list", help="List every model and its output columns")
    p_list.set_defaults(func=cmd_list)

    p_graph = sub.add_parser("graph", help="Print the full lineage graph as Mermaid")
    p_graph.set_defaults(func=cmd_graph)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
