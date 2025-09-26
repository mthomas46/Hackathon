#!/usr/bin/env python3
"""
Script to run comprehensive audits on all services and generate a todo list.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any

def get_kebab_case_services() -> List[str]:
    """Get all services that are already in kebab-case format."""
    services_dir = Path("/Users/mykalthomas/Documents/work/Hackathon/services")
    services = []

    for item in services_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in ['__pycache__', '_template']:
            # Check if it follows kebab-case pattern
            import re
            if re.match(r'^[a-z][a-z0-9-]*$', item.name):
                services.append(item.name)

    return sorted(services)

def run_audit(service_name: str) -> Dict[str, Any]:
    """Run audit on a single service and return results."""
    try:
        cmd = [
            "python3", "scripts/audit-framework/audit_cli.py",
            "audit", "--service", service_name, "--output", "json"
        ]

        result = subprocess.run(
            cmd,
            cwd="/Users/mykalthomas/Documents/work/Hackathon",
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Failed to audit {service_name}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error auditing {service_name}: {e}")
        return None

def analyze_audit_results(results: Dict[str, Any]) -> List[str]:
    """Analyze audit results and generate specific improvement tasks."""
    service_name = results['service_name']
    tasks = []

    # Overall score analysis
    overall_score = results['overall_score']
    grade = results['grade']

    if overall_score < 70:
        tasks.append(f"🚨 CRITICAL: {service_name} has failing audit score ({overall_score:.1f} - {grade}) - requires immediate attention")
    elif overall_score < 80:
        tasks.append(f"⚠️  HIGH PRIORITY: Improve {service_name} overall score from {overall_score:.1f} to target 80+")

    # Dimension-specific analysis
    dimensions = results['dimensions']

    # Architecture issues
    if dimensions['architecture'] < 80:
        tasks.append(f"🏗️  ARCHITECTURE: Improve {service_name} architecture score ({dimensions['architecture']:.1f}) - focus on DDD compliance and REST API design")

    # Code quality issues
    if dimensions['code_quality'] < 70:
        tasks.append(f"💻 CODE QUALITY: Address {service_name} code quality issues ({dimensions['code_quality']:.1f}) - complexity, testing, linting")

    # Performance issues
    if dimensions['performance'] < 75:
        tasks.append(f"⚡ PERFORMANCE: Optimize {service_name} performance ({dimensions['performance']:.1f}) - resource usage and response times")

    # Maintainability issues
    if dimensions['maintainability'] < 75:
        tasks.append(f"🔧 MAINTAINABILITY: Improve {service_name} maintainability ({dimensions['maintainability']:.1f}) - documentation and code organization")

    # Specific recommendations
    recommendations = results.get('recommendations', [])
    for rec in recommendations[:3]:  # Top 3 recommendations
        tasks.append(f"📋 {service_name}: {rec}")

    # Critical issues
    critical_count = results.get('critical_issues_count', 0)
    if critical_count > 0:
        tasks.append(f"🚨 CRITICAL ISSUES: {service_name} has {critical_count} critical issues requiring immediate fixes")

    return tasks

def main():
    """Main function to run all audits and generate comprehensive todo list."""
    print("🔍 Discovering services in kebab-case format...")
    services = get_kebab_case_services()
    print(f"Found {len(services)} services: {', '.join(services)}")

    all_results = {}
    all_tasks = []

    print("\n🏃 Running comprehensive audits...")
    for service in services:
        print(f"  Auditing {service}...")
        results = run_audit(service)

        if results:
            all_results[service] = results
            tasks = analyze_audit_results(results)
            all_tasks.extend(tasks)

            # Save individual results
            with open(f"audit_{service}.json", 'w') as f:
                json.dump(results, f, indent=2)

    # Generate comprehensive todo list
    print(f"\n📊 Audit Summary:")
    print(f"  Services audited: {len(all_results)}")
    print(f"  Total improvement tasks: {len(all_tasks)}")

    # Group tasks by priority
    critical_tasks = [t for t in all_tasks if t.startswith("🚨 CRITICAL")]
    high_priority = [t for t in all_tasks if t.startswith("⚠️  HIGH PRIORITY") or "CRITICAL ISSUES" in t]
    architecture_tasks = [t for t in all_tasks if "🏗️  ARCHITECTURE" in t]
    code_quality_tasks = [t for t in all_tasks if "💻 CODE QUALITY" in t]
    performance_tasks = [t for t in all_tasks if "⚡ PERFORMANCE" in t]
    maintainability_tasks = [t for t in all_tasks if "🔧 MAINTAINABILITY" in t]
    specific_tasks = [t for t in all_tasks if "📋" in t]

    # Create the todo list
    todo_data = {
        "merge": False,
        "todos": []
    }

    # Add critical issues first
    for task in critical_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"critical_{len(todo_data['todos'])}"
        })

    # Add high priority tasks
    for task in high_priority:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"high_priority_{len(todo_data['todos'])}"
        })

    # Add architecture improvements
    for task in architecture_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"architecture_{len(todo_data['todos'])}"
        })

    # Add code quality improvements
    for task in code_quality_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"code_quality_{len(todo_data['todos'])}"
        })

    # Add performance optimizations
    for task in performance_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"performance_{len(todo_data['todos'])}"
        })

    # Add maintainability improvements
    for task in maintainability_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"maintainability_{len(todo_data['todos'])}"
        })

    # Add specific recommendations
    for task in specific_tasks:
        todo_data["todos"].append({
            "content": task,
            "status": "pending",
            "id": f"specific_{len(todo_data['todos'])}"
        })

    print(f"\n✅ Created comprehensive todo list with {len(todo_data['todos'])} tasks")
    return todo_data

if __name__ == "__main__":
    todo_data = main()
