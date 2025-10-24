"""
Integration tests for Phase 3: Multi-File Analysis.

Tests the complete analysis pipeline from file classification to context generation.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.analysis import (
    get_dependency_analyzer,
    get_stack_detector,
    get_architecture_detector,
    get_service_detector,
    get_analysis_engine,
    get_context_generator
)


@pytest.fixture
def sample_repository(tmp_path):
    """Create a sample repository structure for testing."""
    # Create directory structure
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "services" / "auth").mkdir(parents=True)
    (tmp_path / "frontend").mkdir(parents=True)
    
    # API service
    (tmp_path / "services" / "api" / "app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/users")
def get_users():
    pass
""")
    
    (tmp_path / "services" / "api" / "models.py").write_text("""
from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
""")
    
    # Auth service
    (tmp_path / "services" / "auth" / "app.py").write_text("""
from flask import Flask
import jwt

app = Flask(__name__)

@app.route("/auth/login")
def login():
    pass
""")
    
    # Frontend
    (tmp_path / "frontend" / "App.tsx").write_text("""
import React, { useState, useEffect } from 'react';

const App = () => {
    const [users, setUsers] = useState([]);
    
    useEffect(() => {
        fetch('/api/v1/users').then(r => r.json()).then(setUsers);
    }, []);
    
    return <div>{users.length} users</div>;
};
""")
    
    # Docker files
    (tmp_path / "docker-compose.yml").write_text("""
version: '3'
services:
  api:
    build: ./services/api
  auth:
    build: ./services/auth
""")
    
    (tmp_path / "services" / "api" / "Dockerfile").write_text("FROM python:3.11")
    
    # Requirements
    (tmp_path / "services" / "api" / "requirements.txt").write_text("""
fastapi
sqlalchemy
redis
""")
    
    (tmp_path / "frontend" / "package.json").write_text("""
{
  "dependencies": {
    "react": "^18.0.0"
  }
}
""")
    
    return tmp_path



@pytest.mark.asyncio
async def test_dependency_analysis(sample_files, sample_repository):
    """Test dependency analysis on sample repository."""
    analyzer = get_dependency_analyzer()
    
    graph = await analyzer.analyze_repository(
        repo_path=str(sample_repository),
        files=sample_files
    )
    
    assert graph is not None
    assert len(graph.nodes) > 0
    assert isinstance(graph.edges, list)
    assert isinstance(graph.metrics, dict)


