<!-- AI_READ_PRIORITY: 4 -->
<!-- AI_TAGS: tdd, checklist, red-green-refactor -->
<!-- AI_KEY_SECTIONS: RED Phase, GREEN Phase, REFACTOR Phase -->

---
ai_metadata:
  purpose: tdd_checklist
  read_priority: 4
  context_level: tactical
  tags:
  - tdd
  - checklist
  - red-green-refactor
  when_to_read: During Phase 3 (TDD Implementation)
  key_sections:
  - RED Phase
  - GREEN Phase
  - REFACTOR Phase
  execution_relevance: phase-specific
  relevant_phases:
  - Phase 3
---

# ✅ TDD Checklist - Test-Driven Development

**Service**: _________________  
**Developer**: _________________  
**Sprint**: _________________  
**Date**: _________________

---

## 📋 Overview

This checklist ensures Test-Driven Development (TDD) practices are followed throughout the refactoring process. Each feature or component must follow the Red-Green-Refactor cycle.

**TDD Principles**:
1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve code while keeping tests green

---

## 🎯 Pre-Development Checklist

### Test Infrastructure Setup

- [ ] Test framework installed (pytest)
- [ ] Test directory structure created
- [ ] Conftest.py configured
- [ ] Pytest.ini configured
- [ ] CI/CD test pipeline configured
- [ ] Code coverage tool configured
- [ ] Test database/fixtures prepared

### Test Environment

- [ ] Test environment variables defined
- [ ] Test configuration files created
- [ ] Mock services configured
- [ ] Test data generators prepared
- [ ] Fixtures defined

---

## 🔴 RED Phase: Write Failing Tests

### Domain Layer Tests

#### Entities
- [ ] **Test: Entity Creation**
  - [ ] Test with valid data
  - [ ] Test with invalid data
  - [ ] Test with missing required fields
  - [ ] Test with invalid field types
  - [ ] Test entity equality
  - [ ] Test entity identity

- [ ] **Test: Entity Validation**
  - [ ] Test business rule validation
  - [ ] Test constraint validation
  - [ ] Test cross-field validation
  - [ ] Test validation error messages

- [ ] **Test: Entity Behavior**
  - [ ] Test state transitions
  - [ ] Test domain logic
  - [ ] Test invariant enforcement

**Entity Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Value Objects
- [ ] **Test: Value Object Creation**
  - [ ] Test with valid values
  - [ ] Test with invalid values
  - [ ] Test immutability
  - [ ] Test equality comparison

- [ ] **Test: Value Object Validation**
  - [ ] Test format validation
  - [ ] Test range validation
  - [ ] Test complex validation rules

**Value Object Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Aggregates
- [ ] **Test: Aggregate Creation**
  - [ ] Test aggregate root creation
  - [ ] Test child entity creation
  - [ ] Test aggregate consistency

- [ ] **Test: Aggregate Behavior**
  - [ ] Test command handling
  - [ ] Test event generation
  - [ ] Test transaction boundaries
  - [ ] Test consistency enforcement

**Aggregate Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Domain Services
- [ ] **Test: Domain Service Logic**
  - [ ] Test core business logic
  - [ ] Test cross-entity operations
  - [ ] Test domain calculations
  - [ ] Test domain rules

**Domain Service Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Domain Events
- [ ] **Test: Event Creation**
  - [ ] Test event data
  - [ ] Test event metadata
  - [ ] Test event serialization

**Domain Event Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

### Application Layer Tests

#### Use Cases / Commands
- [ ] **Test: Command Validation**
  - [ ] Test with valid inputs
  - [ ] Test with invalid inputs
  - [ ] Test with missing data
  - [ ] Test business rule validation

- [ ] **Test: Command Execution**
  - [ ] Test successful execution
  - [ ] Test failure scenarios
  - [ ] Test transaction handling
  - [ ] Test event publishing

- [ ] **Test: Command Authorization**
  - [ ] Test with authorized user
  - [ ] Test with unauthorized user
  - [ ] Test permission checks

**Command Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Queries
- [ ] **Test: Query Validation**
  - [ ] Test with valid parameters
  - [ ] Test with invalid parameters
  - [ ] Test with missing parameters

