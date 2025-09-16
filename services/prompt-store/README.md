# Prompt Store v2.0 - Domain-Driven Architecture

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**Advanced prompt management with domain-driven architecture, comprehensive analytics, bulk operations, and real-time notifications.**

- **Port**: 5110
- **Architecture**: Domain-Driven Design (DDD)
- **Database**: SQLite with FTS and WAL mode
- **Cache**: Redis-backed multi-level caching
- **Tests**: 200+ comprehensive test cases

## 🚀 What's New in v2.0

### Domain-Driven Architecture
- **Clean Architecture**: Separated concerns with `core/`, `domain/`, `infrastructure/`, `db/`, `api/` layers
- **Repository Pattern**: Consistent data access layer with SQLite optimizations
- **Service Layer**: Business logic encapsulation with validation and caching
- **Handler Layer**: HTTP request/response mapping with error handling

### Advanced Features
- **Bulk Operations**: Asynchronous bulk prompt processing with progress tracking
- **LLM-Assisted Prompt Refinement**: AI-powered prompt improvement with doc_store integration
- **Lifecycle Management**: Draft → Published → Deprecated → Archived workflow
- **Semantic Relationships**: Prompt interconnections (extends, references, alternatives)
- **Performance Caching**: Redis-backed caching with automatic invalidation
- **Real-time Notifications**: Webhook system for prompt changes and A/B test results
- **Enhanced Search**: Full-text search with faceting and suggestions
- **Advanced Analytics**: Usage patterns, performance insights, drift detection

### Production Ready
- **Database Migrations**: Automatic schema initialization with indexes
- **Connection Pooling**: Efficient database connection management
- **Health Checks**: Comprehensive service health monitoring
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Configuration**: Environment-based configuration with fallbacks

## Overview and Role in Ecosystem

The Prompt Store serves as the central repository for all AI prompts across the platform, providing:

- **Version Control**: Full prompt versioning with rollback capabilities
- **A/B Testing**: Statistical comparison of prompt variants
- **Analytics**: Usage tracking and performance optimization insights
- **Template System**: Variable substitution and dynamic prompt generation
- **Bulk Operations**: Efficient batch processing for large prompt sets
- **Caching**: High-performance prompt retrieval with Redis
- **Notifications**: Real-time updates via webhooks

## Architecture

```
services/prompt_store/
├── core/                    # Domain entities and base classes
│   ├── entities.py         # Core domain entities
│   ├── models.py          # Pydantic API models
│   ├── repository.py      # Base repository pattern
│   ├── service.py         # Base service pattern
│   └── handler.py         # Base handler pattern
├── domain/                 # Business domains
│   ├── prompts/           # Prompt management domain
│   ├── ab_testing/        # A/B testing domain
│   ├── analytics/         # Analytics domain
│   ├── bulk/              # Bulk operations domain
│   ├── lifecycle/         # Lifecycle management domain
│   ├── relationships/     # Prompt relationships domain
│   └── notifications/     # Notification system domain
├── infrastructure/         # Technical infrastructure
│   ├── cache.py           # Redis/local caching
│   └── utils.py           # Utility functions
├── db/                     # Database layer
│   ├── schema.py          # Table definitions & migrations
│   ├── connection.py      # Connection management
│   └── queries.py         # Query utilities
├── api/                    # API routes (future)
└── main_new.py            # Domain-driven service entry point
```

## API v2.0 Endpoints

### Prompt Management
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/prompts` | Create prompt with validation |
| GET | `/api/v1/prompts` | List prompts with filtering |
| GET | `/api/v1/prompts/search/{category}/{name}` | Get and fill prompt template |
| PUT | `/api/v1/prompts/{id}` | Update prompt with versioning |
| DELETE | `/api/v1/prompts/{id}` | Soft delete prompt |

### Advanced Features
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/prompts/{id}/fork` | Fork prompt to new variant |
| PUT | `/api/v1/prompts/{id}/content` | Update content with versioning |
| GET | `/api/v1/prompts/{id}/drift` | Detect prompt drift |
| GET | `/api/v1/prompts/{id}/suggestions` | Get improvement suggestions |
| POST | `/api/v1/prompts/search` | Advanced full-text search |

