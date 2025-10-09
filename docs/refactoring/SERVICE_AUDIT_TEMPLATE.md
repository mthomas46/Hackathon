<!-- AI_READ_PRIORITY: 4 -->
<!-- AI_TAGS: audit, template, assessment -->
<!-- AI_KEY_SECTIONS: Service Overview, Architecture Assessment, Gap Analysis -->

---
ai_metadata:
  purpose: audit_template
  read_priority: 4
  context_level: reference
  tags:
  - audit
  - template
  - assessment
  when_to_read: During Phase 1 (Audit & Analysis)
  key_sections:
  - Service Overview
  - Architecture Assessment
  - Gap Analysis
  execution_relevance: phase-specific
  relevant_phases:
  - Phase 1
---

# 📋 Service Audit Template

**Service Name**: _________________  
**Audit Date**: _________________  
**Auditor**: _________________  
**Version**: _________________

---

## 📊 Executive Summary

**Service Status**: ⚪ Not Started | 🟡 In Progress | 🟢 Complete  
**Overall Score**: ___/100  
**Recommendation**: ⚪ No Action | 🟡 Minor Refactor | 🟠 Major Refactor | 🔴 Complete Rewrite

**Key Findings**:
1. 
2. 
3. 

---

## 1️⃣ Service Overview

### Basic Information

| Item | Value |
|------|-------|
| Service Name | |
| Current Port | |
| Repository Location | |
| Primary Language | |
| Framework/Library | |
| Current Version | |
| Lines of Code | |
| Last Updated | |

### Purpose & Responsibilities

**Primary Purpose**:
> Describe what this service does in 2-3 sentences

**Key Responsibilities**:
- 
- 
- 

**Bounded Context** (DDD):
> Describe the domain boundary

---

## 2️⃣ Architecture Assessment

### Current Architecture

**Architecture Pattern**: ⚪ Monolithic | ⚪ Layered | ⚪ DDD | ⚪ Other: _______

**Layer Structure**:
```
Current Structure:
├── [List current directories]
├── 
└── 
```

**Score**: ___/10

**Findings**:
- ✅ Strengths:
  - 
  
- ❌ Weaknesses:
  - 
  
- 💡 Recommendations:
  - 

### DDD Compliance

| Component | Exists | Properly Structured | Score |
|-----------|--------|-------------------|-------|
| Domain Entities | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Value Objects | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Aggregates | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Domain Services | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Domain Events | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Repositories (Interfaces) | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Application Services | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Use Cases | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| DTOs | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Repository Implementations | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |

**Overall DDD Score**: ___/100

### SOLID Principles

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| Single Responsibility | ☐ ✅ ☐ ⚠️ ☐ ❌ | |
| Open/Closed | ☐ ✅ ☐ ⚠️ ☐ ❌ | |
| Liskov Substitution | ☐ ✅ ☐ ⚠️ ☐ ❌ | |
| Interface Segregation | ☐ ✅ ☐ ⚠️ ☐ ❌ | |
| Dependency Inversion | ☐ ✅ ☐ ⚠️ ☐ ❌ | |

**Overall SOLID Score**: ___/10

---

## 3️⃣ Dependencies Analysis

### Service Dependencies

**Services This Service Depends On**:

| Service | Purpose | Required | Health Check |
|---------|---------|----------|-------------|
| | | ☐ Required ☐ Optional | ☐ Yes ☐ No |
| | | ☐ Required ☐ Optional | ☐ Yes ☐ No |
| | | ☐ Required ☐ Optional | ☐ Yes ☐ No |

**Services That Depend On This Service**:

| Service | Purpose | Critical |
|---------|---------|----------|
| | | ☐ Yes ☐ No |
| | | ☐ Yes ☐ No |
| | | ☐ Yes ☐ No |

### Circular Dependencies

**Circular Dependencies Detected**: ☐ Yes ☐ No

**Details**:
```
Service A → Service B → Service C → Service A
```

**Impact**: ⚪ None | 🟡 Low | 🟠 Medium | 🔴 High

### External Dependencies

**Python Packages**:
| Package | Version | Purpose | Up-to-date |
|---------|---------|---------|-----------|
| | | | ☐ Yes ☐ No |
| | | | ☐ Yes ☐ No |

**External Services/APIs**:
| Service | Purpose | SLA |
|---------|---------|-----|
| | | |

---

## 4️⃣ API Assessment

### REST Compliance

**Endpoint Inventory**:

| Method | Endpoint | Purpose | REST Compliant |
|--------|----------|---------|----------------|
| | | | ☐ Yes ☐ No |
| | | | ☐ Yes ☐ No |
| | | | ☐ Yes ☐ No |

**Total Endpoints**: ___

**REST Compliance Score**: ___/10

**Issues**:
- 
- 

### OpenAPI/Swagger Documentation

**OpenAPI Specification Exists**: ☐ Yes ☐ No

**Documentation Coverage**:
| Aspect | Coverage |
|--------|----------|
| Endpoints | ___% |
| Request Schemas | ___% |
| Response Schemas | ___% |
| Error Responses | ___% |
| Examples | ___% |

