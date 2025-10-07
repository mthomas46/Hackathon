# Zookeeper's Role in MCP Ecosystem

## Overview

**Apache Zookeeper** is a centralized service for maintaining configuration information, naming, providing distributed synchronization, and providing group services. In the MCP ecosystem, it serves as the critical coordination layer for Apache Kafka.

## Why Zookeeper is Required

### Primary Function: Kafka Coordination

Zookeeper acts as the backbone for Kafka's distributed architecture:

1. **Cluster Coordination**
   - Manages metadata about Kafka brokers
   - Tracks which brokers are alive and available
   - Maintains cluster state information

2. **Leader Election**
   - Determines which broker is the leader for each partition
   - Manages failover when leaders become unavailable
   - Ensures data consistency across replicas

3. **Configuration Management**
   - Stores topic configurations (partitions, replication factors)
   - Manages consumer group metadata
   - Tracks offset information for consumers

4. **Service Discovery**
   - Allows Kafka clients to discover available brokers
   - Provides dynamic broker registration
   - Maintains connection information

5. **Distributed Synchronization**
   - Ensures consistent state across distributed Kafka cluster
   - Manages distributed locks and barriers
   - Coordinates distributed transactions

## In MCP Ecosystem Context

```
┌─────────────────────────────────────────────────┐
│                 MCP Workflow                     │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│        kafka-ingestion-service                   │
│  (Document Event Streaming)                      │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Apache Kafka                        │
│  (Message Broker - Event Streaming)              │
└─────────────────────────────────────────────────┘
                      │
                      ▼ (requires)
┌─────────────────────────────────────────────────┐
│            Apache Zookeeper                      │
│  (Cluster Coordination & Metadata)               │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Ingestion**:
   - `kafka-ingestion-service` receives documents via API
   - Publishes events to Kafka topic: `document-ingestion`

2. **Kafka Processing**:
   - Kafka uses Zookeeper to determine partition leader
   - Message is written to appropriate partition
   - Zookeeper tracks offset and replication status

3. **Consumer Coordination**:
   - Downstream services (e.g., `llm-tagging-pipeline`) connect as consumers
   - Zookeeper manages consumer group coordination
   - Ensures each message is processed exactly once

## Configuration in MCP Ecosystem

### Docker Compose Configuration

```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  ports:
    - "2181:2181"
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
  networks:
    - ams

kafka:
  image: confluentinc/cp-kafka:7.5.0
  depends_on:
    - zookeeper
  environment:
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    # ... other Kafka settings
```

### Key Settings

- **Port 2181**: Standard Zookeeper client port
- **TICK_TIME: 2000ms**: Basic time unit for heartbeats
- **Network: ams**: Ensures Kafka and Zookeeper can communicate

## Operational Considerations

### Startup Order

1. **Zookeeper** starts first
2. **Kafka** starts after Zookeeper is ready
3. **kafka-ingestion-service** starts after Kafka is ready

This order is critical - Kafka cannot start without Zookeeper.

### Health Monitoring

```bash
# Check Zookeeper status
docker exec -it zookeeper zkServer.sh status

# Check Kafka's connection to Zookeeper
docker exec -it kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092
```

### Common Issues

1. **Zookeeper Not Ready**
   - Symptom: Kafka fails to start with "Connection refused"
   - Solution: Wait for Zookeeper to be fully initialized

2. **Connection Timeout**
   - Symptom: Kafka logs show "Timed out waiting for connection"
   - Solution: Verify network connectivity and ZOOKEEPER_CONNECT setting

3. **Metadata Out of Sync**
   - Symptom: Kafka shows stale broker information
   - Solution: Restart Kafka and let it re-register with Zookeeper

## Future: KRaft Mode

**Note**: Apache Kafka is transitioning away from Zookeeper dependency with KRaft (Kafka Raft) mode, where Kafka manages its own metadata. However, for stability and compatibility, the MCP ecosystem currently uses the traditional Zookeeper-based deployment.

### Migration Path (Future)

When KRaft becomes production-ready:
1. Update to Kafka 3.x with KRaft support
2. Remove Zookeeper dependency
3. Simplify deployment (one less service)
4. Improve startup time and resource usage

## Resources

- **Port**: 2181 (client connections)
- **Memory**: ~512MB
- **CPU**: Minimal (mostly idle)
- **Network**: Internal only (ams network)
- **Storage**: Ephemeral (no persistent volume in current setup)

## Troubleshooting

### Check Zookeeper Logs
```bash
docker logs zookeeper --tail 50
```

### Verify Kafka Connection
```bash
docker exec -it kafka kafka-topics \
  --list --bootstrap-server localhost:9092
```

### Test Connectivity from Services
```bash
# From within kafka-ingestion-service container
nc -zv zookeeper 2181
```

## Summary

Zookeeper is an essential infrastructure component that:
- ✅ Enables Kafka's distributed architecture
- ✅ Manages cluster coordination and metadata
- ✅ Ensures data consistency and reliability
- ✅ Provides service discovery for Kafka clients

**Without Zookeeper**: Kafka cannot function, and `kafka-ingestion-service` would fail to publish document events, breaking the entire MCP workflow.

**Status in MCP Ecosystem**: Critical infrastructure service, always required when using Kafka.
