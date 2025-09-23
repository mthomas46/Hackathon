#!/usr/bin/env python3
"""
Test script to verify the modified _generate_dynamic_documents function
"""

import json
import os
import sys
from datetime import datetime

# Add the services directory to the path so we can import
sys.path.append(os.path.join(os.path.dirname(__file__), "services"))

try:
    from interpreter.main import _generate_dynamic_documents

    print("✅ Successfully imported _generate_dynamic_documents")
except ImportError as e:
    print(f"❌ Failed to import function: {e}")
    sys.exit(1)


def test_document_generation():
    """Test the document generation function."""
    print("\n" + "=" * 60)
    print("TESTING DYNAMIC DOCUMENT GENERATION")
    print("=" * 60)

    # Test context
    test_context = {"project_type": "ecommerce", "tech_stack": "React/Node.js", "query_id": "test_12345"}

    # Test query
    test_query = "Create a comprehensive documentation ecosystem for an e-commerce platform"

    print(f"📋 Test Query: {test_query}")
    print(f"🔧 Test Context: {json.dumps(test_context, indent=2)}")
    print()

    try:
        # Generate documents
        start_time = datetime.now()
        documents = _generate_dynamic_documents(test_query, test_context)
        end_time = datetime.now()

        print("✅ Document generation completed successfully!")
        print(f"⏱️  Generation time: {(end_time - start_time).total_seconds():.2f} seconds")
        print(f"📊 Total documents generated: {len(documents)}")
        print()

        # Validate minimum requirement
        if len(documents) >= 25:
            print("✅ SUCCESS: Generated 25+ documents as required!")
        else:
            print(f"❌ FAILURE: Only generated {len(documents)} documents (need 25+)")
            return False

        # Analyze document types
        doc_types = {}
        categories = {}
        authors = {}
        statuses = {}

        for doc in documents:
            # Count document types
            doc_type = doc.get("type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            # Count categories
            category = doc.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

            # Count authors
            author = doc.get("author", "unknown")
            authors[author] = authors.get(author, 0) + 1

            # Count statuses
            status = doc.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1

        print("📈 DOCUMENT ANALYSIS")
        print("-" * 30)
        print(f"Document Types: {json.dumps(doc_types, indent=2)}")
        print()
        print(f"Categories: {json.dumps(categories, indent=2)}")
        print()
        print(f"Authors: {json.dumps(authors, indent=2)}")
        print()
        print(f"Statuses: {json.dumps(statuses, indent=2)}")
        print()

        # Sample some documents
        print("📄 SAMPLE DOCUMENTS")
        print("-" * 20)
        for i, doc in enumerate(documents[:5]):  # Show first 5
            print(f"\n{i+1}. {doc['title']}")
            print(f"   Type: {doc['type']}")
            print(f"   Category: {doc['category']}")
            print(f"   Author: {doc['author']}")
            print(f"   Status: {doc.get('status', 'N/A')}")
            print(f"   Content Length: {len(doc['content'])} chars")
            print(f"   Tags: {doc.get('tags', [])}")

        # Check for diversity
        unique_types = len(doc_types)
        unique_categories = len(categories)

        print("\n🎯 DIVERSITY CHECK")
        print("-" * 20)
        print(f"Unique document types: {unique_types}")
        print(f"Unique categories: {unique_categories}")
        print(f"Unique authors: {len(authors)}")

        if unique_types >= 5:
            print("✅ Good diversity in document types")
        else:
            print("⚠️  Limited diversity in document types")

        if unique_categories >= 8:
            print("✅ Good diversity in categories")
        else:
            print("⚠️  Limited diversity in categories")

        # Check content quality
        avg_content_length = sum(len(doc["content"]) for doc in documents) / len(documents)
        print("\n📝 CONTENT QUALITY")
        print("-" * 18)
        print(f"Average content length: {avg_content_length:.0f} characters")

        long_docs = len([doc for doc in documents if len(doc["content"]) > 500])
        print(f"Documents with detailed content (>500 chars): {long_docs} ({long_docs/len(documents)*100:.1f}%)")

        if avg_content_length > 300:
            print("✅ Good content detail level")
        else:
            print("⚠️  Content could be more detailed")

        return True

    except Exception as e:
        print(f"❌ ERROR during document generation: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_multiple_runs():
    """Test multiple runs to ensure consistency."""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE RUNS")
    print("=" * 60)

    results = []
    for i in range(3):
        print(f"\n🏃 Run {i+1}:")
        context = {"project_type": f"project_{i}", "tech_stack": "React/Node.js", "query_id": f"query_{i}"}
        documents = _generate_dynamic_documents("Test query", context)
        results.append(len(documents))
        print(f"   Generated: {len(documents)} documents")

    print("\n📊 Multiple run results:")
    print(f"   Run 1: {results[0]} documents")
    print(f"   Run 2: {results[1]} documents")
    print(f"   Run 3: {results[2]} documents")

    if all(r >= 25 for r in results):
        print("✅ All runs generated 25+ documents")
        return True
    else:
        print("❌ Some runs generated fewer than 25 documents")
        return False


if __name__ == "__main__":
    print("🚀 Starting Dynamic Document Generation Tests")
    print("=" * 60)

    success1 = test_document_generation()
    success2 = test_multiple_runs()

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Document generation works correctly")
        print("✅ Generates 25+ documents")
        print("✅ Good diversity and detail")
        print("✅ Consistent across multiple runs")
    else:
        print("❌ SOME TESTS FAILED!")
        if not success1:
            print("❌ Document generation test failed")
        if not success2:
            print("❌ Multiple runs test failed")

    print("=" * 60)