**Overall API Documentation Score**: ___/10

### Request/Response Patterns

**Consistent Response Format**: ☐ Yes ☐ No

**Current Format**:
```json
{
  "example": "response"
}
```

**Standard Error Handling**: ☐ Yes ☐ No

**Error Response Format**:
```json
{
  "error": {
    "code": "",
    "message": ""
  }
}
```

---

## 5️⃣ Code Quality Assessment

### Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Lines of Code | | | |
| Cyclomatic Complexity | | < 10 | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Code Duplication | ___% | < 3% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Test Coverage | ___% | > 80% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Type Hint Coverage | ___% | > 90% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Documentation Coverage | ___% | > 80% | ☐ ✅ ☐ ⚠️ ☐ ❌ |

**Overall Code Quality Score**: ___/10

### Naming Conventions

**Follows Standard Naming Conventions**: ☐ Yes ☐ Partial ☐ No

**Issues Found**:
- 
- 

**Score**: ___/10

### Code Organization

**Code Organization Quality**: ☐ Excellent ☐ Good ☐ Fair ☐ Poor

**Strengths**:
- 
- 

**Weaknesses**:
- 
- 

**Score**: ___/10

---

## 6️⃣ Testing Assessment

### Test Coverage

**Test Suite Exists**: ☐ Yes ☐ No

**Coverage by Layer**:
| Layer | Coverage | Target | Status |
|-------|----------|--------|--------|
| Domain | ___% | > 90% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Application | ___% | > 80% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Infrastructure | ___% | > 70% | ☐ ✅ ☐ ⚠️ ☐ ❌ |
| Presentation | ___% | > 80% | ☐ ✅ ☐ ⚠️ ☐ ❌ |

**Overall Test Coverage Score**: ___/10

### Test Types

| Test Type | Count | Quality | Score |
|-----------|-------|---------|-------|
| Unit Tests | | ☐ Good ☐ Fair ☐ Poor | /10 |
| Integration Tests | | ☐ Good ☐ Fair ☐ Poor | /10 |
| E2E Tests | | ☐ Good ☐ Fair ☐ Poor | /10 |
| Performance Tests | | ☐ Good ☐ Fair ☐ Poor | /10 |

**Test Organization**:
```
tests/
├── [List test structure]
└── 
```

**Follows TDD Practices**: ☐ Yes ☐ Partial ☐ No

**Score**: ___/10

### Test Quality

**Test Naming Conventions**: ☐ Consistent ☐ Inconsistent

**Use of Fixtures**: ☐ Appropriate ☐ Needs Improvement

**Test Independence**: ☐ Yes ☐ Some Dependencies ☐ Many Dependencies

**Mocking Strategy**: ☐ Good ☐ Fair ☐ Poor ☐ None

**Overall Test Quality Score**: ___/10

---

## 7️⃣ Configuration Management

### Configuration Structure

**Configuration Files**:
- [ ] config.yaml
- [ ] config.development.yaml
- [ ] config.production.yaml
- [ ] config.test.yaml

**Environment Variables**:
- [ ] Well documented
- [ ] Follow naming conventions
- [ ] Have defaults
- [ ] Validated on startup

**Configuration Score**: ___/10

### Environment-Specific Configuration

**Supports Multiple Environments**: ☐ Yes ☐ No

**Environment Separation**: ☐ Clear ☐ Mixed ☐ None

**Secrets Management**: ☐ Secure ☐ Needs Improvement ☐ Insecure

**Score**: ___/10

---

## 8️⃣ Documentation Assessment

### Service Documentation

**Documentation Files**:
- [ ] README.md (comprehensive)
- [ ] ARCHITECTURE.md
- [ ] API.md
- [ ] INTEGRATION.md
- [ ] TROUBLESHOOTING.md

**README Quality**:
| Section | Exists | Complete | Quality |
|---------|--------|----------|---------|
| Overview | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Quick Start | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Architecture | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| API Reference | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Configuration | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Development | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Integration | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |
| Troubleshooting | ☐ Yes ☐ No | ☐ Yes ☐ No | /10 |

**Overall Documentation Score**: ___/10

### Code Documentation

**Docstring Coverage**: ___% (target: > 80%)

**Docstring Quality**: ☐ Excellent ☐ Good ☐ Fair ☐ Poor

**Inline Comments**: ☐ Appropriate ☐ Too Many ☐ Too Few

**Score**: ___/10

---

## 9️⃣ Docker & Deployment

### Docker Configuration

**Dockerfile Exists**: ☐ Yes ☐ No

**Docker Compose File**: ☐ Yes ☐ No

**Dockerfile Quality**:
- [ ] Multi-stage build
- [ ] Optimized layers
- [ ] Security best practices
- [ ] Health check defined
- [ ] Non-root user

**Docker Score**: ___/10

### Deployment Modes

**Can Run**:
- [ ] Standalone in terminal
- [ ] Solo in Docker container
- [ ] In Docker Compose (standalone)
- [ ] In full ecosystem

