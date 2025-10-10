# 🔧 bedrock-proxy Configuration Guide

**Service**: `bedrock-proxy`  
**Version**: `1.0.0`  
**Last Updated**: 2025-10-10

---

## 📋 Overview

This document describes all configuration options, environment variables, ports, and deployment settings for the `bedrock-proxy` service.

---

## 🔌 Ports & Networking

| Port | Type | Purpose | Required |
|------|------|---------|----------|
| **7090** | Internal | Service HTTP API | Yes |
| **5060** | External | External access (load balancer) | No |

### Port Configuration

```bash
# Environment variable
export SERVICE_API_PORT=7090

# Default if not set: 7090
```

---

## 🌍 Environment Variables

### Core Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_API_PORT` | Internal service port | `7090` | No |
| `BEDROCK_MOCK_MODE` | Enable mock mode (no AWS costs) | `true` | No |

### AWS Configuration (Production Mode Only)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock | - | Prod only |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | Prod only |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` | No |

---

## 📝 Configuration Files

### config.yaml

Main service configuration (development settings).

```yaml
service:
  name: bedrock-proxy
  version: 1.0.0
  port: 7090

bedrock:
  mock_mode: true
  default_model: "anthropic.claude-3-sonnet-20240229-v1:0"
  default_region: "us-east-1"

templates:
  supported:
    - summary
    - risks
    - decisions
    - pr_confidence
    - life_of_ticket
  
formats:
  supported:
    - md
    - txt
    - json
```

### config.development.yaml

Development-specific settings (mock mode enabled).

### config.production.yaml

Production settings (AWS Bedrock integration).

---

## 🎭 Configuration Profiles

### Development Profile

**Purpose**: Local development without AWS costs

```bash
# Enable mock mode
export BEDROCK_MOCK_MODE=true
export SERVICE_API_PORT=7090

# No AWS credentials needed
```

**Features**:
- Template-based responses
- No AWS Bedrock API calls
- Zero infrastructure costs
- Deterministic outputs for testing

### Production Profile

**Purpose**: Full AWS Bedrock integration

```bash
# Disable mock mode
export BEDROCK_MOCK_MODE=false

# AWS credentials required
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

export SERVICE_API_PORT=7090
```

**Features**:
- Real AWS Bedrock foundation models
- Claude, Titan, and other models
- Production-grade AI responses
- Usage-based AWS billing

---

## 🐳 Docker Configuration

### Dockerfile

Multi-stage build for optimized images.

**Build**:
```bash
docker build -t bedrock-proxy:latest .
```

**Run (Development)**:
```bash
docker run -d \
  -p 7090:7090 \
  -e BEDROCK_MOCK_MODE=true \
  --name bedrock-proxy \
  bedrock-proxy:latest
```

**Run (Production)**:
```bash
docker run -d \
  -p 7090:7090 \
  -e BEDROCK_MOCK_MODE=false \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_REGION=us-east-1 \
  --name bedrock-proxy \
  bedrock-proxy:latest
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bedrock-proxy:
    build: .
    ports:
      - "7090:7090"
    environment:
      - SERVICE_API_PORT=7090
      - BEDROCK_MOCK_MODE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🔗 Service Dependencies

### Runtime Dependencies

| Service | Purpose | Required | Fallback |
|---------|---------|----------|----------|
| **AWS Bedrock** | Foundation models | Prod only | Mock mode |

### No External Dependencies in Mock Mode

The service is fully self-contained in development/mock mode.

---

## 🎯 Template Configuration

### Supported Templates

| Template | Purpose | Use Case |
|----------|---------|----------|
| `summary` | General summarization | Content summaries, key points |
| `risks` | Risk assessment | Risk analysis, mitigation planning |
| `decisions` | Decision documentation | Decision tracking, rationale |
| `pr_confidence` | PR confidence scoring | Code review confidence |
| `life_of_ticket` | Ticket lifecycle | Issue tracking, lifecycle |

### Template Auto-Detection

Templates are auto-detected from prompt content:

```json
{
  "prompt": "Summarize this PR",
  "template": null  // Auto-detected as "summary"
}
```

Detection rules (in order):
1. "summary" keyword → `summary` template
2. "risk" keyword → `risks` template
3. "decision" keyword → `decisions` template
4. "pr" + "confidence" → `pr_confidence` template
5. "life" + "ticket" → `life_of_ticket` template

---

## 📊 Output Format Configuration

### Supported Formats

| Format | Description | Content-Type | Use Case |
|--------|-------------|--------------|----------|
| `md` | Markdown | `text/markdown` | Documentation, rich text |
| `txt` | Plain text | `text/plain` | Simple output, logs |
| `json` | Structured JSON | `application/json` | API integration, parsing |

### Format Examples

**Markdown**:
```markdown
## Summary

- Key point 1
- Key point 2
- Key point 3
```

**Plain Text**:
```
Summary

- Key point 1
- Key point 2
- Key point 3
```

**JSON**:
```json
{
  "title": "Summary",
  "sections": {
    "Summary": ["Key point 1", "Key point 2", "Key point 3"]
  }
}
```

---

## 🚀 Deployment Configuration

### Local Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 7090
```

### Docker Deployment

```bash
# Build
docker build -t bedrock-proxy:1.0.0 .

# Run
docker run -d -p 7090:7090 bedrock-proxy:1.0.0

# Verify
curl http://localhost:7090/health
```

### Docker Compose Deployment

```bash
# Start
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:7090/health

# Stop
docker-compose down
```

---

## 🔒 Security Configuration

### API Authentication

Currently optional. Can be enabled through middleware.

### AWS Credentials

**Production Mode**:
- Use IAM roles when possible
- Never commit credentials to code
- Use AWS Secrets Manager for production

**Development Mode**:
- No credentials needed (mock mode)

---

## 📈 Monitoring Configuration

### Health Checks

```bash
# Health endpoint
GET /health

# Response
{
  "service": "bedrock-proxy",
  "version": "1.0.0",
  "status": "healthy"
}
```

### Metrics

- Request count
- Template usage
- Format distribution
- AWS API calls (production mode)

---

## 🧪 Testing Configuration

### Test Environment

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=. --cov-report=html

# View coverage
open htmlcov/index.html
```

### Mock Mode for Testing

```bash
export BEDROCK_MOCK_MODE=true
pytest tests/
```

---

## 📝 Configuration Best Practices

1. **Use Environment Variables**: Don't hardcode configuration
2. **Mock Mode for Development**: Save costs, faster iteration
3. **IAM Roles for Production**: Avoid credential management
4. **Health Checks**: Always configure Docker health checks
5. **Version Control**: Never commit AWS credentials
6. **Template Selection**: Use auto-detection when possible
7. **Format Selection**: Choose based on consumer needs

---

## 🔍 Troubleshooting

### Issue: Service won't start

**Check**:
```bash
# Verify port not in use
lsof -i :7090

# Check environment variables
env | grep BEDROCK
```

### Issue: AWS authentication fails

**Solution**:
- Verify AWS credentials are set
- Check IAM permissions
- Use mock mode for development

### Issue: Template not detected

**Solution**:
- Explicitly specify template parameter
- Check prompt keywords
- Review auto-detection rules

---

**For More Information**:
- Main README: [README.md](README.md)
- API Documentation: http://localhost:7090/docs
- OpenAPI Spec: http://localhost:7090/openapi.json