- [ ] **Test: Query Execution**
  - [ ] Test data retrieval
  - [ ] Test filtering
  - [ ] Test sorting
  - [ ] Test pagination
  - [ ] Test empty results

- [ ] **Test: Query Authorization**
  - [ ] Test data access permissions
  - [ ] Test field-level permissions

**Query Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### DTOs
- [ ] **Test: DTO Validation**
  - [ ] Test required fields
  - [ ] Test field types
  - [ ] Test field constraints
  - [ ] Test serialization
  - [ ] Test deserialization

**DTO Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

### Infrastructure Layer Tests

#### Repositories
- [ ] **Test: Create Operations**
  - [ ] Test successful create
  - [ ] Test duplicate handling
  - [ ] Test constraint violations
  - [ ] Test transaction rollback

- [ ] **Test: Read Operations**
  - [ ] Test find by ID
  - [ ] Test find by criteria
  - [ ] Test find with relations
  - [ ] Test not found scenarios
  - [ ] Test pagination

- [ ] **Test: Update Operations**
  - [ ] Test successful update
  - [ ] Test concurrent updates
  - [ ] Test not found update
  - [ ] Test partial updates

- [ ] **Test: Delete Operations**
  - [ ] Test successful delete
  - [ ] Test cascade deletes
  - [ ] Test soft deletes
  - [ ] Test not found delete

**Repository Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### External Service Integrations
- [ ] **Test: Service Calls**
  - [ ] Test successful call
  - [ ] Test with invalid response
  - [ ] Test timeout handling
  - [ ] Test network errors
  - [ ] Test retry logic
  - [ ] Test circuit breaker

**Integration Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Event Publishing
- [ ] **Test: Event Publishing**
  - [ ] Test event publication
  - [ ] Test publish failure
  - [ ] Test event serialization
  - [ ] Test publish retry

**Event Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

### Presentation Layer Tests

#### API Controllers
- [ ] **Test: Request Handling**
  - [ ] Test valid requests
  - [ ] Test invalid requests
  - [ ] Test missing parameters
  - [ ] Test invalid content type

- [ ] **Test: Response Formatting**
  - [ ] Test success responses
  - [ ] Test error responses
  - [ ] Test status codes
  - [ ] Test response headers

- [ ] **Test: Authentication**
  - [ ] Test with valid credentials
  - [ ] Test with invalid credentials
  - [ ] Test with missing credentials
  - [ ] Test token validation

- [ ] **Test: Authorization**
  - [ ] Test with authorized user
  - [ ] Test with unauthorized user
  - [ ] Test role-based access

**Controller Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

#### Middleware
- [ ] **Test: Request Processing**
  - [ ] Test request logging
  - [ ] Test error handling
  - [ ] Test CORS handling
  - [ ] Test rate limiting

**Middleware Tests Written**: ___/___  
**All Tests Failing (Red)**: ☐ Yes ☐ No

---

## 🟢 GREEN Phase: Make Tests Pass

### Implementation Checklist

#### Domain Layer Implementation
- [ ] Entity classes implemented
- [ ] Value object classes implemented
- [ ] Aggregate root implemented
- [ ] Domain services implemented
- [ ] Domain events implemented
- [ ] Repository interfaces defined

**Domain Tests Passing**: ___/___  
**All Tests Green**: ☐ Yes ☐ No

#### Application Layer Implementation
- [ ] Use cases implemented
- [ ] Commands implemented
- [ ] Queries implemented
- [ ] DTOs implemented
- [ ] Validators implemented
- [ ] Application services implemented

**Application Tests Passing**: ___/___  
**All Tests Green**: ☐ Yes ☐ No

#### Infrastructure Layer Implementation
- [ ] Repository implementations
- [ ] Database configurations
- [ ] External service clients
- [ ] Event publishers
- [ ] Caching implementation

**Infrastructure Tests Passing**: ___/___  
**All Tests Green**: ☐ Yes ☐ No

#### Presentation Layer Implementation
- [ ] API controllers implemented
- [ ] Request/response models
- [ ] Middleware implemented
- [ ] Error handlers implemented
- [ ] OpenAPI documentation

