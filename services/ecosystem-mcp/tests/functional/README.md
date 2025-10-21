# Functional & Smoke Tests

This directory contains functional tests that validate the entire 4-phase system by running it against our own codebase.

## Test Philosophy

These tests serve dual purposes:

1. **Functional Testing** - Validate that each phase works correctly
2. **Smoke Testing** - Quick validation that the system is operational

## Test Targets

Tests run against our three services:
- `ecosystem-mcp` - Main service (largest, most complex)
- `ecosystem-mcp-dashboard` - Streamlit dashboard
- `ecosystem-mcp-embedding` - FastEmbed embedding service

## Test Coverage

### Phase 1: Discovery Engine
- ✅ Repository scanning
- ✅ File classification
- ✅ Processing plan generation

### Phase 2: Sub-Job Execution
- (Tested via integration tests)

### Phase 3: Multi-File Analysis
- ✅ Technology stack detection
- ✅ Architecture pattern detection
- ✅ Service boundary detection
- ✅ Complete analysis engine

### Phase 4: Documentation Generation
- ✅ Architecture documentation
- ✅ Component documentation
- ✅ API reference documentation
- ✅ Complete 5-pass generation

### Integration
- ✅ Complete pipeline (Phase 1 → 3 → 4)

## Running Tests

### Quick Smoke Test (Recommended)
```bash
python run_smoke_tests.py --quick
```

### Full Functional Suite
```bash
# All functional tests
pytest tests/functional/ -v -m functional

# Just Phase 1
pytest tests/functional/ -v -k "test_phase1"

# Just Phase 3
pytest tests/functional/ -v -k "test_phase3"

# Just Phase 4
pytest tests/functional/ -v -k "test_phase4"

# Complete integration test
pytest tests/functional/ -v -k "test_complete_pipeline"
```

### With Output Saving
```bash
python run_smoke_tests.py --save-output
```

This will save generated documentation to `smoke_test_output/`.

## Test Markers

- `@pytest.mark.functional` - Functional test
- `@pytest.mark.slow` - Slow test (integration)
- `@pytest.mark.asyncio` - Async test

## Expected Results

### Phase 1 (Discovery)
- **ecosystem-mcp**: 50+ files, 10+ sub-jobs
- **ecosystem-mcp-dashboard**: 10+ files, 5+ sub-jobs
- **ecosystem-mcp-embedding**: 5+ files, 3+ sub-jobs

### Phase 3 (Analysis)
- **Languages**: Python detected
- **Frameworks**: FastAPI, SQLAlchemy, Streamlit (depending on service)
- **Pattern**: Microservices or Layered
- **Modularity**: > 0.5

### Phase 4 (Documentation)
- **Artifacts**: 10+ documents
- **Words**: 1,000+ words
- **Quality**: > 0.5
- **Passes**: 5 complete

## Output Artifacts

Generated documentation includes:

1. **Architecture Docs**
   - System overview
   - Pattern analysis
   - Technology stack
   - Component map
   - Dependency analysis
   - Service architecture

2. **Component Docs**
   - Service-specific documentation
   - API endpoints
   - Setup instructions
   - Testing approach

3. **API Reference**
   - API overview
   - Endpoint documentation
   - Authentication
   - Error handling
   - Best practices

4. **Examples**
   - Quick start guide
   - Usage examples
   - Integration guide
   - Common workflows

5. **Synthesis**
   - Master README
   - Documentation map
   - Glossary

## Validation Criteria

Tests validate:
- ✅ No exceptions thrown
- ✅ Expected number of artifacts generated
- ✅ Content length > minimum thresholds
- ✅ Required sections present
- ✅ Quality scores above thresholds
- ✅ Expected technologies detected
- ✅ Architecture patterns identified

## Performance

Approximate test times:
- **Quick smoke test**: 30-60 seconds
- **Phase 1 tests**: 10 seconds
- **Phase 3 tests**: 20 seconds
- **Phase 4 tests**: 30 seconds
- **Full integration**: 60 seconds

## Troubleshooting

### Import Errors
Ensure you're running from the service root:
```bash
cd services/ecosystem-mcp
python run_smoke_tests.py
```

### Path Not Found
Tests expect services at specific paths. Update `TEST_TARGETS` in `test_full_pipeline.py` if your paths differ.

### Slow Tests
Use `--quick` flag to skip integration tests:
```bash
python run_smoke_tests.py --quick
```

## CI/CD Integration

To integrate into CI/CD:

```bash
# In CI script
cd services/ecosystem-mcp
python run_smoke_tests.py --quick
if [ $? -ne 0 ]; then
    echo "Smoke tests failed!"
    exit 1
fi
```

## Monitoring Output

Generated documentation can be inspected to verify:
- Completeness
- Accuracy
- Quality
- Formatting

Use `--save-output` to review artifacts:
```bash
python run_smoke_tests.py --save-output
cd smoke_test_output/[timestamp]
ls -la  # View generated files
```

## Next Steps

After smoke tests pass:
1. Review generated documentation for quality
2. Run full test suite with `pytest`
3. Perform manual validation of complex scenarios
4. Deploy to staging environment
5. Monitor production metrics

## Contributing

When adding new features:
1. Add corresponding functional tests
2. Ensure smoke tests still pass
3. Update expected results if needed
4. Document any new test targets

