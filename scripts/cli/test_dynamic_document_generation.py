import json
import sys

sys.path.insert(0, ".")
from services.interpreter.main import _generate_dynamic_documents


def main():
    # Example query/context for diversity
    query = "Generate all docs"
    context = {"project_type": "ecommerce", "tech_stack": "React/Node.js", "query_id": "testquery1234"}
    docs = _generate_dynamic_documents(query, context)
    print(
        json.dumps(
            {"count": len(docs), "titles": [d["title"] for d in docs], "types": list(set(d["type"] for d in docs))},
            indent=2,
        )
    )
    # Optionally print a sample doc for inspection
    print("\nSample document:\n", json.dumps(docs[0], indent=2))


if __name__ == "__main__":
    main()
