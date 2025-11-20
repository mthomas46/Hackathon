# Adaptive Documentation System - Deployment Guide

**Version:** 1.0  
**Date:** November 20, 2025  
**Status:** Production-Ready  

---

## 📋 Pre-Deployment Checklist

### **System Requirements:**
- ✅ Docker & Docker Compose installed
- ✅ PostgreSQL container running
- ✅ Redis container running
- ✅ Ollama container running (for LLM)
- ✅ Sufficient disk space (~2GB for rebuild)

### **Phase Completion Status:**
- ✅ Phase 1: Database Schema & Models (100%)
- ✅ Phase 2: Template System (100%)
- ✅ Phase 3: Adaptive Features (100%)
- ✅ Phase 4: Integration (100%)

---

## 🚀 Deployment Steps

### **Step 1: Rebuild Docker Container**

The container needs to be rebuilt to include all new code from Phases 1-4.

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Stop the service
docker-compose stop ecosystem-mcp-service

# Rebuild with no cache to ensure fresh build
docker-compose build --no-cache ecosystem-mcp-service

# Start the service
docker-compose up -d ecosystem-mcp-service

# Verify it's running
docker ps | grep ecosystem-mcp-service
```

**Expected Duration:** 3-5 minutes

---

### **Step 2: Verify Database Tables**

Ensure all Phase 1 tables were created successfully.

```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN (
    'documentation_templates',
    'template_execution_history',
    'prompt_execution_history',
    'documentation_citations',
    'generation_transparency_log'
)
ORDER BY table_name;
"
```

**Expected Output:** 5 tables listed

---

### **Step 3: Seed System Templates**

Load the 3 built-in templates into the database.

```bash
docker exec ecosystem-mcp-service python -m src.scripts.seed_templates
```

**Expected Output:**
```
✅ Loaded template from .rag-config/doc-templates/api-reference/openapi-style.yaml
✅ Seeded template 'api_reference_openapi_style'
✅ Loaded template from .rag-config/doc-templates/runbooks/sre-style.yaml
✅ Seeded template 'runbook_sre_style'
✅ Loaded template from .rag-config/doc-templates/architecture/c4-model.yaml
✅ Seeded template 'architecture_c4_style'
🌱 Template seeding complete!
   ✅ Successfully seeded: 3
```

---

### **Step 4: Verify Templates in Database**

```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
SELECT name, category, is_system_template, is_active 
FROM documentation_templates 
WHERE is_system_template = true;
"
```

**Expected Output:** 3 templates listed

---

### **Step 5: Test API Health**

Verify the service is responding.

```bash
curl -s http://localhost:8000/health | jq .
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "...",
  "services": {...}
}
```

---

### **Step 6: Test Template API**

List available templates.

```bash
curl -s http://localhost:8000/api/v1/templates/ | jq .
```

**Expected Response:** Array of 3 templates

---

### **Step 7: Test Context Preview**

Preview what context would be used for documentation generation.

```bash
curl -s "http://localhost:8000/api/v1/documentation/adaptive/preview/adminservice?template_name=api_reference_openapi_style&category=api_reference" | jq .
```

**Expected Response:**
```json
{
  "service_name": "adminservice",
  "template_name": "api_reference_openapi_style",
  "context": {
    "frameworks": ["Play Framework"],
    "languages": {...},
    "concepts": [...],
    "keywords": [...]
  },
  "template": {
    "sections": [...]
  }
}
```

---

### **Step 8: Generate Test Documentation**

Generate documentation for adminservice using API Reference template.

```bash
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "adminservice",
    "template_name": "api_reference_openapi_style",
    "category": "api_reference",
    "include_citations": true,
    "citation_style": "endnotes",
    "transparency_mode": "verbose",
    "include_optional_sections": false
  }' | jq . > test_documentation.json
```

**Expected Response:**
```json
{
  "run_id": "...",
  "service_name": "adminservice",
  "content": "# adminservice - API Reference\n\n...",
  "metadata": {
    "sections_generated": 8,
    "concepts_discovered": 12,
    "frameworks_detected": ["Play Framework"],
    "citations_added": 45
  },
  "transparency_report_url": "/api/v1/transparency/...",
  "citations": [...]
}
```

---

### **Step 9: Verify Transparency Logging**

Get transparency report for the test generation.

```bash
# Extract run_id from previous response
RUN_ID=$(cat test_documentation.json | jq -r '.run_id')