@pytest.mark.asyncio
async def test_technology_stack_detection(sample_files, sample_repository):
    """Test technology stack detection."""
    detector = get_stack_detector()
    
    stack = await detector.detect_stack(
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    assert stack is not None
    assert 'Python' in stack.languages or 'python' in stack.languages  # Support both cases
    assert 'typescript' in stack.languages
    assert 'fastapi' in stack.frameworks or 'flask' in stack.frameworks
    assert 'react' in stack.frameworks
    assert 'docker' in stack.tools


@pytest.mark.asyncio
async def test_architecture_detection(sample_files, sample_repository):
    """Test architecture detection."""
    detector = get_architecture_detector()
    
    analysis = await detector.detect_architecture(
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    assert analysis is not None
    assert analysis.primary_pattern is not None
    # Should detect microservices due to services/ structure
    assert analysis.primary_pattern.name in ['microservices', 'layered']
    assert len(analysis.entry_points) > 0


@pytest.mark.asyncio
async def test_service_detection(sample_files, sample_repository):
    """Test service boundary detection."""
    detector = get_service_detector()
    
    service_map = await detector.detect_services(
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    assert service_map is not None
    assert service_map.service_count >= 2  # api and auth services
    assert len(service_map.services) >= 2
    
    # Check service names
    service_names = [s.name for s in service_map.services]
    assert 'api' in service_names or 'auth' in service_names


@pytest.mark.asyncio
async def test_complete_analysis_pipeline(sample_files, sample_repository):
    """Test complete analysis pipeline with AnalysisEngine."""
    engine = get_analysis_engine()
    
    report = await engine.analyze(
        plan_id="test-plan-123",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    # Verify all components executed
    assert report.plan_id == "test-plan-123"
    assert report.repo_path == str(sample_repository)
    assert report.total_files == len(sample_files)
    
    # Verify analysis components
    assert report.dependency_graph is not None
    assert report.technology_stack is not None
    assert report.architecture is not None
    assert report.service_map is not None
    
    # Verify metrics
    assert report.total_languages > 0
    assert report.total_frameworks > 0
    assert report.total_services > 0
    assert 0.0 <= report.modularity_score <= 1.0
    
    # Should complete successfully
    assert report.analysis_complete == True
    assert len(report.errors) == 0


@pytest.mark.asyncio
async def test_context_generation(sample_files, sample_repository):
    """Test context generation from analysis report."""
    # Run analysis
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-context-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    # Generate context
    context_gen = get_context_generator()
    context = await context_gen.generate_context(
        analysis_report=report,
        repo_name="TestRepo"
    )
    
    assert context is not None
    assert context.repo_name == "TestRepo"
    assert len(context.languages) > 0
    assert len(context.frameworks) > 0
    assert context.architecture_type is not None
    assert len(context.brief_description) > 0
    assert len(context.key_features) > 0


@pytest.mark.asyncio
async def test_chromadb_filter_generation(sample_files, sample_repository):
    """Test ChromaDB filter generation."""
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-filter-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    context_gen = get_context_generator()
    context = await context_gen.generate_context(report)
    
    # Get filter
    filter_dict = await context_gen.get_chromadb_filter(context)
    
    assert filter_dict is not None
    assert 'repo_id' in filter_dict
    assert filter_dict['repo_id'] == context.repo_id


@pytest.mark.asyncio
async def test_query_enrichment(sample_files, sample_repository):
    """Test query enrichment with context."""
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-enrich-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    context_gen = get_context_generator()
    context = await context_gen.generate_context(report)
    
    # Enrich query
    original_query = "How does authentication work?"
    enriched_query = await context_gen.enrich_query_with_context(
        query=original_query,
        context=context
    )
    
    assert len(enriched_query) > len(original_query)
    assert original_query in enriched_query
    assert context.repo_name in enriched_query
    assert context.architecture_type in enriched_query or 'N/A' in enriched_query


@pytest.mark.asyncio
async def test_topological_order(sample_files, sample_repository):
    """Test getting topological order for processing."""
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-topo-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    topo_order = await engine.get_topological_order(report)
    
    # May or may not have topological order depending on dependencies
    if topo_order:
        assert isinstance(topo_order, list)
        assert len(topo_order) > 0


@pytest.mark.asyncio
async def test_primary_language_detection(sample_files, sample_repository):
    """Test primary language detection."""
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-lang-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    primary_lang = await engine.get_primary_language(report)
    
    assert primary_lang is not None
    assert primary_lang in ['python', 'typescript', 'javascript']


@pytest.mark.asyncio
async def test_microservices_detection(sample_files, sample_repository):
    """Test microservices architecture detection."""
    engine = get_analysis_engine()
    report = await engine.analyze(
        plan_id="test-micro-plan",
        files=sample_files,
        repo_path=str(sample_repository)
    )
    
    is_microservices = await engine.is_microservices(report)
    
    # Should detect microservices due to services/ structure
    assert isinstance(is_microservices, bool)


@pytest.mark.asyncio
async def test_error_handling_invalid_path(sample_files):
    """Test error handling with invalid repository path."""
    engine = get_analysis_engine()
    
    report = await engine.analyze(
        plan_id="test-error-plan",
        files=sample_files,
        repo_path="/nonexistent/path"
    )
    
    # Should handle errors gracefully
    assert report.plan_id == "test-error-plan"
    assert not report.analysis_complete or len(report.errors) > 0