### Bulk Operations
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/bulk/prompts` | Bulk create prompts |
| PUT | `/api/v1/bulk/prompts/tags` | Bulk update tags |
| GET | `/api/v1/bulk/operations` | List bulk operations |
| GET | `/api/v1/bulk/operations/{id}` | Get operation status |

### Analytics & Insights
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/analytics/summary` | Comprehensive analytics |
| GET | `/api/v1/analytics/prompts/{id}` | Prompt-specific analytics |
| GET | `/api/v1/analytics/usage` | Usage patterns over time |

### A/B Testing
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ab-tests` | Create A/B test |
| GET | `/api/v1/ab-tests` | List A/B tests |
| GET | `/api/v1/ab-tests/{id}/select` | Select prompt variant |
| GET | `/api/v1/ab-tests/{id}/results` | Get test results |

### Prompt Refinement
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/prompts/{id}/refine` | Start LLM-assisted refinement |
| GET | `/api/v1/refinement/sessions/{id}` | Get refinement status |
| GET | `/api/v1/prompts/{id}/refinement/compare` | Compare prompt versions |
| GET | `/api/v1/refinement/compare/{a}/{b}` | Compare refinement documents |
| POST | `/api/v1/prompts/{id}/refinement/apply/{session}` | Apply refined prompt |
| GET | `/api/v1/prompts/{id}/refinement/history` | Get refinement history |

### Relationships & Versioning
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/prompts/{id}/relationships` | Add prompt relationship |
| GET | `/api/v1/prompts/{id}/relationships` | Get prompt relationships |
| GET | `/api/v1/prompts/{id}/versions` | Get version history |
| POST | `/api/v1/prompts/{id}/versions/{v}/rollback` | Rollback to version |

### Lifecycle Management
| Method | Path | Description |
|--------|------|-------------|
| PUT | `/api/v1/prompts/{id}/lifecycle` | Update lifecycle status |
| GET | `/api/v1/prompts/lifecycle/{status}` | Get prompts by status |

### Cache Management
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cache/stats` | Cache performance stats |
| POST | `/api/v1/cache/invalidate` | Invalidate cache patterns |
| POST | `/api/v1/cache/warmup` | Warm up cache |

### Notifications
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/webhooks` | Register webhook |
| GET | `/api/v1/webhooks` | List webhooks |
| GET | `/api/v1/notifications/stats` | Notification statistics |

## Quickstart

### Development with Auto-reload
```bash
# Initialize database
python scripts/populate_promptstore_test_data.py --seed

# Run with auto-reload
python run_promptstore.py --reload
```

### Production
```bash
# Run production service
python run_promptstore.py
```

### Test Data Population
```bash
# Populate with realistic test data
python scripts/populate_promptstore_test_data.py --seed

# This creates:
# - 7 sample prompts across different categories
# - A/B test configurations
# - Usage analytics data
# - Prompt relationships
# - Bulk operation examples
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMPT_STORE_DB` | SQLite database path | `services/prompt_store/prompt_store.db` |
| `PROMPT_STORE_PORT` | Service port | `5110` |
| `PROMPT_STORE_ENV` | Environment | `development` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

## Prompt Refinement Feature

### Overview
The Prompt Refinement feature provides LLM-assisted prompt improvement with a complete workflow:

1. **Initiate Refinement**: Send prompt to LLM service with refinement instructions
2. **LLM Processing**: AI analyzes and improves the prompt
3. **Document Storage**: Results stored in doc_store for review
4. **User Review**: Read and evaluate refinement results
5. **Iterative Refinement**: Option to refine further or accept changes
6. **Version Control**: Compare versions and apply changes with proper versioning

### Workflow Example
```bash
# 1. Create a prompt
curl -X POST http://localhost:5110/api/v1/prompts \
  -d '{"name":"blog_intro","category":"writing","content":"Write a blog introduction"}'

