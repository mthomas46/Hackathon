#!/usr/bin/env python3
"""Populate Prompt Store with comprehensive test data.

Creates realistic prompts, A/B tests, analytics data, and relationships
for testing the new domain-driven architecture.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.prompt_store.db.schema import init_database
from services.prompt_store.core.entities import (
    Prompt, PromptVersion, ABTest, PromptUsage, PromptRelationship, BulkOperation
)
from services.prompt_store.domain.prompts.repository import PromptRepository
from services.prompt_store.domain.prompts.versioning_repository import PromptVersioningRepository


def create_sample_prompts():
    """Create a diverse set of sample prompts."""
    prompts_data = [
        # Code-related prompts
        {
            "name": "python_function",
            "category": "code",
            "description": "Generate Python functions with proper documentation",
            "content": """Write a Python function called {{function_name}} that {{description}}.

Requirements:
- Include comprehensive docstring with parameters and return value
- Add type hints for all parameters and return value
- Handle edge cases and input validation
- Include at least 2 test cases as comments

Function signature: {{function_name}}({{parameters}}) -> {{return_type}}""",
            "variables": ["function_name", "description", "parameters", "return_type"],
            "tags": ["python", "functions", "documentation", "type_hints"],
            "is_template": True,
            "created_by": "test_user_1"
        },
        {
            "name": "sql_query_optimizer",
            "category": "code",
            "description": "Optimize SQL queries for better performance",
            "content": """Analyze and optimize the following SQL query for better performance:

{{sql_query}}

Provide:
1. The optimized query
2. Explanation of improvements made
3. Expected performance gains
4. Any additional indexes that might help""",
            "variables": ["sql_query"],
            "tags": ["sql", "optimization", "performance", "database"],
            "is_template": True,
            "created_by": "test_user_2"
        },

        # Writing prompts
        {
            "name": "blog_post_outline",
            "category": "writing",
            "description": "Create a comprehensive blog post outline",
            "content": """Create a detailed outline for a blog post about {{topic}}.

Include:
- Compelling headline
- Introduction hook
- 5-7 main sections with subpoints
- Key takeaways
- Call-to-action

Target audience: {{audience}}
Word count goal: {{word_count}}""",
            "variables": ["topic", "audience", "word_count"],
            "tags": ["blogging", "content_creation", "outlining", "seo"],
            "is_template": True,
            "created_by": "test_user_3"
        },
        {
            "name": "email_sequence",
            "category": "writing",
            "description": "Design an email marketing sequence",
            "content": """Design a {{sequence_length}}-email sequence for {{product_service}}.

Sequence goals: {{goals}}

For each email, provide:
- Subject line
- Key message
- Call-to-action
- Send timing

Make it {{tone}} and focused on {{target_audience}}.""",
            "variables": ["sequence_length", "product_service", "goals", "tone", "target_audience"],
            "tags": ["email_marketing", "sequences", "copywriting", "marketing"],
            "is_template": True,
            "created_by": "test_user_4"
        },

        # Analysis prompts
        {
            "name": "data_analysis_report",
            "category": "analysis",
            "description": "Generate comprehensive data analysis reports",
            "content": """Analyze the following dataset and provide insights:

Dataset: {{dataset_description}}
Key metrics: {{key_metrics}}
Time period: {{time_period}}

Deliverables:
1. Executive summary
2. Key findings and trends
3. Data visualizations needed
4. Recommendations
5. Next steps

Focus on {{focus_areas}} and provide actionable insights.""",
            "variables": ["dataset_description", "key_metrics", "time_period", "focus_areas"],
            "tags": ["data_analysis", "reporting", "insights", "visualization"],
            "is_template": True,
            "created_by": "test_user_5"
        },

        # AI/ML prompts
        {
            "name": "model_evaluation",
            "category": "ai_ml",
            "description": "Evaluate machine learning model performance",
            "content": """Evaluate the performance of {{model_type}} for {{use_case}}.

Model details:
- Algorithm: {{algorithm}}
- Training data size: {{data_size}}
- Key features: {{features}}

Evaluation criteria:
- Accuracy metrics
- Performance benchmarks
- Bias and fairness assessment
- Scalability considerations

