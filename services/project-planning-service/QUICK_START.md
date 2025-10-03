# 🚀 Project Planning Service - Quick Start Guide

Get the AI-powered feature planning service running in 2 minutes!

---

## ⚡ Quick Start (60 seconds)

```bash
# 1. Navigate to service directory
cd /Users/mykalthomas/Documents/work/Hackathon/services/project-planning-service

# 2. Start the service
./start_service.sh

# 3. Test it works
curl http://localhost:5170/health
```

**Done! Service is running on http://localhost:5170** 🎉

---

## 📊 What Can It Do?

### 1. Analyze Features with AI

```bash
curl -X POST http://localhost:5170/api/v1/planning/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "User Authentication",
    "description": "Implement secure user login with email and password",
    "context": {"tech_stack": ["Python", "FastAPI"]},
    "user_id": "demo-user"
  }'
```

**Returns**: Feature ID, complexity score (1-10), story points (Fibonacci), estimated duration, risks, user stories, and technical requirements.

### 2. Decompose into Tasks

```bash
curl -X POST http://localhost:5170/api/v1/planning/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "feature_id": "your-feature-uuid",
    "decomposition_level": "detailed",
    "assign_automatically": false
  }'
```

**Returns**: User stories, implementation tasks, testing tasks, total story points, and estimated duration.

### 3. List Features

```bash
# All features
curl http://localhost:5170/api/v1/planning/features

# Filter by status
curl "http://localhost:5170/api/v1/planning/features?status=analyzed&limit=10"

# Filter by priority
curl "http://localhost:5170/api/v1/planning/features?priority=high"
```

### 4. Get Feature Details

```bash
curl http://localhost:5170/api/v1/planning/features/your-feature-uuid
```

### 5. List Tasks

```bash
# All tasks for a feature
curl "http://localhost:5170/api/v1/planning/tasks?feature_id=your-feature-uuid"

# Tasks assigned to a user
curl "http://localhost:5170/api/v1/planning/tasks?assigned_to=user-123"

# Tasks by status
curl "http://localhost:5170/api/v1/planning/tasks?status=in_progress"
```

---

## 📚 Interactive API Documentation

Once the service is running, visit:

- **Swagger UI**: http://localhost:5170/docs
- **ReDoc**: http://localhost:5170/redoc

Try out all endpoints interactively!

---

## 🧪 Run Tests

```bash
# Unit tests (15 tests)
python3 -m pytest tests/unit/test_feature_entity.py -v

# Functional test (end-to-end demo)
python3 functional_test.py

# Expected: All tests pass ✅
```

---

## 🔍 View Logs

The service automatically logs all operations to the log-collector service:

```bash
# If log-collector is running on port 5080
curl http://localhost:5080/logs | python3 -m json.tool
```

Logs include:
- Business events (feature analysis started/completed)
- API requests with duration
- Integration calls with success/failure
- Feature analysis results

---

## 🛠️ Environment Variables

Optional configuration (defaults provided):

```bash
export DATABASE_PATH="data/project_planning.db"       # SQLite database
export LOG_COLLECTOR_URL="http://localhost:5080"     # Log collector
export INTERPRETER_URL="http://localhost:5120"       # AI interpreter
export LLM_GATEWAY_URL="http://localhost:5055"       # LLM gateway
export USER_STORE_URL="http://localhost:5150"        # User store
```

---

## 📖 Full Documentation

- **README.md** - Comprehensive guide
- **IMPLEMENTATION_STATUS.md** - Architecture details
- **PHASE1_COMPLETION_REPORT.md** - What was built
- **/docs** - Interactive API docs (when running)

---

## ❓ Common Issues

### Import Errors

Make sure PYTHONPATH is set:
```bash
export PYTHONPATH="/Users/mykalthomas/Documents/work/Hackathon:$PYTHONPATH"
```

### Port Already in Use

Kill existing process:
```bash
lsof -ti:5170 | xargs kill -9
```

### Database Not Found

Database is created automatically on first run. Location:
```bash
data/project_planning.db
```

---

## 🎯 What's Next?

### Try It Out

1. Start the service: `./start_service.sh`
2. Open API docs: http://localhost:5170/docs
3. Try the `/api/v1/planning/analyze` endpoint
4. View the results!

### Learn More

- Read the [README.md](README.md) for detailed documentation
- Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for architecture
- View [test examples](tests/) for usage patterns

---

**Ready to plan features with AI?** 🚀

Start the service and visit http://localhost:5170/docs

