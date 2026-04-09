#!/usr/bin/env python3
"""
Knowledge Graph Example for PropWeaver

Demonstrates how to model and query a knowledge graph with programming languages,
frameworks, and their relationships.
"""

import sys
from pathlib import Path

# Add src to Python path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from propweaver import PropertyGraph


def main():
    """Knowledge graph example with languages and frameworks"""
    print("=== Knowledge Graph Example ===\n")

    with PropertyGraph() as graph:  # Use in-memory for examples
        # Create programming languages
        print("Creating programming languages...")
        python = graph.add_node("Language", name="Python", year=1991, paradigm="multi-paradigm")
        javascript = graph.add_node(
            "Language", name="JavaScript", year=1995, paradigm="multi-paradigm"
        )
        java = graph.add_node("Language", name="Java", year=1995, paradigm="object-oriented")
        rust = graph.add_node("Language", name="Rust", year=2010, paradigm="systems")

        print(f"✅ Created 4 programming languages")

        # Create frameworks and libraries
        print("\nCreating frameworks...")
        django = graph.add_node(
            "Framework", name="Django", language="Python", type="web", year=2005
        )
        flask = graph.add_node("Framework", name="Flask", language="Python", type="web", year=2010)
        react = graph.add_node(
            "Framework", name="React", language="JavaScript", type="frontend", year=2013
        )
        spring = graph.add_node(
            "Framework", name="Spring", language="Java", type="enterprise", year=2003
        )
        actix = graph.add_node("Framework", name="Actix", language="Rust", type="web", year=2018)

        print(f"✅ Created 5 frameworks")

        # Create relationships
        print("\nCreating relationships...")
        graph.add_edge(python, "HAS_FRAMEWORK", django, popularity="high", maturity="stable")
        graph.add_edge(python, "HAS_FRAMEWORK", flask, popularity="high", maturity="stable")
        graph.add_edge(
            javascript, "HAS_FRAMEWORK", react, popularity="very_high", maturity="stable"
        )
        graph.add_edge(java, "HAS_FRAMEWORK", spring, popularity="high", maturity="stable")
        graph.add_edge(rust, "HAS_FRAMEWORK", actix, popularity="medium", maturity="growing")

        # Create some cross-language influences
        graph.add_edge(python, "INFLUENCES", javascript, aspect="syntax_flexibility")
        graph.add_edge(rust, "INFLUENCES", python, aspect="memory_safety_ideas")

        print(f"✅ Created relationships")

        # Query examples
        print("\n=== Query Examples ===")

        # Find all languages created in the 1990s
        nineties_languages = [
            lang for lang in graph.nodes("Language") if 1990 <= lang.props["year"] < 2000
        ]
        print(f"\nLanguages from the 1990s: {len(nineties_languages)}")
        for lang in nineties_languages:
            print(f"  - {lang.props['name']} ({lang.props['year']})")

        # Find all web frameworks
        web_frameworks = list(graph.nodes("Framework", type="web"))
        print(f"\nWeb frameworks: {len(web_frameworks)}")
        for framework in web_frameworks:
            print(f"  - {framework.props['name']} ({framework.props['language']})")

        # Find frameworks for Python
        python_frameworks = []
        for edge in graph.edges("HAS_FRAMEWORK"):
            if edge.src_id == python.node_id:
                # Find the framework node by ID
                for framework in graph.nodes("Framework"):
                    if framework.node_id == edge.dst_id:
                        python_frameworks.append(framework.props["name"])
                        break

        print(f"\nPython frameworks: {len(python_frameworks)}")
        for framework in python_frameworks:
            print(f"  - {framework}")

        # Find high popularity relationships
        high_pop_edges = [
            e
            for e in graph.edges("HAS_FRAMEWORK")
            if e.props["popularity"] in ["high", "very_high"]
        ]
        print(f"\nHigh popularity frameworks: {len(high_pop_edges)}")

        # Show property management examples
        print("\n=== Property Management Examples ===")
        python.props["temp_note"] = "Under review"
        print(f"Python has {len(python.props)} properties: {list(python.props.keys())}")

        # Clean up temporary data
        del python.props["temp_note"]
        print(f"After cleanup: {len(python.props)} properties")

        # Set graph metadata
        graph.props.update(
            {
                "domain": "programming",
                "total_concepts": graph.node_count(),
                "example_version": "2.0",
            }
        )

        print(f"\n✅ Knowledge graph example completed!")
        print(f"Graph covers {graph.props['total_concepts']} programming concepts")


if __name__ == "__main__":
    main()
