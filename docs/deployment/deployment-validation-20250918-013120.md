# Deployment Validation Report

**Timestamp**: Thu Sep 18 01:31:20 CDT 2025
**Validation Status**: PASSED
**Environment**: Development

## Container Overview
```
NAMES                                STATUS                       PORTS
hackathon-discovery-agent-1          Up 14 minutes (healthy)      0.0.0.0:5045->5045/tcp, :::5045->5045/tcp
hackathon-notification-service-1     Up 18 minutes (unhealthy)    0.0.0.0:5020->5020/tcp, :::5020->5020/tcp
hackathon-code-analyzer-1            Up 21 minutes (unhealthy)    0.0.0.0:5050->5050/tcp, :::5050->5050/tcp
hackathon-summarizer-hub-1           Up 28 minutes (healthy)      0.0.0.0:5160->5160/tcp, :::5160->5160/tcp
hackathon-analysis-service-1         Up 32 minutes (healthy)      0.0.0.0:5080->5020/tcp, [::]:5080->5020/tcp
hackathon-github-mcp-1               Up 33 minutes (unhealthy)    0.0.0.0:5030->5072/tcp, [::]:5030->5072/tcp
hackathon-bedrock-proxy-1            Up 33 minutes (unhealthy)    0.0.0.0:5060->7090/tcp, [::]:5060->7090/tcp
hackathon-log-collector-1            Up 43 minutes (unhealthy)    0.0.0.0:5040->5080/tcp, [::]:5040->5080/tcp
hackathon-secure-analyzer-1          Up 43 minutes (unhealthy)    0.0.0.0:5100->5070/tcp, [::]:5100->5070/tcp
hackathon-memory-agent-1             Up 43 minutes (unhealthy)    0.0.0.0:5090->5040/tcp, [::]:5090->5040/tcp
hackathon-mock-data-generator-1      Up About an hour (healthy)   0.0.0.0:5065->5065/tcp, :::5065->5065/tcp
hackathon-redis-1                    Up About an hour (healthy)   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp
hackathon-llm-gateway-1              Up About an hour (healthy)   0.0.0.0:5055->5055/tcp, :::5055->5055/tcp
hackathon-source-agent-1             Up 23 minutes (unhealthy)    0.0.0.0:5070->5070/tcp, :::5070->5070/tcp
hackathon-doc_store-1                Up About an hour (healthy)   0.0.0.0:5087->5010/tcp, [::]:5087->5010/tcp
hackathon-ollama-1                   Up About an hour             0.0.0.0:11434->11434/tcp, :::11434->11434/tcp
hackathon-frontend-1                 Up About an hour (healthy)   0.0.0.0:3000->3000/tcp, :::3000->3000/tcp
hackathon-architecture-digitizer-1   Up About an hour (healthy)   0.0.0.0:5105->5105/tcp, :::5105->5105/tcp
hackathon-prompt_store-1             Up About an hour (healthy)   0.0.0.0:5110->5110/tcp, :::5110->5110/tcp
hackathon-interpreter-1              Up About an hour (healthy)   0.0.0.0:5120->5120/tcp, :::5120->5120/tcp
hackathon-cli-1                      Up 53 minutes                
hackathon-orchestrator-1             Up About an hour (healthy)   0.0.0.0:5099->5099/tcp, :::5099->5099/tcp
```

## Health Metrics
- **Total Containers**: 23
- **Healthy Containers**: 20
- **Health Percentage**: 86.9%

## Critical Services Status
- **orchestrator**: ✅ Running
- **llm-gateway**: ✅ Running
- **doc_store**: ✅ Running
- **discovery-agent**: ✅ Running

## Resource Usage Summary
```
CONTAINER      CPU %     MEM %     MEM USAGE / LIMIT
a4a89a3d39b1   0.16%     0.62%     48.38MiB / 7.653GiB
27f3494c0449   0.21%     0.61%     47.96MiB / 7.653GiB
32d86c183ba9   0.20%     0.43%     33.7MiB / 7.653GiB
9424dd4f19f5   0.15%     0.43%     33.46MiB / 7.653GiB
278f42d8c330   0.21%     0.58%     45.37MiB / 7.653GiB
20ad1cccb97a   0.17%     0.61%     47.77MiB / 7.653GiB
05fb6969afb7   0.18%     0.62%     48.6MiB / 7.653GiB
24b4f6a038af   0.58%     0.62%     48.22MiB / 7.653GiB
63166ca2f1d7   0.19%     0.61%     48.09MiB / 7.653GiB
4ae72e6a2345   0.14%     0.62%     48.7MiB / 7.653GiB
d6d54a2be097   0.13%     0.62%     48.46MiB / 7.653GiB
52d956e25c57   0.15%     0.56%     43.61MiB / 7.653GiB
da2e6d3c40dd   0.49%     0.12%     9.457MiB / 7.653GiB
71ef179a8096   0.15%     0.57%     44.54MiB / 7.653GiB
295113316fa6   0.51%     0.62%     48.75MiB / 7.653GiB
5aa8c23fa591   0.19%     0.66%     52.06MiB / 7.653GiB
dec2ee6baba7   0.00%     1.18%     92.62MiB / 7.653GiB
a89342ccdfe9   0.16%     0.65%     51.09MiB / 7.653GiB
2c0db74bb97e   0.25%     0.63%     49.1MiB / 7.653GiB
5a03b29a1a95   0.53%     0.75%     58.86MiB / 7.653GiB
db45efc3086a   0.14%     0.57%     44.43MiB / 7.653GiB
8cb980681ac8   0.00%     0.01%     716KiB / 7.653GiB
30e715daf81a   0.22%     0.72%     56.17MiB / 7.653GiB
```

## Validation Checklist
- [x] Critical services validation
- [x] Health percentage check
- [x] Network connectivity test
- [x] Resource usage analysis
- [x] Log error scanning
- [x] Dependency validation

**Report Generated**: Thu Sep 18 01:31:23 CDT 2025