**Health Checks**:
- [ ] Liveness check
- [ ] Readiness check
- [ ] Dependency checks
- [ ] Performance metrics

**Deployment Score**: ___/10

---

## 🔟 Performance & Scalability

### Performance Characteristics

**Response Times**:
| Endpoint | P50 | P95 | P99 | Target |
|----------|-----|-----|-----|--------|
| | | | | < 200ms |

**Throughput**:
- **Requests/Second**: ___ (target: > 100)
- **Concurrent Connections**: ___ (target: > 50)

**Resource Usage**:
- **Memory**: ___ MB (under load)
- **CPU**: ___ % (under load)

**Performance Score**: ___/10

### Scalability

**Horizontal Scaling**: ☐ Supported ☐ Not Supported

**State Management**: ☐ Stateless ☐ Stateful

**Database Connection Pooling**: ☐ Yes ☐ No

**Caching Strategy**: ☐ Yes ☐ No

**Scalability Score**: ___/10

---

## 1️⃣1️⃣ Security Assessment

### Security Practices

**Security Features**:
- [ ] Input validation
- [ ] Output sanitization
- [ ] SQL injection protection
- [ ] Authentication
- [ ] Authorization
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Security headers

**Secrets Management**:
- [ ] No secrets in code
- [ ] Environment variables used
- [ ] Secrets encrypted
- [ ] Rotation supported

**Security Score**: ___/10

### Vulnerabilities

**Known Vulnerabilities**: ☐ Yes ☐ No

**Details**:
| Type | Severity | Status |
|------|----------|--------|
| | | |

---

## 1️⃣2️⃣ Gap Analysis

### Critical Gaps

**Architecture Gaps**:
1. 
2. 
3. 

**Code Quality Gaps**:
1. 
2. 
3. 

**Testing Gaps**:
1. 
2. 
3. 

**Documentation Gaps**:
1. 
2. 
3. 

### Refactoring Scope

**Estimated Effort**: ___person-days

**Complexity**: ⚪ Low | 🟡 Medium | 🟠 High | 🔴 Very High

**Risk Level**: ⚪ Low | 🟡 Medium | 🟠 High | 🔴 Critical

---

## 1️⃣3️⃣ Refactoring Plan

### Phase 1: Audit & Analysis ✅
- [x] Complete this audit
- [ ] Map dependencies
- [ ] Document current behavior
- [ ] Create test baseline

**Duration**: ___ days

### Phase 2: Design & Planning
- [ ] Design DDD domain model
- [ ] Create API specification
- [ ] Plan test strategy
- [ ] Design migration approach

**Duration**: ___ days

### Phase 3: TDD Implementation
- [ ] Domain layer
- [ ] Application layer
- [ ] Infrastructure layer
- [ ] Presentation layer

**Duration**: ___ days

### Phase 4: Integration Testing
- [ ] Service integration tests
- [ ] Docker testing
- [ ] Ecosystem testing
- [ ] Performance testing

**Duration**: ___ days

### Phase 5: Documentation
- [ ] Update README
- [ ] Create architecture diagrams
- [ ] Write API documentation
- [ ] Update integration guides

**Duration**: ___ days

### Phase 6: Deployment
- [ ] Deploy to development
- [ ] Run smoke tests
- [ ] Monitor metrics
- [ ] Production deployment

**Duration**: ___ days

**Total Estimated Duration**: ___ days

---

## 1️⃣4️⃣ Risk Assessment

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| | ⚪ Low 🟡 Med 🟠 High | ⚪ Low 🟡 Med 🟠 High | |
| | ⚪ Low 🟡 Med 🟠 High | ⚪ Low 🟡 Med 🟠 High | |
| | ⚪ Low 🟡 Med 🟠 High | ⚪ Low 🟡 Med 🟠 High | |

---

## 1️⃣5️⃣ Recommendations

### Immediate Actions (Week 1)
1. 
2. 
3. 

### Short-term Actions (Week 2-4)
1. 
2. 
3. 

### Long-term Actions (Month 2-3)
1. 
2. 
3. 

---

## 1️⃣6️⃣ Appendices

### Appendix A: Dependency Map

```
[Diagram or description of service dependencies]
```

### Appendix B: Current Architecture Diagram

```
[Current architecture diagram]
```

### Appendix C: Target Architecture Diagram

```
[Target DDD architecture diagram]
```

### Appendix D: Test Inventory

```
[List of all existing tests]
```

---

## 📊 Audit Score Card

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|---------------|
| Architecture | /10 | 15% | |
| DDD Compliance | /10 | 15% | |
| API Design | /10 | 10% | |
| Code Quality | /10 | 15% | |
| Testing | /10 | 15% | |
| Documentation | /10 | 10% | |
| Docker/Deployment | /10 | 10% | |
| Security | /10 | 10% | |
| **TOTAL** | **/100** | **100%** | **/100** |

---

## ✅ Sign-off

**Auditor**: _________________  
**Date**: _________________  
**Signature**: _________________

**Reviewed By**: _________________  
**Date**: _________________  
**Signature**: _________________

---

**Document Control**  
**Template Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Template Review**: 2025-11-08