**Presentation Tests Passing**: ___/___  
**All Tests Green**: ☐ Yes ☐ No

### Verification
- [ ] All unit tests pass
- [ ] No failing tests
- [ ] No skipped tests
- [ ] Test execution time reasonable

**Total Tests**: ___  
**Passing Tests**: ___  
**Failing Tests**: ___  
**Skipped Tests**: ___

---

## 🔄 REFACTOR Phase: Improve Code

### Code Quality Improvements

#### Remove Duplication
- [ ] Identified duplicate code
- [ ] Extracted common functionality
- [ ] Created reusable components
- [ ] Updated tests (still green)

**Duplication**: Before: ___%  After: ___%

#### Improve Naming
- [ ] Reviewed variable names
- [ ] Reviewed function names
- [ ] Reviewed class names
- [ ] Updated documentation
- [ ] Tests still passing

#### Simplify Logic
- [ ] Identified complex methods
- [ ] Broke down complex functions
- [ ] Simplified conditionals
- [ ] Reduced nesting
- [ ] Tests still passing

**Cyclomatic Complexity**: Before: ___  After: ___

#### Optimize Performance
- [ ] Identified bottlenecks
- [ ] Optimized algorithms
- [ ] Added caching where appropriate
- [ ] Optimized database queries
- [ ] Tests still passing

#### Improve Structure
- [ ] Reorganized code structure
- [ ] Improved module organization
- [ ] Enhanced separation of concerns
- [ ] Tests still passing

### Refactoring Verification
- [ ] All tests still passing
- [ ] Code coverage maintained/improved
- [ ] Performance maintained/improved
- [ ] No new linting errors
- [ ] Documentation updated

**Test Coverage**: Before: ___%  After: ___%

---

## 🧪 Integration Testing

### Service Integration Tests

#### Internal Integration
- [ ] **Test: Cross-Layer Integration**
  - [ ] Domain → Application
  - [ ] Application → Infrastructure
  - [ ] Infrastructure → Presentation

- [ ] **Test: Database Integration**
  - [ ] Connection handling
  - [ ] Transaction handling
  - [ ] Migration compatibility

- [ ] **Test: Cache Integration**
  - [ ] Cache hits
  - [ ] Cache misses
  - [ ] Cache invalidation

**Internal Integration Tests**: ___/___  
**All Tests Passing**: ☐ Yes ☐ No

#### External Integration
- [ ] **Test: Service-to-Service**
  - [ ] Dependent service calls
  - [ ] Event publishing/subscription
  - [ ] Circuit breaker behavior
  - [ ] Retry logic

- [ ] **Test: External APIs**
  - [ ] Third-party API calls
  - [ ] Error handling
  - [ ] Timeout handling

**External Integration Tests**: ___/___  
**All Tests Passing**: ☐ Yes ☐ No

---

## 🎭 End-to-End Testing

### E2E Test Scenarios

- [ ] **Test: Happy Path**
  - [ ] Complete user workflow
  - [ ] All services integrated
  - [ ] Data persistence verified

- [ ] **Test: Error Scenarios**
  - [ ] Invalid input handling
  - [ ] Service unavailable
  - [ ] Timeout scenarios
  - [ ] Data consistency

- [ ] **Test: Edge Cases**
  - [ ] Boundary values
  - [ ] Large datasets
  - [ ] Concurrent operations

**E2E Tests**: ___/___  
**All Tests Passing**: ☐ Yes ☐ No

---

## 📊 Performance Testing

### Performance Test Scenarios

- [ ] **Test: Load Testing**
  - [ ] Normal load (100 req/s)
  - [ ] High load (500 req/s)
  - [ ] Peak load (1000 req/s)

- [ ] **Test: Stress Testing**
  - [ ] Gradual load increase
  - [ ] Sudden load spike
  - [ ] Sustained high load

- [ ] **Test: Endurance Testing**
  - [ ] 24-hour stability test
  - [ ] Memory leak detection
  - [ ] Resource cleanup