Provide recommendations for improvement and deployment readiness.""",
            "variables": ["model_type", "use_case", "algorithm", "data_size", "features"],
            "tags": ["machine_learning", "evaluation", "performance", "deployment"],
            "is_template": True,
            "created_by": "test_user_1"
        },

        # Business prompts
        {
            "name": "business_plan_section",
            "category": "business",
            "description": "Write business plan sections",
            "content": """Write the {{section_name}} section for a business plan.

Business: {{business_description}}
Target market: {{target_market}}
Competitive advantage: {{competitive_advantage}}

Make it {{tone}} and focused on convincing {{audience_type}} investors/partners.""",
            "variables": ["section_name", "business_description", "target_market", "competitive_advantage", "tone", "audience_type"],
            "tags": ["business_planning", "entrepreneurship", "strategy", "finance"],
            "is_template": True,
            "created_by": "test_user_2"
        }
    ]

    return prompts_data


def create_ab_tests_data(prompts):
    """Create sample A/B test configurations."""
    ab_tests_data = [
        {
            "name": "python_function_docs_test",
            "description": "Test different documentation styles for Python functions",
            "prompt_a_id": next(p.id for p in prompts if p.name == "python_function"),
            "prompt_b_id": next(p.id for p in prompts if p.name == "python_function"),  # Same prompt for demo
            "test_metric": "response_quality",
            "traffic_split": 0.5,
            "created_by": "test_user_1"
        },
        {
            "name": "blog_post_engagement_test",
            "description": "Test different blog post outline structures",
            "prompt_a_id": next(p.id for p in prompts if p.name == "blog_post_outline"),
            "prompt_b_id": next(p.id for p in prompts if p.name == "blog_post_outline"),
            "test_metric": "user_satisfaction",
            "traffic_split": 0.6,
            "created_by": "test_user_3"
        }
    ]

    return ab_tests_data


def create_usage_data(prompts):
    """Create sample usage analytics data."""
    usage_data = []
    now = datetime.now(timezone.utc)

    for prompt in prompts:
        # Generate 10-50 usage records per prompt
        num_records = random.randint(10, 50)

        for i in range(num_records):
            # Random timestamp within last 30 days
            timestamp = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

            usage = {
                "prompt_id": prompt.id,
                "session_id": f"session_{random.randint(1, 100)}",
                "user_id": f"user_{random.randint(1, 20)}",
                "service_name": random.choice(["web_app", "api", "cli", "mobile"]),
                "operation": "generate",
                "input_tokens": random.randint(10, 500),
                "output_tokens": random.randint(50, 2000),
                "response_time_ms": random.randint(100, 5000),
                "success": random.choices([True, False], weights=[0.95, 0.05])[0],
                "created_at": timestamp
            }

            # Add some error messages for failed requests
            if not usage["success"]:
                usage["error_message"] = random.choice([
                    "Template variable missing",
                    "Invalid input format",
                    "Rate limit exceeded",
                    "Internal server error"
                ])

            usage_data.append(usage)

    return usage_data


def create_relationships_data(prompts):
    """Create sample prompt relationships."""
    relationships_data = []

    # Group prompts by category
    categories = {}
    for prompt in prompts:
        if prompt.category not in categories:
            categories[prompt.category] = []
        categories[prompt.category].append(prompt)

    # Create relationships within categories
    for category, category_prompts in categories.items():
        if len(category_prompts) > 1:
            for i, prompt in enumerate(category_prompts):
                # Connect to 1-2 related prompts in same category
                num_connections = min(random.randint(1, 2), len(category_prompts) - 1)
                connected_indices = random.sample([j for j in range(len(category_prompts)) if j != i], num_connections)

                for target_idx in connected_indices:
                    target_prompt = category_prompts[target_idx]
                    relationship = {
                        "source_prompt_id": prompt.id,
                        "target_prompt_id": target_prompt.id,
                        "relationship_type": random.choice(["similar", "extends", "references", "alternative"]),
                        "strength": random.uniform(0.3, 0.9),
                        "metadata": {"auto_generated": True, "confidence": random.uniform(0.7, 0.95)},
                        "created_by": "system"
                    }
                    relationships_data.append(relationship)

    # Create some cross-category relationships
    all_prompts = list(prompts)
    for _ in range(min(10, len(all_prompts))):  # Add up to 10 cross-category relationships
        source_idx, target_idx = random.sample(range(len(all_prompts)), 2)
        source_prompt = all_prompts[source_idx]
        target_prompt = all_prompts[target_idx]

        # Only create relationship if they're in different categories
        if source_prompt.category != target_prompt.category:
            relationship = {
                "source_prompt_id": source_prompt.id,
                "target_prompt_id": target_prompt.id,
                "relationship_type": "inspiration",
                "strength": random.uniform(0.1, 0.4),
                "metadata": {"cross_category": True, "inspirational": True},
                "created_by": "system"
            }
            relationships_data.append(relationship)

    return relationships_data


def populate_test_data(seed_realistic: bool = True):
    """Populate the database with comprehensive test data."""

    print("🚀 Initializing Prompt Store database...")
    init_database()

    print("📝 Creating sample prompts...")

    # Create prompts
    prompts_data = create_sample_prompts()
    prompts = []

    prompt_repo = PromptRepository()
    for prompt_data in prompts_data:
        prompt = Prompt(
            name=prompt_data["name"],
            category=prompt_data["category"],
            description=prompt_data["description"],
            content=prompt_data["content"],
            variables=prompt_data["variables"],
            tags=prompt_data["tags"],
            is_template=prompt_data["is_template"],
            created_by=prompt_data["created_by"],
            performance_score=random.uniform(0.6, 0.95),
            usage_count=random.randint(0, 100)
        )
        saved_prompt = prompt_repo.save(prompt)
        prompts.append(saved_prompt)

    print(f"✅ Created {len(prompts)} prompts")

    # Create prompt versions (simulate evolution)
    print("📝 Creating prompt versions...")
    version_repo = PromptVersioningRepository()
    versions_created = 0

    for prompt in prompts:
        # Create 1-3 versions for some prompts
        num_versions = random.randint(0, 3)
        for version_num in range(2, num_versions + 2):
            # Simulate content changes
            modified_content = prompt.content
            if "{{function_name}}" in modified_content:
                modified_content = modified_content.replace("{{function_name}}", "{{func_name}}")

            version = PromptVersion(
                prompt_id=prompt.id,
                version=version_num,
                content=modified_content,
                variables=prompt.variables,
                change_summary=f"Version {version_num} improvements",
                change_type="update",
                created_by=prompt.created_by
            )
            version_repo.save(version)
            versions_created += 1

    print(f"✅ Created {versions_created} prompt versions")

    # Create A/B tests
    print("📝 Creating A/B tests...")
    from services.prompt_store.domain.ab_testing.repository import ABTestRepository

    ab_tests_data = create_ab_tests_data(prompts)
    ab_tests = []

    ab_test_repo = ABTestRepository()
    for test_data in ab_tests_data:
        ab_test = ABTest(
            name=test_data["name"],
            description=test_data["description"],
            prompt_a_id=test_data["prompt_a_id"],
            prompt_b_id=test_data["prompt_b_id"],
            test_metric=test_data["test_metric"],
            traffic_split=test_data["traffic_split"],
            created_by=test_data["created_by"]
        )
        saved_test = ab_test_repo.save(ab_test)
        ab_tests.append(saved_test)

    print(f"✅ Created {len(ab_tests)} A/B tests")

    # Create usage data
    print("📝 Creating usage analytics...")
    from services.prompt_store.domain.analytics.repository import AnalyticsRepository

    usage_data = create_usage_data(prompts)
    usage_repo = AnalyticsRepository()

    for usage_item in usage_data:
        usage = PromptUsage(
            prompt_id=usage_item["prompt_id"],
            session_id=usage_item["session_id"],
            user_id=usage_item["user_id"],
            service_name=usage_item["service_name"],
            operation=usage_item["operation"],
            input_tokens=usage_item["input_tokens"],
            output_tokens=usage_item["output_tokens"],
            response_time_ms=usage_item["response_time_ms"],
            success=usage_item["success"],
            error_message=usage_item.get("error_message"),
            created_at=usage_item["created_at"]
        )
        usage_repo.save(usage)

    print(f"✅ Created {len(usage_data)} usage records")

    # Create relationships
    print("📝 Creating prompt relationships...")
    from services.prompt_store.domain.relationships.repository import RelationshipRepository

    relationships_data = create_relationships_data(prompts)
    relationship_repo = RelationshipRepository()

    for rel_data in relationships_data:
        relationship = PromptRelationship(
            source_prompt_id=rel_data["source_prompt_id"],
            target_prompt_id=rel_data["target_prompt_id"],
            relationship_type=rel_data["relationship_type"],
            strength=rel_data["strength"],
            metadata=rel_data["metadata"],
            created_by=rel_data["created_by"]
        )
        relationship_repo.save(relationship)

    print(f"✅ Created {len(relationships_data)} prompt relationships")

    # Create bulk operations (simulate some completed operations)
    print("📝 Creating bulk operation history...")
    from services.prompt_store.domain.bulk.repository import BulkOperationRepository

    bulk_operations_data = [
        {
            "operation_type": "update_prompts",
            "status": "completed",
            "total_items": 5,
            "processed_items": 5,
            "successful_items": 4,
            "failed_items": 1,
            "errors": ["Failed to update prompt xyz: validation error"],
            "metadata": {"update_type": "tags", "new_tags": ["test", "updated"]},
            "results": [
                {"prompt_id": "success_1", "status": "success"},
                {"prompt_id": "success_2", "status": "success"},
                {"prompt_id": "success_3", "status": "success"},
                {"prompt_id": "success_4", "status": "success"},
                {"prompt_id": "failed_1", "status": "failed", "error": "validation error"}
            ],
            "created_by": "test_user_1",
            "completed_at": datetime.now(timezone.utc) - timedelta(hours=2)
        },
        {
            "operation_type": "create_prompts",
            "status": "completed",
            "total_items": 3,
            "processed_items": 3,
            "successful_items": 3,
            "failed_items": 0,
            "errors": [],
            "metadata": {"source": "yaml_import", "category": "imported"},
            "results": [
                {"prompt_id": "new_1", "status": "success"},
                {"prompt_id": "new_2", "status": "success"},
                {"prompt_id": "new_3", "status": "success"}
            ],
            "created_by": "test_user_2",
            "completed_at": datetime.now(timezone.utc) - timedelta(hours=4)
        }
    ]

    bulk_repo = BulkOperationRepository()
    for bulk_data in bulk_operations_data:
        bulk_op = BulkOperation(
            operation_type=bulk_data["operation_type"],
            status=bulk_data["status"],
            total_items=bulk_data["total_items"],
            processed_items=bulk_data["processed_items"],
            successful_items=bulk_data["successful_items"],
            failed_items=bulk_data["failed_items"],
            errors=bulk_data["errors"],
            metadata=bulk_data["metadata"],
            results=bulk_data["results"],
            created_by=bulk_data["created_by"],
            completed_at=bulk_data["completed_at"]
        )
        bulk_repo.save(bulk_op)

    print(f"✅ Created {len(bulk_operations_data)} bulk operations")

    print("\n🎉 Prompt Store test data population completed!")
    print(f"   📊 Prompts: {len(prompts)}")
    print(f"   📈 Versions: {versions_created}")
    print(f"   🧪 A/B Tests: {len(ab_tests)}")
    print(f"   📈 Usage Records: {len(usage_data)}")
    print(f"   🔗 Relationships: {len(relationships_data)}")
    print(f"   📦 Bulk Operations: {len(bulk_operations_data)}")
    print("\n🚀 Ready for testing the new domain-driven architecture!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate Prompt Store with test data")
    parser.add_argument("--seed", action="store_true", help="Populate with realistic test data")

    args = parser.parse_args()

    if args.seed:
        populate_test_data()
    else:
        print("Use --seed flag to populate with test data")
        print("Example: python scripts/populate_promptstore_test_data.py --seed")
