---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about technical aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# API Schema Documentation

This document defines the standardized API response schemas for all services.

## Doc_Store Service

### `/api/v1/documents`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/api/v1/documents/*`
**Schema**: `SuccessResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Optional[typing.Dict[str, typing.Any]]

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

## Orchestrator Service

### `/api/v1/services`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

## Llm-Gateway Service

### `/api/v1/providers`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

## Discovery-Agent Service

### `/api/v1/discovery/services`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

## Analysis-Service Service

### `/api/v1/analysis/analyze`
**Schema**: `SuccessResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Optional[typing.Dict[str, typing.Any]]

### `/api/v1/analysis/capabilities`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

## Prompt_Store Service

### `/api/v1/prompts`
**Schema**: `ListResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `data`: typing.Dict[str, typing.Any]
- `total`: <class 'int'>
- `has_more`: <class 'bool'>
- `limit`: <class 'int'>
- `offset`: <class 'int'>

### `/health`
**Schema**: `HealthResponseModel`

**Fields**:
- `success`: <class 'bool'>
- `message`: <class 'str'>
- `timestamp`: <class 'str'>
- `request_id`: typing.Optional[str]
- `status`: <class 'str'>
- `service`: <class 'str'>
- `version`: <class 'str'>
- `uptime_seconds`: <class 'float'>
- `environment`: <class 'str'>
- `dependencies`: typing.Optional[typing.Dict[str, str]]

