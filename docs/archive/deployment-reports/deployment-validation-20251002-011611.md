# Deployment Validation Report

**Timestamp**: Thu Oct  2 01:16:11 CDT 2025
**Validation Status**: PASSED
**Environment**: Development

## Container Overview
```
NAMES                                  STATUS                   PORTS
hackathon-simulation-dashboard-1       Up 2 hours (unhealthy)   0.0.0.0:8100->8501/tcp, [::]:8100->8501/tcp
hackathon-frontend-1                   Up 2 hours (healthy)     0.0.0.0:8089->3000/tcp, [::]:8089->3000/tcp
hackathon-project-simulation-1         Up 2 hours (healthy)     0.0.0.0:8099->5075/tcp, [::]:8099->5075/tcp
hackathon-unified-api-dashboard-1      Up 2 hours (healthy)     0.0.0.0:8101->8000/tcp, [::]:8101->8000/tcp
hackathon-interpreter-1                Up 2 hours (healthy)     0.0.0.0:8098->5120/tcp, [::]:8098->5120/tcp
hackathon-cli-1                        Up 2 hours (healthy)     0.0.0.0:8110->5130/tcp, [::]:8110->5130/tcp
hackathon-mock-data-generator-1        Up 2 hours (healthy)     0.0.0.0:8093->5065/tcp, [::]:8093->5065/tcp
hackathon-llm-gateway-1                Up 2 hours (healthy)     0.0.0.0:8092->5055/tcp, [::]:8092->5055/tcp
hackathon-analysis-service-1           Up 2 hours (healthy)     0.0.0.0:8087->5020/tcp, [::]:8087->5020/tcp
hackathon-discovery-agent-1            Up 2 hours (healthy)     0.0.0.0:8095->5045/tcp, [::]:8095->5045/tcp
hackathon-project-planning-service-1   Up 2 hours (healthy)     0.0.0.0:5170->5170/tcp, [::]:5170->5170/tcp
hackathon-bedrock-proxy-1              Up 2 hours (healthy)     0.0.0.0:5002->5002/tcp, [::]:5002->5002/tcp
hackathon-source-agent-1               Up 2 hours (healthy)     0.0.0.0:8088->5085/tcp, [::]:8088->5085/tcp
hackathon-summarizer-hub-1             Up 2 hours (healthy)     0.0.0.0:5160->5160/tcp, [::]:5160->5160/tcp
hackathon-ollama-1                     Up 2 hours (healthy)     0.0.0.0:8090->11434/tcp, [::]:8090->11434/tcp
hackathon-prompt_store-1               Up 2 hours (healthy)     0.0.0.0:8097->5110/tcp, [::]:8097->5110/tcp
hackathon-memory-agent-1               Up 2 hours (healthy)     0.0.0.0:5090->5090/tcp, [::]:5090->5090/tcp
hackathon-user-store-1                 Up 2 hours (healthy)     0.0.0.0:8106->5150/tcp, [::]:8106->5150/tcp
hackathon-doc_store-1                  Up 2 hours (healthy)     0.0.0.0:8086->5087/tcp, [::]:8086->5087/tcp
hackathon-external-service-store-1     Up 2 hours (healthy)     0.0.0.0:8105->5140/tcp, [::]:8105->5140/tcp
hackathon-architecture-digitizer-1     Up 2 hours (healthy)     0.0.0.0:8091->5105/tcp, [::]:8091->5105/tcp
hackathon-log-collector-1              Up 2 hours (healthy)     0.0.0.0:8104->5080/tcp, [::]:8104->5080/tcp
hackathon-orchestrator-1               Up 2 hours (healthy)     0.0.0.0:8085->5099/tcp, [::]:8085->5099/tcp
hackathon-secure-analyzer-1            Up 2 hours (healthy)     0.0.0.0:8103->5070/tcp, [::]:8103->5070/tcp
hackathon-code-analyzer-1              Up 2 hours (healthy)     0.0.0.0:8102->5025/tcp, [::]:8102->5025/tcp
hackathon-github-mcp-1                 Up 2 hours (healthy)     0.0.0.0:8094->5030/tcp, [::]:8094->5030/tcp
hackathon-notification-service-1       Up 2 hours (healthy)     0.0.0.0:8096->5130/tcp, [::]:8096->5130/tcp
hackathon-redis-1                      Up 2 hours (healthy)     0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
```

## Health Metrics
- **Total Containers**: 29
- **Healthy Containers**: 28
- **Health Percentage**: 96.5%

## Critical Services Status
- **redis**: ✅ Running
- **orchestrator**: ✅ Running
- **doc_store**: ✅ Running
- **analysis-service**: ✅ Running
- **llm-gateway**: ✅ Running
- **discovery-agent**: ✅ Running

## Resource Usage Summary
```
CONTAINER      CPU %     MEM %     MEM USAGE / LIMIT
a014a045176f   0.16%     0.62%     48.77MiB / 7.653GiB
c749fda90c62   0.22%     0.62%     48.43MiB / 7.653GiB
1628d6074636   0.20%     0.97%     75.96MiB / 7.653GiB
604ef93e1456   0.33%     0.92%     72.19MiB / 7.653GiB
54485e00b8ad   0.17%     0.73%     57.02MiB / 7.653GiB
4bafd662d011   0.33%     1.28%     100.5MiB / 7.653GiB
d8c6b6ef3a5d   0.26%     0.66%     51.54MiB / 7.653GiB
7bc0c01f2727   0.19%     0.69%     54.16MiB / 7.653GiB
17f904334ede   0.21%     0.88%     69.34MiB / 7.653GiB
728a5e4035e7   0.23%     0.61%     47.6MiB / 7.653GiB
65acb073315d   0.28%     0.70%     54.49MiB / 7.653GiB
68d1e0c2be0b   0.19%     0.49%     38.56MiB / 7.653GiB
f0bd72029433   0.21%     0.69%     53.83MiB / 7.653GiB
7d44f055d87d   0.19%     0.67%     52.82MiB / 7.653GiB
a948764a34cf   0.00%     0.69%     54.32MiB / 7.653GiB
72baa936f9d6   0.19%     0.93%     72.69MiB / 7.653GiB
75eeb7a1e1e4   0.25%     0.53%     41.42MiB / 7.653GiB
86940e7732e4   0.17%     0.63%     49.3MiB / 7.653GiB
cd8f30ed456b   0.24%     0.72%     56.66MiB / 7.653GiB
f5b23a5af1d7   0.20%     0.51%     40.24MiB / 7.653GiB
a5986ebe2789   0.21%     0.74%     57.77MiB / 7.653GiB
7c86e5b8598d   0.20%     1.10%     86.59MiB / 7.653GiB
fe75efde6701   0.21%     0.87%     68.53MiB / 7.653GiB
018554728b3b   0.18%     0.60%     46.71MiB / 7.653GiB
8278fd35d415   0.17%     0.61%     47.85MiB / 7.653GiB
cab34bfdf0a5   0.20%     0.82%     64.07MiB / 7.653GiB
827830ae93a8   0.17%     0.54%     42.24MiB / 7.653GiB
8079f195a7ed   0.78%     0.19%     15.19MiB / 7.653GiB
```

## Validation Checklist
- [x] Critical services validation
- [x] Health percentage check
- [x] Network connectivity test
- [x] Resource usage analysis
- [x] Log error scanning
- [x] Dependency validation

**Report Generated**: Thu Oct  2 01:16:13 CDT 2025
