#!/usr/bin/env python3
"""
Simple Document Persistence CLI

Provides CLI commands for all document persistence and provenance features
without complex import dependencies.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import aiohttp
import click


# Simple CLI for document persistence features
@click.group()
def cli():
    """Simple CLI for Document Persistence and Provenance System"""
    pass


# Global interpreter URL
INTERPRETER_URL = "http://localhost:5120"


async def make_request(method, endpoint, data=None):
    """Make HTTP request to interpreter service."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{INTERPRETER_URL}{endpoint}"

            if method.upper() == "GET":
                async with session.get(url, params=data) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
    except Exception as e:
        return {"error": str(e)}


def run_async(coro):
    """Helper to run async functions."""
    return asyncio.run(coro)


@cli.command()
def get_supported_formats():
    """Get supported output formats."""
    result = run_async(make_request("GET", "/outputs/formats"))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    formats = result.get("supported_formats", [])
    descriptions = result.get("format_descriptions", {})

    click.echo("📋 Supported Output Formats:")
    click.echo("-" * 30)

    for format_name in formats:
        description = descriptions.get(format_name, "No description")
        click.echo(f"✅ {format_name}: {description}")


@cli.command()
def list_workflow_templates():
    """List available workflow templates."""
    result = run_async(make_request("GET", "/workflows/templates"))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    templates = result.get("templates", {})

    click.echo("📋 Available Workflow Templates:")
    click.echo("-" * 35)

    for name, template in templates.items():
        click.echo(f"✅ {name}:")
        click.echo(f"   Description: {template.get('description', 'No description')}")
        click.echo(f"   Services: {', '.join(template.get('services', []))}")
        click.echo(f"   Outputs: {', '.join(template.get('output_types', []))}")
        click.echo()


@cli.command()
@click.argument("query")
@click.option("--format", default="json", help="Output format")
@click.option("--user-id", default="cli_user", help="User ID")
@click.option("--download", is_flag=True, help="Download the generated file")
def execute_e2e_query(query, format, user_id, download):
    """Execute end-to-end query with document generation."""
    click.echo(f"🚀 Executing E2E Query: {query}")
    click.echo(f"📄 Format: {format} | User: {user_id}")

    data = {"query": query, "output_format": format, "user_id": user_id, "filename_prefix": "cli_query"}

    result = run_async(make_request("POST", "/execute-query", data))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    if result.get("status") == "completed":
        click.echo("✅ Query executed successfully!")
        click.echo(f"✅ Execution ID: {result.get('execution_id')}")
        click.echo(f"✅ Workflow: {result.get('workflow_executed')}")

        output_info = result.get("output", {})
        if output_info:
            click.echo(f"✅ Document ID: {output_info.get('document_id')}")
            click.echo(f"✅ Format: {output_info.get('format')}")
            click.echo(f"✅ Storage: {output_info.get('storage_type')}")
            click.echo(f"✅ Persistent: {output_info.get('metadata', {}).get('persistent')}")

            if download and output_info.get("document_id"):
                click.echo("\n⬇️ Downloading document...")
                download_result = run_async(download_document_async(output_info.get("document_id")))
                if download_result:
                    click.echo(f"✅ Downloaded: {download_result}")
    else:
        click.echo(f"❌ Query failed: {result.get('error', 'Unknown error')}")