**Performance Targets Met**: ☐ Yes ☐ No

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P95 Response Time | < 200ms | | ☐ ✅ ☐ ❌ |
| Throughput | > 100 req/s | | ☐ ✅ ☐ ❌ |
| Error Rate | < 0.1% | | ☐ ✅ ☐ ❌ |
| Memory Usage | Stable | | ☐ ✅ ☐ ❌ |

---

## 📈 Test Coverage Analysis

### Coverage Metrics

| Layer | Line Coverage | Branch Coverage | Target |
|-------|--------------|----------------|--------|
| Domain | ___% | ___% | > 90% |
| Application | ___% | ___% | > 80% |
| Infrastructure | ___% | ___% | > 70% |
| Presentation | ___% | ___% | > 80% |
| **Overall** | **___%** | **___%** | **> 80%** |

### Coverage Gaps

**Uncovered Code**:
- Module: _________________ (Lines: __-__, Reason: ____________)
- Module: _________________ (Lines: __-__, Reason: ____________)

**Justification for Gaps**:
- 
- 

---

## 🔍 Code Review Checklist

### Test Quality Review

- [ ] Tests are independent
- [ ] Tests are repeatable
- [ ] Tests are fast
- [ ] Tests are readable
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test names are descriptive
- [ ] Fixtures are well-organized
- [ ] Mocks are appropriate
- [ ] Test data is realistic
- [ ] Edge cases are covered

### Code Quality Review

- [ ] Code follows SOLID principles
- [ ] Code follows DRY principle
- [ ] Code follows KISS principle
- [ ] Naming conventions followed
- [ ] Type hints present
- [ ] Docstrings present
- [ ] Error handling comprehensive
- [ ] Security best practices followed

---

## ✅ Final Checklist

### TDD Completion Criteria

- [ ] All tests written before code
- [ ] All tests initially failed (Red)
- [ ] Minimal code written to pass tests (Green)
- [ ] Code refactored for quality (Refactor)
- [ ] Test coverage > 80%
- [ ] All tests passing
- [ ] No skipped tests
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Performance tests passing
- [ ] Code review completed
- [ ] Documentation updated

**TDD Process Complete**: ☐ Yes ☐ No

---

## 📝 Notes & Observations

### Lessons Learned

**What Went Well**:
- 
- 
- 

**What Could Be Improved**:
- 
- 
- 

**Blockers Encountered**:
- 
- 
- 

### Metrics Summary

| Metric | Value |
|--------|-------|
| Total Tests Written | |
| Test Execution Time | |
| Code Coverage | |
| Cyclomatic Complexity | |
| Lines of Code | |
| Bugs Found in Testing | |
| Time to Green (per test) | |

---

## 🎯 Sign-off

**Developer**: _________________  
**Date**: _________________  
**All TDD Practices Followed**: ☐ Yes ☐ No

**Reviewed By**: _________________  
**Date**: _________________  
**Approved**: ☐ Yes ☐ No

**Comments**:
```
[Reviewer comments]
```

---

**Document Control**  
**Template Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Review**: 2025-11-08

---

## 📚 TDD Resources

### Quick Reference

**Red Phase**:
1. Write a test for the next bit of functionality
2. Run all tests and verify the new test fails
3. Write just enough code to make test pass

**Green Phase**:
1. Write minimal production code
2. Run all tests
3. All tests pass

**Refactor Phase**:
1. Eliminate duplication
2. Improve names
3. Simplify logic
4. Run all tests to ensure they still pass

### Testing Patterns

**AAA Pattern**:
```python
def test_create_document_with_valid_data_returns_document():
    # Arrange
    title = "Test Document"
    content = "Test content"
    service = DocumentService()
    
    # Act
    result = service.create_document(title, content)
    
    # Assert
    assert result.title == title
    assert result.content == content
```

**Given-When-Then Pattern**:
```python
def test_document_creation():
    # Given a valid title and content
    title = "Test Document"
    content = "Test content"
    
    # When creating a document
    doc = create_document(title, content)
    
    # Then the document should be created successfully
    assert doc is not None
    assert doc.title == title
```

---

**End of TDD Checklist**

