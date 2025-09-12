# Docs Parity Matrix

Legend: Present = ✓, Missing = ✗, N/A = —

| Service | Navigation | Overview/Role | Features | Endpoint Table | Environment/Config | Testing | Related |
|---------|------------|---------------|----------|-----------------|--------------------|---------|---------|
| analysis-service | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| bedrock-proxy | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| cli | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| code-analyzer | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| discovery-agent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| doc-store | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| frontend | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| github-mcp | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| interpreter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| log-collector | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| memory-agent | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| notification-service | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| orchestrator | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| prompt-store | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| secure-analyzer | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| summarizer-hub | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| source-agent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Status Summary

✅ **All services now have comprehensive documentation** with:
- Navigation headers linking to related docs
- Overview and role sections explaining ecosystem purpose
- Features sections highlighting key capabilities
- Endpoint tables with method, path, and descriptions
- Environment/Config sections (where applicable)
- Testing sections with links to test directories
- Related services sections for cross-referencing

## Notes and follow-ups

### Resolved Issues ✅
- CLI: Already has "Overview and role" section and "Commands" table
- Code Analyzer, Discovery Agent, Secure Analyzer: All have explicit overview sections
- Memory Agent: Already has endpoint table format
- Frontend: Has environment configuration documented
- Bedrock Proxy: Has environment configuration for proxy setup

### Remaining Considerations
- For services with minimal environment variables (Memory Agent), the lack of extensive env config is appropriate as they use shared config
- CLI doesn't require extensive environment setup as it's primarily a client tool

### Maintenance Guidelines
When updating service documentation:
1. Ensure new services follow the established template
2. Update this matrix when adding new documentation sections
3. Keep cross-references current when services are renamed or endpoints change
4. Review and update environment variables when configuration changes

This matrix is intended for ongoing maintenance and ensures consistent documentation quality across all services.
