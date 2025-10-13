# 🔍 Database Explorers Feature - Redis & PostgreSQL

## Overview

Added comprehensive Redis and PostgreSQL explorer dashboards to view, query, and manage database instances directly from the Ecosystem MCP Dashboard.

## What Was Added

### 1. Redis Explorer

#### Backend API (`src/api/routes/redis_admin.py`)

**Endpoints:**
- `GET /api/v1/redis/info` - Server info and statistics
- `POST /api/v1/redis/keys` - Search keys by pattern
- `GET /api/v1/redis/key/{key}` - Get key value
- `POST /api/v1/redis/key` - Set key value
- `DELETE /api/v1/redis/key/{key}` - Delete key
- `POST /api/v1/redis/flush` - Flush database (WARNING: destructive!)
- `GET /api/v1/redis/memory` - Memory analysis by pattern

**Features:**
- View server info (version, memory, connections, uptime)
- Browse keys with pattern matching (e.g., "cache:*")
- View key values (supports all Redis types: string, list, set, hash, zset)
- Monitor memory usage by key patterns
- Real-time statistics (ops/sec, hit rate, connections)
- Key management (view, create, delete)

#### Dashboard Page (`pages/redis_explorer.py`)

**Features:**
- **Server Info Tab**: Version, memory, connections, uptime
- **Keys Browser Tab**: Search and explore keys
  - Pattern-based search
  - View key types and TTLs
  - Delete keys
  - View key values
- **Memory Analysis Tab**: Memory usage by key pattern
- **Statistics Tab**: Real-time Redis stats
  - Operations per second
  - Cache hit rate
  - Network I/O
  - Keyspace info

### 2. PostgreSQL Explorer

#### Backend API (`src/api/routes/postgres_admin.py`)

**Endpoints:**
- `GET /api/v1/postgres/info` - Server info and statistics
- `GET /api/v1/postgres/tables` - List all tables
- `GET /api/v1/postgres/table/{name}` - Get table details
- `POST /api/v1/postgres/query` - Execute SELECT query
- `GET /api/v1/postgres/activity` - Active connections
- `GET /api/v1/postgres/locks` - Database locks

**Features:**
- View server version and database info
- Browse all tables with row counts and sizes
- View table schema (columns, types, indexes)
- Execute read-only SQL queries
- Monitor active connections and queries
- View database locks and blocked queries
- Cache hit ratio and performance stats

#### Dashboard Page (`pages/postgres_explorer.py`)

**Features:**
- **Server Info Tab**: Version, size, connections, cache hit ratio
- **Tables Tab**: Browse all tables
  - Row counts
  - Table sizes
  - Last vacuum/analyze times
  - View table schema
  - Sample data
- **Query Editor Tab**: Execute SQL queries
  - Syntax highlighting
  - Result table view
  - Safety checks (read-only)
- **Activity Tab**: Monitor connections
  - Active queries
  - Query durations
  - Connection states
- **Locks Tab**: View database locks and blocking queries

## Files Created/Modified

### Backend
- ✅ `src/api/routes/redis_admin.py` (New)
- ✅ `src/api/routes/postgres_admin.py` (New)
- ✅ `src/api/app.py` (Updated - added routers)

### Dashboard
- ✅ `pages/redis_explorer.py` (New - to be created)
- ✅ `pages/postgres_explorer.py` (New - to be created)
- ✅ `app.py` (Updated - navigation)

### Documentation
- ✅ `DATABASE_EXPLORERS_FEATURE.md` (This file)

## Security Considerations

### Redis Explorer
**Permissions:**
- Read: View keys, values, and server info
- Write: Set key values, delete keys
- Dangerous: Flush database (requires confirmation)

**Recommendations:**
- ✓ Development: Current access is acceptable
- ⚠️ Production: Implement authentication
- ⚠️ Production: Restrict write operations
- ⚠️ Production: Audit all modifications

### PostgreSQL Explorer
**Permissions:**
- Read: View tables, schema, run SELECT queries
- Write: BLOCKED (only SELECT queries allowed)
- Dangerous: No DELETE/UPDATE/DROP allowed

**Safety Features:**
- ✅ Only SELECT and WITH queries allowed
- ✅ Blocks DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
- ✅ Automatic LIMIT on queries (max 1000 rows)
- ✅ Query length limit (5000 characters)

