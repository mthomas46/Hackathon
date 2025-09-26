# 🔴 Redis - Distributed Caching & Session Store

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "redis"
- port: 6379
- key_concepts: ["caching", "session_management", "data_structures", "pubsub", "persistence"]
- architecture: "distributed_cache"
- processing_hints: "Containerized Redis service for caching, session management, and data persistence"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../shared/README.md"]
- integration_points: ["all_services", "session_management", "caching_layer", "event_streaming"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**Status**: ✅ Production Ready  
**Port**: `6379` (External) → `6379` (Internal)  
**Version**: `7.2.0`  
**Last Updated**: September 26, 2025

## 🎯 **Overview & Purpose**

The **Redis service** provides **high-performance distributed caching and data structure storage** capabilities for the LLM Documentation Ecosystem. It serves as the central caching layer, session store, and data persistence solution with advanced Redis features for enterprise-scale applications.

**Core Mission**: Deliver ultra-fast data access and storage capabilities that enable high-performance, scalable operations across all ecosystem services through advanced caching, session management, and data structure support.

## 🚀 **Key Features & Capabilities**

### **⚡ High-Performance Caching**
- **In-Memory Storage**: Ultra-fast data access with sub-millisecond response times
- **TTL Management**: Automatic key expiration and memory management
- **Cache Strategies**: LRU, LFU, and custom eviction policies
- **Distributed Caching**: Multi-instance cache coordination and consistency

### **💾 Advanced Data Structures**
- **Strings**: Simple key-value storage with atomic operations
- **Hashes**: Field-value pairs for structured data storage
- **Lists**: Ordered collections with push/pop operations
- **Sets**: Unique element collections with set operations
- **Sorted Sets**: Ordered unique elements with scoring
- **Streams**: Append-only data structures for event streaming
- **HyperLogLog**: Probabilistic cardinality estimation

### **📡 Pub/Sub Messaging**
- **Publish/Subscribe**: Real-time message broadcasting capabilities
- **Pattern Matching**: Channel pattern subscription support
- **Event Streaming**: Reliable event distribution across services
- **Message Persistence**: Configurable message retention policies

### **🔄 Session Management**
- **Session Storage**: User session data persistence and retrieval
- **Token Management**: Authentication token storage and validation
- **State Management**: Application state persistence across restarts
- **Distributed Sessions**: Session sharing across multiple service instances

## 📡 **API Reference**

### **🔧 Core Redis Commands**

| Command Type | Examples | Purpose |
|--------------|----------|---------|
| **Strings** | `SET`, `GET`, `INCR`, `DECR` | Basic key-value operations |
| **Hashes** | `HSET`, `HGET`, `HGETALL`, `HLEN` | Structured data storage |
| **Lists** | `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE` | Ordered collections |
| **Sets** | `SADD`, `SREM`, `SMEMBERS`, `SISMEMBER` | Unique element collections |
| **Sorted Sets** | `ZADD`, `ZRANGE`, `ZSCORE`, `ZRANK` | Ordered unique elements |
| **Pub/Sub** | `PUBLISH`, `SUBSCRIBE`, `PSUBSCRIBE` | Message broadcasting |

### **🔍 Common Operations**
```bash
# String operations
SET user:123:name "John Doe"
GET user:123:name
EXPIRE user:123:name 3600

# Hash operations
HSET user:123 name "John" email "john@example.com"
HGETALL user:123

# List operations
LPUSH messages "Hello"
LPUSH messages "World"
LRANGE messages 0 -1

# Publish/Subscribe
SUBSCRIBE notifications
PUBLISH notifications "System update completed"
```

## 🏗️ **Architecture & Design**

### **🎯 Redis Architecture**
The Redis service employs a containerized Redis instance optimized for ecosystem integration:

#### **Configuration Features**
- **Persistence**: RDB and AOF persistence for data durability
- **Replication**: Master-slave replication for high availability
- **Clustering**: Redis Cluster for horizontal scaling
- **Security**: Access control and connection authentication

#### **Memory Management**
- **Max Memory**: Configurable memory limits with eviction policies
- **Key Expiry**: Automatic key expiration and cleanup
- **Memory Optimization**: Efficient data structure encoding
- **Monitoring**: Memory usage tracking and alerts

## ⚙️ **Configuration**

### **🐳 Docker Configuration**
```yaml
# docker-compose.yml
redis:
  image: redis:7.2-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
    - ./redis.conf:/etc/redis/redis.conf
  command: redis-server /etc/redis/redis.conf
  restart: unless-stopped
```

### **🔧 Redis Configuration**
```ini
# redis.conf
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300
daemonize no
supervised no
loglevel notice
databases 16
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
```

## 📋 **Requirements**

### **🔧 System Requirements**
- **Docker**: Container runtime for service deployment
- **Memory**: 256MB+ RAM minimum, 2GB+ recommended for production
- **Storage**: 1GB+ for data persistence and logs
- **Network**: Stable network connectivity for service communication

### **🎯 Performance Recommendations**
- **CPU**: Multi-core processor for concurrent operations
- **Memory**: Sufficient RAM for in-memory data storage
- **Storage**: SSD storage for persistence file I/O
- **Network**: Low-latency network for high-throughput scenarios

## 🏗️ **Infrastructure**

### **🐳 Container Deployment**
- **Docker Images**: Official Redis Alpine images for minimal footprint
- **Volume Management**: Persistent data volumes for data durability
- **Network Configuration**: Service mesh integration and discovery
- **Resource Limits**: CPU and memory limits for resource management

### **☸️ Kubernetes Support**
- **StatefulSets**: Persistent storage and stable network identities
- **ConfigMaps**: Runtime configuration management
- **Persistent Volumes**: Data persistence across pod restarts
- **Services**: Load balancing and service discovery

## 🌐 **Ecosystem Integration**

### **🎯 Primary Integrations**
- **All Services**: Caching and session management across the ecosystem
- **Orchestrator**: Workflow state persistence and coordination
- **Analysis Service**: Result caching and performance optimization
- **Frontend**: Session management and user state persistence

### **🔄 Integration Patterns**
- **Cache-aside Pattern**: Application-managed cache population
- **Write-through Caching**: Synchronous cache updates
- **Session Store**: Centralized session data management
- **Event Streaming**: Pub/Sub for inter-service communication

### **📊 Usage Patterns**
- **API Response Caching**: Frequently accessed data caching
- **Session Storage**: User authentication and session data
- **Rate Limiting**: Request rate tracking and enforcement
- **Analytics Aggregation**: Real-time metrics and statistics

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Connection Tests**: Redis connectivity and basic operations
- **Data Structure Tests**: All Redis data types and operations
- **Persistence Tests**: Data durability and recovery testing
- **Performance Tests**: High-throughput and concurrent access testing

### **📊 Testing Strategies**
- **Unit Testing**: Individual Redis command validation
- **Integration Testing**: Multi-service Redis interaction testing
- **Load Testing**: High-concurrency and high-throughput validation
- **Failover Testing**: Replication and cluster failover scenarios

## 🚀 **Deployment & Operations**

### **🐳 Quick Start**
```bash
# Start Redis service
docker run -d -p 6379:6379 --name redis redis:7.2-alpine

# Connect to Redis
docker exec -it redis redis-cli

# Basic operations
SET greeting "Hello World"
GET greeting
```

### **📊 Monitoring**
```bash
# Monitor Redis
docker exec redis redis-cli INFO

# Check memory usage
docker exec redis redis-cli INFO memory

# Monitor connected clients
docker exec redis redis-cli INFO clients
```

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#redis-service-port-6379---distributed-caching)** - Complete technical reference
- **[Redis Documentation](https://redis.io/documentation)** - Official Redis documentation
- **[Shared Caching Utilities](../shared/README.md)** - Ecosystem caching patterns

### **🎯 Integration Guides**
- **[Caching Best Practices](../../docs/guides/CACHING_BEST_PRACTICES.md)** - Caching strategy and implementation
- **[Session Management](../../docs/guides/SESSION_MANAGEMENT.md)** - Session handling patterns
- **[Performance Optimization](../../docs/guides/PERFORMANCE_OPTIMIZATION.md)** - Redis performance tuning

---

**🎯 The Redis service provides enterprise-grade caching and data management capabilities that enable high-performance, scalable operations across the entire ecosystem.**
