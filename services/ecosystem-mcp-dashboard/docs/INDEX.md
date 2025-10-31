---
title: "Ecosystem MCP Dashboard - Documentation Index"
service: "ecosystem-mcp-dashboard"
category: "index"
tags: ["index", "dashboard", "navigation", "streamlit", "ui"]
related: ["../../ecosystem-mcp/docs/INDEX.md"]
status: "current"
last_updated: "2025-10-28"
audience: "all"
---

# Ecosystem MCP Dashboard Documentation

**Interactive web dashboard for Ecosystem MCP service management and monitoring**

---

## 📚 Quick Navigation

### Getting Started
- [Quick Start Guide](guides/QUICK_START.md) - Get the dashboard running in 5 minutes
- [Configuration Guide](guides/CONFIGURATION.md) - Configure dashboard settings
- [Deployment Guide](guides/DEPLOYMENT.md) - Deploy to production

### Architecture
- [System Overview](architecture/OVERVIEW.md) - Dashboard architecture and components
- [Component Catalog](features/COMPONENTS.md) - Reusable UI components
- [Integration](architecture/INTEGRATION.md) - How dashboard connects to MCP service

### Features
- [RAG Query Interface](features/RAG_INTERFACE.md) - Query documents with RAG
- [Ingestion Manager](features/INGESTION.md) - Manage document ingestion jobs
- [Monitoring & Health](features/MONITORING.md) - System health and metrics
- [Database Explorers](features/EXPLORERS.md) - PostgreSQL, Redis, ChromaDB viewers
- [Visualization](features/VISUALIZATION.md) - Charts and graphs
- [Configuration Registry](features/CONFIG_REGISTRY.md) - System configuration viewer

### API Client
- [API Client Guide](guides/API_CLIENT.md) - Using the dashboard API client
- [Circuit Breakers](architecture/CIRCUIT_BREAKERS.md) - Fault tolerance patterns
- [Caching Strategy](architecture/CACHING.md) - Response caching

### Development
- [Contributing Guide](development/CONTRIBUTING.md) - How to contribute
- [Testing Guide](development/TESTING.md) - Testing strategy
- [Component Development](development/COMPONENTS.md) - Building new components

---

## 🎯 Dashboard Overview

**Technology Stack**:
- **Frontend**: Streamlit 1.28+
- **API Client**: `httpx` with circuit breakers
- **Caching**: Redis + in-memory TTL cache
- **Visualization**: Plotly, Altair
- **Deployment**: Docker container

**Key Features**:
1. **RAG Query Interface**: Standard, Temporal, Context-Aware, Multi-Pass RAG
2. **Ingestion Management**: Start, monitor, and troubleshoot ingestion jobs
3. **System Monitoring**: Real-time health checks and metrics
4. **Database Explorers**: Interactive PostgreSQL, Redis, and ChromaDB explorers
5. **Configuration Viewer**: Centralized configuration registry
6. **Visualization**: Charts for job progress, document counts, temporal data

---

## 🏷️ Tags

#dashboard #streamlit #rag #ingestion #monitoring #visualization #ui #python

---

## 🔗 Related Services

- [Ecosystem MCP Service](../../ecosystem-mcp/docs/INDEX.md) - Main backend service
- [Embedding Service](../../ecosystem-mcp-embedding/docs/INDEX.md) - Embedding worker

---

## 📖 Quick Links

- **GitHub**: [Project Repository](../../../)
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Health**: http://localhost:8000/health

---

**Last Updated**: 2025-10-28  
**Version**: 1.0.0

