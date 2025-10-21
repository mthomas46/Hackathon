"""
Unit tests for TechnologyStackDetector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.services.analysis.stack_detector import (
    TechnologyStackDetector,
    TechnologyStack,
    get_stack_detector
)


@pytest.fixture
def detector():
    """Create detector instance."""
    return TechnologyStackDetector()


@pytest.fixture
def sample_files():
    """Sample file list."""
    return [
        {
            'path': 'src/main.py',
            'language': 'python',
            'is_code': True
        },
        {
            'path': 'src/api.py',
            'language': 'python',
            'is_code': True
        },
        {
            'path': 'frontend/App.tsx',
            'language': 'typescript',
            'is_code': True
        },
        {
            'path': 'docker-compose.yml',
            'language': 'yaml',
            'is_code': False
        },
        {
            'path': 'package.json',
            'language': 'json',
            'is_code': False
        }
    ]


@pytest.mark.asyncio
async def test_detect_stack_basic(detector, sample_files, tmp_path):
    """Test basic stack detection."""
    # Create test files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("from fastapi import FastAPI\nimport redis")
    (tmp_path / "src" / "api.py").write_text("import sqlalchemy")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "App.tsx").write_text("import React from 'react'")
    
    # Update file paths
    for f in sample_files:
        f['path'] = str(tmp_path / f['path'])
    
    stack = await detector.detect_stack(sample_files, str(tmp_path))
    
    assert isinstance(stack, TechnologyStack)
    assert 'Python' in stack.languages or 'python' in stack.languages  # Support both cases
    assert 'typescript' in stack.languages
    assert len(stack.frameworks) > 0


@pytest.mark.asyncio
async def test_detect_frameworks_python(detector, tmp_path):
    """Test Python framework detection."""
    files = [
        {'path': str(tmp_path / 'app.py'), 'language': 'python', 'is_code': True}
    ]
    
    (tmp_path / "app.py").write_text("""
from fastapi import FastAPI
from flask import Flask
import sqlalchemy
from pydantic import BaseModel
""")
    
    stack = await detector.detect_stack(files, str(tmp_path))
    
    assert 'fastapi' in stack.frameworks
    assert 'flask' in stack.frameworks
    assert 'sqlalchemy' in stack.frameworks
    assert 'pydantic' in stack.frameworks


@pytest.mark.asyncio
async def test_detect_frameworks_javascript(detector, tmp_path):
    """Test JavaScript framework detection."""
    files = [
        {'path': str(tmp_path / 'index.js'), 'language': 'javascript', 'is_code': True}
    ]
    
    (tmp_path / "index.js").write_text("""
import React from 'react';
import { useState, useEffect } from 'react';
const express = require('express');
""")
    
    stack = await detector.detect_stack(files, str(tmp_path))
    
    assert 'react' in stack.frameworks
    assert 'express' in stack.frameworks


@pytest.mark.asyncio
async def test_detect_databases(detector, tmp_path):
    """Test database detection."""
    files = [
        {'path': str(tmp_path / 'db.py'), 'language': 'python', 'is_code': True}
    ]
    
    (tmp_path / "db.py").write_text("""
import psycopg2
import redis
from pymongo import MongoClient
""")
    
    stack = await detector.detect_stack(files, str(tmp_path))
    
    assert 'postgresql' in stack.databases
    assert 'redis' in stack.databases
    assert 'mongodb' in stack.databases


@pytest.mark.asyncio
async def test_detect_tools(detector, sample_files):
    """Test tool detection from file names."""
    files = sample_files + [
        {'path': 'Dockerfile', 'language': 'dockerfile', 'is_code': False},
        {'path': 'requirements.txt', 'language': 'text', 'is_code': False},
        {'path': '.gitignore', 'language': 'text', 'is_code': False}
    ]
    
    stack = await detector.detect_stack(files, '/tmp')
    
    assert 'docker' in stack.tools
    assert 'pip' in stack.tools
    assert 'git' in stack.tools


@pytest.mark.asyncio
async def test_detect_deployment_platforms(detector, tmp_path):
    """Test deployment platform detection."""
    files = [
        {'path': str(tmp_path / 'deploy.py'), 'language': 'python', 'is_code': True}
    ]
    
    (tmp_path / "deploy.py").write_text("""
import boto3
from google.cloud import storage
import azure.storage
""")
    
    stack = await detector.detect_stack(files, str(tmp_path))
    
    assert 'aws' in stack.deployment
    assert 'gcp' in stack.deployment
    assert 'azure' in stack.deployment


@pytest.mark.asyncio
async def test_get_primary_language(detector):
    """Test primary language detection."""
    stack = TechnologyStack(
        languages={'python': 100, 'javascript': 30, 'go': 10},
        frameworks={},
        databases=[],
        tools=[],
        deployment=[],
        testing=[]
    )
    
    primary = await detector.get_primary_language(stack)
    assert primary == 'python'


@pytest.mark.asyncio
async def test_is_polyglot(detector):
    """Test polyglot detection."""
    stack_polyglot = TechnologyStack(
        languages={'python': 50, 'javascript': 30, 'go': 20},
        frameworks={},
        databases=[],
        tools=[],
        deployment=[],
        testing=[]
    )
    
    stack_single = TechnologyStack(
        languages={'python': 100},
        frameworks={},
        databases=[],
        tools=[],
        deployment=[],
        testing=[]
    )
    
    assert await detector.is_polyglot(stack_polyglot) == True
    assert await detector.is_polyglot(stack_single) == False


@pytest.mark.asyncio
async def test_get_architecture_hints(detector):
    """Test architecture hint generation."""
    stack = TechnologyStack(
        languages={'python': 100},
        frameworks={'fastapi': ['api.py'], 'react': ['App.tsx']},
        databases=['postgresql', 'redis', 'mongodb'],
        tools=['docker', 'kubernetes'],
        deployment=['aws'],
        testing=['pytest']
    )
    
    hints = await detector.get_architecture_hints(stack)
    
    assert 'microservices' in hints
    assert 'api-driven' in hints
    assert 'spa-frontend' in hints
    assert 'data-intensive' in hints
    assert 'cloud-native' in hints


@pytest.mark.asyncio
async def test_empty_file_list(detector):
    """Test with empty file list."""
    stack = await detector.detect_stack([], '/tmp')
    
    assert isinstance(stack, TechnologyStack)
    assert len(stack.languages) == 0
    assert len(stack.frameworks) == 0


@pytest.mark.asyncio
async def test_large_file_skipped(detector, tmp_path):
    """Test that very large files are skipped."""
    files = [
        {'path': str(tmp_path / 'huge.py'), 'language': 'python', 'is_code': True}
    ]
    
    # Create a file larger than 1MB
    (tmp_path / "huge.py").write_text("x = 1\n" * 500000)
    
    stack = await detector.detect_stack(files, str(tmp_path))
    
    # Should not crash, just skip the file
    assert isinstance(stack, TechnologyStack)


def test_singleton():
    """Test singleton pattern."""
    detector1 = get_stack_detector()
    detector2 = get_stack_detector()
    
    assert detector1 is detector2