# 2. Start refinement
curl -X POST http://localhost:5110/api/v1/prompts/{prompt_id}/refine \
  -d '{"refinement_instructions":"Make it more engaging and SEO-friendly","llm_service":"interpreter"}'

# 3. Check status
curl http://localhost:5110/api/v1/refinement/sessions/{session_id}

# 4. Compare versions (when complete)
curl http://localhost:5110/api/v1/prompts/{prompt_id}/refinement/compare

# 5. Apply refined version
curl -X POST http://localhost:5110/api/v1/prompts/{prompt_id}/refinement/apply/{session_id}
```

### Integration with Doc Store
- Refinement results automatically stored as documents
- Full document versioning and search capabilities
- Cross-referencing between prompts and refinement sessions
- Audit trail of all refinement activities

## Testing

### Test Structure (Domain-Driven)
```
tests/unit/prompt_store/
├── core/                    # Core layer tests
├── domain/                  # Domain layer tests
│   ├── prompts/            # Prompt domain tests
│   ├── ab_testing/         # A/B testing tests
│   ├── analytics/          # Analytics tests
│   ├── bulk/               # Bulk operations tests
│   ├── refinement/         # Prompt refinement tests
│   └── ...
├── infrastructure/          # Infrastructure tests
├── api/                     # API endpoint tests
└── conftest.py             # Test fixtures
```

### Running Tests
```bash
# Run all prompt_store tests
pytest tests/unit/prompt_store/ -v

# Run with parallel execution
pytest tests/unit/prompt_store/ -n auto

# Run specific domain tests
pytest tests/unit/prompt_store/domain/prompts/ -v
```

### Test Coverage
- **200+ Test Cases**: Comprehensive coverage of all domains
- **Parallel Execution**: Optimized for CI/CD pipelines
- **Realistic Fixtures**: Production-like test data
- **Integration Tests**: Cross-domain workflow testing

## Performance Features

### Caching Strategy
- **Multi-level Cache**: Redis + Local cache fallback
- **Intelligent Invalidation**: Pattern-based cache clearing
- **Usage-based Warming**: Frequently accessed prompts cached
- **TTL Management**: Configurable cache expiration

### Database Optimizations
- **FTS Support**: Full-text search on prompts
- **WAL Mode**: Write-Ahead Logging for concurrency
- **Connection Pooling**: Efficient connection reuse
- **Indexed Queries**: Optimized for common access patterns

### Bulk Operations
- **Asynchronous Processing**: Non-blocking bulk operations
- **Progress Tracking**: Real-time operation status
- **Error Handling**: Partial failure support
- **Resource Management**: Memory-efficient processing

## Migration from v1.x

The v2.0 architecture is designed for gradual migration:

1. **Database Migration**: Automatic schema updates
2. **API Compatibility**: v1 endpoints remain functional
3. **Incremental Adoption**: New features can be adopted per domain
4. **Backward Compatibility**: Existing integrations continue working

## Development

### Adding New Domains
1. Create domain directory structure
2. Implement repository, service, and handler layers
3. Add API routes following REST conventions
4. Create comprehensive tests
5. Update documentation

### Code Quality
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Structured exception handling
- **Testing**: 90%+ test coverage target

## Related Services

- **Interpreter**: [../interpreter/README.md](../interpreter/README.md) - Uses prompts for AI interactions
- **Doc Store**: [../doc_store/README.md](../doc_store/README.md) - Inspiration for this architecture
- **CLI**: [../cli/README.md](../cli/README.md) - Administrative interface
- **Services Index**: [../README_SERVICES.md](../README_SERVICES.md)

---

**🎉 Prompt Store v2.0**: Enterprise-grade prompt management with domain-driven architecture, ready for production deployment!