@cli.command()
@click.option("--name", required=True, help="Workflow name")
@click.option("--params", help="JSON parameters")
@click.option("--format", default="json", help="Output format")
@click.option("--user-id", default="cli_user", help="User ID")
def execute_direct_workflow(name, params, format, user_id):
    """Execute workflow directly."""
    click.echo(f"🚀 Executing Direct Workflow: {name}")

    parameters = {}
    if params:
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError:
            click.echo(f"❌ Invalid JSON parameters: {params}")
            return

    data = {
        "workflow_name": name,
        "parameters": parameters,
        "output_format": format,
        "user_id": user_id,
        "filename_prefix": "cli_direct",
    }

    result = run_async(make_request("POST", "/workflows/execute-direct", data))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    if result.get("status") == "completed":
        click.echo("✅ Workflow executed successfully!")
        click.echo(f"✅ Execution ID: {result.get('execution_id')}")

        output_info = result.get("output", {})
        if output_info:
            click.echo(f"✅ Document ID: {output_info.get('document_id')}")
            click.echo(f"✅ Format: {output_info.get('format')}")
            click.echo(f"✅ Provenance Tracked: {bool(output_info.get('provenance'))}")
    else:
        click.echo(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")


@cli.command()
@click.option("--doc-id", required=True, help="Document ID")
def get_document_provenance(doc_id):
    """Get document provenance information."""
    click.echo(f"🔍 Getting provenance for document: {doc_id}")

    result = run_async(make_request("GET", f"/documents/{doc_id}/provenance"))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    click.echo("✅ Document Provenance Retrieved:")
    click.echo("-" * 40)

    # Document Info
    doc_info = result.get("document_info", {})
    click.echo(f"📄 Title: {doc_info.get('title', 'N/A')}")
    click.echo(f"📄 Format: {doc_info.get('format', 'N/A')}")
    click.echo(f"📄 Created: {doc_info.get('created_at', 'N/A')}")
    click.echo(f"📄 Author: {doc_info.get('author', 'N/A')}")

    # Workflow Chain
    workflow_chain = result.get("workflow_chain", {})
    click.echo(f"\n🔗 Services Used: {', '.join(workflow_chain.get('services_used', []))}")

    prompts = workflow_chain.get("prompts_used", [])
    if prompts:
        click.echo(f"🔗 Prompts Used: {len(prompts)}")
        for prompt in prompts[:3]:
            click.echo(f"   • {prompt.get('action', 'Unknown')} (Step {prompt.get('step_index', 'N/A')})")

    # Quality Metrics
    quality = workflow_chain.get("quality_metrics", {})
    if quality:
        click.echo(f"🔗 Quality Score: {quality.get('confidence', 0):.2f}")
        click.echo(f"🔗 Completeness: {quality.get('completeness', 0):.2f}")


@cli.command()
@click.option("--workflow", required=True, help="Workflow name")
@click.option("--limit", default=20, help="Limit number of results")
def list_workflow_documents(workflow, limit):
    """List documents generated by a workflow."""
    click.echo(f"📚 Listing documents for workflow: {workflow}")

    result = run_async(make_request("GET", f"/documents/by-workflow/{workflow}", {"limit": limit}))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    documents = result.get("documents", [])

    if documents:
        click.echo(f"✅ Found {len(documents)} documents:")
        click.echo("-" * 50)

        for i, doc in enumerate(documents, 1):
            size_kb = doc.get("size_bytes", 0) / 1024
            click.echo(f"{i}. Document ID: {doc.get('document_id', 'N/A')}")
            click.echo(f"   Title: {doc.get('title', 'Untitled')}")
            click.echo(f"   Format: {doc.get('format', 'unknown')} | Size: {size_kb:.1f} KB")
            click.echo(f"   Created: {doc.get('created_at', 'N/A')[:19]}")
            click.echo()

        click.echo(f"💡 Use 'download-document --doc-id <ID>' to download any document")
    else:
        click.echo(f"📭 No documents found for workflow '{workflow}'")


@cli.command()
@click.option("--execution-id", required=True, help="Execution ID")
def get_execution_trace(execution_id):
    """Get execution trace information."""
    click.echo(f"🔍 Getting execution trace for: {execution_id}")

    result = run_async(make_request("GET", f"/workflows/{execution_id}/trace"))

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")
        return

    click.echo("✅ Execution Trace Retrieved:")
    click.echo("-" * 35)

    # Execution Details
    execution_details = result.get("execution_details", {})
    click.echo(f"🚀 Workflow: {execution_details.get('workflow_name', 'N/A')}")
    click.echo(f"🚀 Status: {execution_details.get('status', 'N/A')}")
    click.echo(f"🚀 User: {execution_details.get('user_id', 'N/A')}")
    click.echo(f"🚀 Started: {execution_details.get('started_at', 'N/A')}")
    click.echo(f"🚀 Execution Time: {execution_details.get('execution_time', 'N/A')}")

    # Generated Documents
    documents = result.get("generated_documents", [])
    if documents:
        click.echo(f"\n📄 Generated Documents ({len(documents)}):")
        for i, doc in enumerate(documents, 1):
            click.echo(f"  {i}. {doc.get('title', 'Untitled')} ({doc.get('format', 'unknown')})")
            click.echo(f"     ID: {doc.get('document_id', 'N/A')}")
            click.echo(f"     Size: {doc.get('size_bytes', 0) / 1024:.1f} KB")
    else:
        click.echo("\n📭 No documents generated by this execution")


@cli.command()
@click.option("--doc-id", required=True, help="Document ID")
@click.option("--save-path", help="Local save path")
def download_document(doc_id, save_path):
    """Download a document from doc_store."""
    click.echo(f"⬇️ Downloading document: {doc_id}")

    result = run_async(download_document_async(doc_id, save_path))

    if result:
        click.echo(f"✅ Downloaded: {result}")
    else:
        click.echo("❌ Download failed")


async def download_document_async(doc_id, save_path=None):
    """Async function to download document."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{INTERPRETER_URL}/documents/{doc_id}/download") as response:
                if response.status == 200:
                    # Get filename from headers or use doc_id
                    filename = doc_id
                    if "Content-Disposition" in response.headers:
                        disposition = response.headers["Content-Disposition"]
                        if "filename=" in disposition:
                            filename = disposition.split("filename=")[1].strip('"')

                    # Determine save path
                    if save_path:
                        final_path = save_path
                    else:
                        final_path = f"./{filename}"

                    # Download file
                    file_content = await response.read()

                    with open(final_path, "wb") as f:
                        f.write(file_content)

                    return final_path
                else:
                    return None
    except Exception:
        return None


if __name__ == "__main__":
    cli()
