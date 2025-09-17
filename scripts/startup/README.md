# Startup Scripts

This directory contains scripts for starting individual services and managing the entire service ecosystem locally.

## Individual Service Starters

Each service has its own startup script that handles:
- PYTHONPATH configuration
- Service initialization
- Health monitoring
- Graceful shutdown

### Available Scripts

- `start_docstore.py` - Start Doc Store service (port 5010)
- `start_analysis_service.py` - Start Analysis Service (port 5020)
- `start_orchestrator.py` - Start Orchestrator service (port 5099)
- `start_summarizer_hub.py` - Start Summarizer Hub (port 5060)
- `start_architecture_digitizer.py` - Start Architecture Digitizer (port 5105)
- `start_bedrock_proxy.py` - Start Bedrock Proxy (port 7090)
- `start_github_mcp.py` - Start GitHub MCP (port 5072)
- `start_interpreter.py` - Start Interpreter service (port 5120)
- `start_prompt_store.py` - Start Prompt Store (port 5110)
- `start_code_analyzer.py` - Start Code Analyzer (port 5085)
- `start_secure_analyzer.py` - Start Secure Analyzer (port 5070)
- `start_log_collector.py` - Start Log Collector (port 5080)

## Master Startup Script

- `start_all_services.py` - Comprehensive service manager that can:
  - Start all services in dependency order
  - Start individual services
  - Monitor service health
  - Handle graceful shutdown
  - Focus on CLI for interactive use

## Usage Examples

```bash
# Start individual service
python scripts/startup/start_docstore.py

# Start all services with CLI focus
python scripts/startup/start_all_services.py --start

# Start services in background, focus on CLI
python scripts/startup/start_all_services.py --start --skip-cli
```

## Legacy Scripts

- `start_services.py` - Legacy startup script (kept for compatibility)
