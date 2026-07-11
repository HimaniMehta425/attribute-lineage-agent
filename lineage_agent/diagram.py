"""Exports the full lineage graph as a Mermaid flowchart (used in the README and slides)."""
from lineage_agent.graph_builder import build_graph
from lineage_agent.sql_parser import parse_all_models

LAYER_STYLE = {
    "01_raw": "fill:#e8e8e8,stroke:#888",
    "02_staging": "fill:#cfe8ff,stroke:#2b6cb0",
    "03_derived": "fill:#d5f5e3,stroke:#2f855a",
    "04_fact": "fill:#fdebd0,stroke:#b7791f",
    "05_reporting": "fill:#f3d9fa,stroke:#7d3c98",
}


def to_mermaid() -> str:
    models = parse_all_models()
    g = build_graph(models)

    lines = ["flowchart LR"]
    for name, model in models.items():
        label = name.replace("_", " ")
        lines.append(f'    {name}["{label}"]')

    for u, v in g.edges():
        lines.append(f"    {u} --> {v}")

    for name, model in models.items():
        style = LAYER_STYLE.get(model.layer, "")
        if style:
            lines.append(f"    style {name} {style}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(to_mermaid())