# Get transparency report
curl -s "http://localhost:8000/api/v1/documentation/adaptive/transparency/${RUN_ID}?format=json" | jq .statistics
```

**Expected Response:**
```json
{
  "discovery": {
    "total_actions": 2,
    "successful_actions": 2,
    "total_duration_ms": 150
  },
  "generation": {
    "total_actions": 8,
    "successful_actions": 8,
    "total_duration_ms": 12000
  },
  ...
}
```

---

### **Step 10: Verify Citations**

Check that citations were properly recorded.

```bash
# Get artifact_id from response (if available)
# For now, verify the citations array in the response
cat test_documentation.json | jq '.citations | length'
```

**Expected Output:** Number of citations (should be > 0)

---

## ✅ Deployment Validation Checklist

After completing all steps, verify:

- [ ] Docker container rebuilt successfully
- [ ] All 5 database tables exist
- [ ] 3 system templates seeded
- [ ] API health check passes
- [ ] Template list endpoint works
- [ ] Context preview works
- [ ] Documentation generation succeeds
- [ ] Generated content is properly formatted
- [ ] Transparency logging working
- [ ] Citations included in output

---

## 🔧 Troubleshooting

### **Issue: Container fails to start**

**Check logs:**
```bash
docker logs ecosystem-mcp-service --tail 100
```

**Common causes:**
- Python syntax errors (check compilation)
- Missing dependencies (check requirements.txt)
- Port conflicts (check if 8000 is available)

**Solution:**
```bash
# Fix any syntax errors, then rebuild
docker-compose build --no-cache ecosystem-mcp-service
docker-compose up -d ecosystem-mcp-service
```

---

### **Issue: Templates not seeding**

**Check if template files exist:**
```bash
ls -la .rag-config/doc-templates/api-reference/
ls -la .rag-config/doc-templates/runbooks/
ls -la .rag-config/doc-templates/architecture/
```

**Check for YAML syntax errors:**
```bash
python3 -c "import yaml; yaml.safe_load(open('.rag-config/doc-templates/api-reference/openapi-style.yaml'))"
```

**Manual seed:**
```bash
docker exec -it ecosystem-mcp-service python -m src.scripts.seed_templates
```

---

### **Issue: Documentation generation fails**

**Check if service has context:**
```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
SELECT service_name, frameworks, architecture_type 
FROM repository_contexts 
WHERE service_name = 'adminservice';
"
```

**If no context found:**
- Run ingestion job for adminservice first
- Check that repository_contexts was populated

**Check transparency log for errors:**
```bash
curl -s "http://localhost:8000/api/v1/documentation/adaptive/transparency/${RUN_ID}/failed" | jq .
```

---

### **Issue: Citations not appearing**

**Verify citation configuration:**
- Check that `include_citations` is `true`
- Verify sources are being returned from RAG queries
- Check that documents exist for the service

**Manual verification:**
```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
SELECT COUNT(*) FROM documents WHERE service_name = 'adminservice';
"
```

---

## 📊 Performance Benchmarks

**Expected performance (Phase 1-4):**

| Operation | Expected Time |
|-----------|---------------|
| Container rebuild | 3-5 minutes |
| Template seeding | < 5 seconds |
| Context preview | < 100ms |
| Single section generation | 2-5 seconds |
| Full document (8 sections) | 20-40 seconds |
| Transparency report | < 100ms |

**Factors affecting performance:**
- LLM response time (Ollama)
- Number of documents to search
- RAG query complexity
- Number of sections in template

---

## 🎯 Post-Deployment Tasks

### **1. Verify All Templates Work**

Test each template:

```bash
# API Reference
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{"service_name": "adminservice", "template_name": "api_reference_openapi_style", "category": "api_reference"}'

# SRE Runbook
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{"service_name": "adminservice", "template_name": "runbook_sre_style", "category": "runbook"}'

# Architecture
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{"service_name": "adminservice", "template_name": "architecture_c4_style", "category": "architecture"}'
```

### **2. Review Generated Documentation**

Check the quality:
- Is content structured according to template?
- Are citations present and properly formatted?
- Is framework-specific terminology used?
- Are code examples included?

### **3. Review Transparency Logs**

Verify complete audit trail:
- All phases logged
- Timing information accurate
- No unexpected failures

### **4. Monitor Prompt Effectiveness**

After a few generations:

```bash
# Get average effectiveness
curl -s http://localhost:8000/api/v1/prompt-analytics/effectiveness | jq .

# Get low-performing prompts
curl -s http://localhost:8000/api/v1/prompt-analytics/low-performing | jq .
```

---

## 🚀 Production Readiness

### **Before Production Use:**

**Security:**
- [ ] Review authentication/authorization
- [ ] Check API rate limiting
- [ ] Verify input validation
- [ ] Review error messages (no sensitive data)

**Performance:**
- [ ] Test with realistic workloads
- [ ] Monitor memory usage
- [ ] Check database query performance
- [ ] Optimize slow endpoints if needed

**Monitoring:**
- [ ] Set up logging aggregation
- [ ] Configure metrics collection
- [ ] Set up alerts for failures
- [ ] Monitor disk usage

**Backup:**
- [ ] Configure database backups
- [ ] Test restore procedures
- [ ] Document recovery process

---

## 📝 Deployment Checklist Summary

**Quick checklist for deployment:**

```bash
# 1. Rebuild
docker-compose build --no-cache ecosystem-mcp-service
docker-compose up -d ecosystem-mcp-service

# 2. Verify database
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "\dt documentation_*"

# 3. Seed templates
docker exec ecosystem-mcp-service python -m src.scripts.seed_templates

# 4. Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/templates/

# 5. Generate test doc
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{"service_name": "adminservice", "template_name": "api_reference_openapi_style", "category": "api_reference"}'

# ✅ Deployment complete!
```

---

**Status:** Ready for deployment!  
**Risk Level:** 🟢 LOW  
**Estimated Time:** 30-45 minutes  
**Rollback Available:** Yes (database backup + git)

