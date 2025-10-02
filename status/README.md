# System Status & Runtime Information

This directory contains current system status files and runtime information for the LLM Documentation Ecosystem.

## Status Files

### Service Status
- **`running_services.txt`** - Currently running services and their status
- **`all_running_services.txt`** - Complete list of all detected running services

## Purpose

Status files provide:
- **Operational Visibility**: Current system state and running services
- **Troubleshooting Support**: Service availability and health information
- **Monitoring Integration**: Input for monitoring dashboards and alerts
- **Deployment Verification**: Confirmation of successful deployments

## File Formats

- **Text Files**: Human-readable service lists and status information
- **Auto-generated**: Updated by monitoring and deployment scripts
- **Timestamped**: Files include generation timestamps where applicable

## Usage

Status files are used by:
- **Monitoring systems** for health checks and alerting
- **Deployment scripts** for verification and rollback decisions
- **Operations teams** for system status assessment
- **Development teams** for environment validation

## Update Frequency

Status files are updated:
- **Real-time**: During service startup/shutdown operations
- **Periodic**: By monitoring systems (typically every 30 seconds)
- **On-demand**: By status check commands and health verification

## Related Systems

- **Monitoring Scripts**: Located in `scripts/monitoring/`
- **Health Dashboards**: Web interfaces and API endpoints
- **Alert Systems**: Email, Slack, and webhook notifications
- **Deployment Tools**: Service orchestration and management scripts

## Maintenance

Status files are:
- **Automatically managed** by system scripts
- **Self-cleaning** with configurable retention policies
- **Backup-enabled** for historical analysis when needed
