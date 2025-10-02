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