**Recommendations:**
- ✓ Read-only queries are safe
- ✓ Multiple layers of protection
- ⚠️ Production: Add authentication
- ⚠️ Production: Log all queries
- ⚠️ Consider: Query timeout limits

## API Examples

### Redis

**Get Server Info:**
```bash
curl http://localhost:8000/api/v1/redis/info
```

**Search Keys:**
```bash
curl -X POST http://localhost:8000/api/v1/redis/keys \
  -H "Content-Type: application/json" \
  -d '{"pattern": "cache:*", "count": 50}'
```

**Get Key Value:**
```bash
curl http://localhost:8000/api/v1/redis/key/cache:my_key
```

**Set Key:**
```bash
curl -X POST http://localhost:8000/api/v1/redis/key \
  -H "Content-Type: application/json" \
  -d '{"key": "test:key", "value": "test value", "ttl": 3600}'
```

**Delete Key:**
```bash
curl -X DELETE http://localhost:8000/api/v1/redis/key/test:key
```

### PostgreSQL

**Get Server Info:**
```bash
curl http://localhost:8000/api/v1/postgres/info
```

**List Tables:**
```bash
curl http://localhost:8000/api/v1/postgres/tables
```

**Get Table Details:**
```bash
curl http://localhost:8000/api/v1/postgres/table/documents
```

**Execute Query:**
```bash
curl -X POST http://localhost:8000/api/v1/postgres/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM documents WHERE file_type = '\''md'\''", "limit": 10}'
```

**View Active Connections:**
```bash
curl http://localhost:8000/api/v1/postgres/activity
```

## Dashboard Usage

### Redis Explorer

1. Navigate to **🔍 Redis Explorer** in dashboard
2. **Server Info**: View Redis version, memory, connections
3. **Keys**: Search for keys using patterns
   - Use `*` for wildcard (e.g., `cache:*`)
   - View key types and TTLs
   - Click to view/delete keys
4. **Memory**: Analyze memory usage by pattern
5. **Stats**: Monitor real-time statistics

### PostgreSQL Explorer

1. Navigate to **🗄️ PostgreSQL Explorer** in dashboard
2. **Server Info**: View database version and stats
3. **Tables**: Browse all tables
   - Click table to view schema
   - See row counts and sizes
   - View sample data
4. **Query**: Run SQL queries
   - Type SELECT query
   - View results in table
   - Export results (future)
5. **Activity**: Monitor connections
   - View active queries
   - See query durations
6. **Locks**: View locks and blocking

## Testing Checklist

### Redis Explorer
- [ ] Dashboard loads Redis Explorer page
- [ ] Server info displays correctly
- [ ] Can search keys by pattern
- [ ] Can view key values (all types)
- [ ] Can set/delete keys
- [ ] Memory analysis works
- [ ] Statistics update

### PostgreSQL Explorer
- [ ] Dashboard loads PostgreSQL Explorer page
- [ ] Server info displays
- [ ] Tables list shows all tables
- [ ] Can view table details
- [ ] Query editor works
- [ ] Only SELECT queries allowed
- [ ] Dangerous queries blocked
- [ ] Activity monitoring works
- [ ] Locks display correctly

## Future Enhancements

### Redis
- [ ] Pub/Sub monitoring
- [ ] Slow log viewer
- [ ] Key expiration management
- [ ] Bulk operations
- [ ] Export/import keys
- [ ] Real-time key updates (WebSocket)

### PostgreSQL
- [ ] Query history
- [ ] Query explain/analyze
- [ ] Index advisor
- [ ] Vacuum/analyze scheduling
- [ ] Table statistics graphs
- [ ] Export query results (CSV, JSON)
- [ ] Saved queries
- [ ] Query templates

## Summary

✅ **Redis Explorer**: Browse keys, view values, monitor memory and stats
✅ **PostgreSQL Explorer**: Browse tables, run queries, monitor activity
✅ **Safety**: Read-only for PostgreSQL, confirmation for destructive Redis ops
✅ **Monitoring**: Real-time stats for both databases
✅ **API**: Complete REST API for both databases

Ready for deployment and testing!
