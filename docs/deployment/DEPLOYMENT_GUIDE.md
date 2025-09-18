# 🚀 Production Deployment Guide - LLM Documentation Ecosystem

<!--
LLM Processing Metadata:
- document_type: "deployment_and_operations_guide"
- content_focus: "production_deployment_with_docker_orchestration"
- key_concepts: ["docker", "microservices", "production_deployment", "infrastructure"]
- processing_hints: "Complete deployment instructions with infrastructure requirements"
- cross_references: ["README.md", "ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "docs/README.md", "docs/operations/"]
- deployment_targets: ["development", "staging", "production", "kubernetes"]
-->

**Target Environments**: Production, Staging, Development  
**Infrastructure**: Docker, Kubernetes, Cloud-Native  
**Architecture**: 23 Microservices, Enterprise-Grade  
**Last Updated**: September 18, 2025

### 🔗 **Related Documentation**
- 📖 **[Master Living Document](ECOSYSTEM_MASTER_LIVING_DOCUMENT.md)** - Complete technical architecture and service details
- 📊 **[System Architecture](docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - Detailed architectural patterns and design decisions
- 🏗️ **[Infrastructure Setup](docs/guides/INFRASTRUCTURE_SETUP.md)** - Detailed infrastructure configuration guide
- ⚙️ **[Operations Runbook](docs/operations/RUNBOOK.md)** - Operational procedures and troubleshooting
- 📚 **[Documentation Index](docs/README.md)** - Complete documentation catalog

---

## 📋 **Deployment Overview**

### **🎯 What You're Deploying**
- **21+ Specialized Services** with enterprise AI-first architecture
- **300+ API Endpoints** across all services (90+ in Doc Store alone)
- **Complete AI Infrastructure** with intelligent LLM Gateway and provider routing
- **Domain-Driven Design** with CQRS, Event Sourcing, and bounded contexts
- **Bulletproof Operations** with self-healing deployment and comprehensive monitoring
- **AI Orchestration** with LangGraph workflows and natural language interfaces

### **🏗️ Infrastructure Requirements**

| Environment | CPU | Memory | Storage | Network |
|-------------|-----|--------|---------|---------|
| **Development** | 4+ cores | 16GB RAM | 100GB SSD | 1GB/s |
| **Staging** | 8+ cores | 32GB RAM | 500GB SSD | 10GB/s |
| **Production** | 16+ cores | 64GB RAM | 1TB SSD | 10GB/s |

---

## 🐳 **Docker Deployment**

### **Quick Start (Development)**

```bash
# Clone repository
git clone <repository-url>
cd LLM-Documentation-Ecosystem

# Start all services (3-5 minutes)
docker-compose -f docker-compose.dev.yml up -d

# Verify deployment
./scripts/validation/health_check_all.sh
```

### **Production Docker Deployment**

#### **1. Production Configuration**
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

#### **2. Production Environment Variables**
Create `.env.production`:
```bash
# Core Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database & Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>

# AI Provider Configuration
OPENAI_API_KEY=<your-openai-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
OLLAMA_ENDPOINT=http://ollama:11434

# Security
JWT_SECRET=<secure-jwt-secret>
ENCRYPTION_KEY=<secure-encryption-key>

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_AGGREGATION=true

# Scaling
REDIS_CLUSTER=true
ANALYSIS_WORKERS=4
PROMPT_CACHE_SIZE=1000
```

#### **3. Production Docker Compose**
Key differences in `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  # Production-optimized services
  llm-gateway:
    image: llm-ecosystem/llm-gateway:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - REDIS_CLUSTER=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5055/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  # Add load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/production.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - llm-gateway
      - frontend
      - orchestrator
```

---

## ☸️ **Kubernetes Deployment**

### **🎯 Kubernetes Architecture**

```yaml
# Namespace isolation
apiVersion: v1
kind: Namespace
metadata:
  name: llm-ecosystem
  labels:
    environment: production
    version: "1.0.0"
```

### **Core Services Deployment**

#### **1. LLM Gateway Service**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-gateway
  namespace: llm-ecosystem
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-gateway
  template:
    metadata:
      labels:
        app: llm-gateway
        version: "1.0.0"
    spec:
      containers:
      - name: llm-gateway
        image: llm-ecosystem/llm-gateway:latest
        ports:
        - containerPort: 5055
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5055
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5055
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: llm-gateway-service
  namespace: llm-ecosystem
spec:
  selector:
    app: llm-gateway
  ports:
  - port: 5055
    targetPort: 5055
  type: ClusterIP
```

#### **2. Prompt Store Service**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prompt-store
  namespace: llm-ecosystem
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prompt-store
  template:
    metadata:
      labels:
        app: prompt-store
        version: "2.0.0"
    spec:
      containers:
      - name: prompt-store
        image: llm-ecosystem/prompt-store:latest
        ports:
        - containerPort: 5110
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: REDIS_HOST
          value: "redis-service"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: prompt-store-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        volumeMounts:
        - name: prompt-data
          mountPath: /app/data
      volumes:
      - name: prompt-data
        persistentVolumeClaim:
          claimName: prompt-store-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: prompt-store-service
  namespace: llm-ecosystem
spec:
  selector:
    app: prompt-store
  ports:
  - port: 5110
    targetPort: 5110
  type: ClusterIP
```

### **3. Redis Cluster**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: llm-ecosystem
spec:
  serviceName: redis-service
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --cluster-enabled
        - yes
        - --cluster-config-file
        - nodes.conf
        - --cluster-node-timeout
        - "5000"
        - --appendonly
        - yes
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: llm-ecosystem
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
```

### **4. Ingress Configuration**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-ecosystem-ingress
  namespace: llm-ecosystem
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.llm-ecosystem.com
    - app.llm-ecosystem.com
    secretName: llm-ecosystem-tls
  rules:
  - host: api.llm-ecosystem.com
    http:
      paths:
      - path: /llm
        pathType: Prefix
        backend:
          service:
            name: llm-gateway-service
            port:
              number: 5055
      - path: /prompts
        pathType: Prefix
        backend:
          service:
            name: prompt-store-service
            port:
              number: 5110
  - host: app.llm-ecosystem.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

---

## 🌩️ **Cloud Deployment**

### **AWS Deployment**

#### **1. EKS Cluster Setup**
```bash
# Create EKS cluster
eksctl create cluster \
  --name llm-ecosystem \
  --region us-west-2 \
  --node-type m5.2xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed

# Configure kubectl
aws eks update-kubeconfig --region us-west-2 --name llm-ecosystem

# Deploy ecosystem
kubectl apply -f k8s/
```

#### **2. AWS Services Integration**
```yaml
# Use AWS managed services
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-config
  namespace: llm-ecosystem
data:
  # Use ElastiCache for Redis
  REDIS_HOST: "llm-ecosystem.cache.amazonaws.com"
  
  # Use RDS for databases
  DATABASE_HOST: "llm-ecosystem.rds.amazonaws.com"
  
  # Use S3 for file storage
  S3_BUCKET: "llm-ecosystem-storage"
  
  # Use CloudWatch for monitoring
  CLOUDWATCH_ENABLED: "true"
```

### **Google Cloud Platform (GCP)**

#### **1. GKE Cluster**
```bash
# Create GKE cluster
gcloud container clusters create llm-ecosystem \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials llm-ecosystem --zone us-central1-a

# Deploy
kubectl apply -f k8s/
```

### **Azure Deployment**

#### **1. AKS Cluster**
```bash
# Create resource group
az group create --name llm-ecosystem --location eastus

# Create AKS cluster
az aks create \
  --resource-group llm-ecosystem \
  --name llm-ecosystem \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10

# Get credentials
az aks get-credentials --resource-group llm-ecosystem --name llm-ecosystem

# Deploy
kubectl apply -f k8s/
```

---

## 📊 **Monitoring & Observability**

### **Prometheus Configuration**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: llm-ecosystem
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    
    scrape_configs:
    - job_name: 'llm-ecosystem'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - llm-ecosystem
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

### **Grafana Dashboards**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: llm-ecosystem
data:
  ecosystem-overview.json: |
    {
      "dashboard": {
        "title": "LLM Ecosystem Overview",
        "panels": [
          {
            "title": "Service Health",
            "type": "stat",
            "targets": [
              {
                "expr": "up{namespace=\"llm-ecosystem\"}"
              }
            ]
          },
          {
            "title": "API Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{namespace=\"llm-ecosystem\"}[5m])"
              }
            ]
          }
        ]
      }
    }
```

---

## 🔒 **Security Configuration**

### **Network Policies**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llm-ecosystem-network-policy
  namespace: llm-ecosystem
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: llm-ecosystem
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: llm-ecosystem
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### **Secret Management**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-ecosystem-secrets
  namespace: llm-ecosystem
type: Opaque
data:
  # Base64 encoded secrets
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
  jwt-secret: <base64-encoded-secret>
  redis-password: <base64-encoded-password>
```

### **RBAC Configuration**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: llm-ecosystem-role
  namespace: llm-ecosystem
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: llm-ecosystem-binding
  namespace: llm-ecosystem
subjects:
- kind: ServiceAccount
  name: llm-ecosystem-serviceaccount
  namespace: llm-ecosystem
roleRef:
  kind: Role
  name: llm-ecosystem-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 🚀 **Deployment Automation**

### **CI/CD Pipeline (GitHub Actions)**
```yaml
name: Deploy LLM Ecosystem

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Build and push images
      run: |
        # Build all service images
        docker build -t llm-ecosystem/llm-gateway:${{ github.sha }} services/llm-gateway/
        docker build -t llm-ecosystem/prompt-store:${{ github.sha }} services/prompt_store/
        
        # Push to ECR
        aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
        docker push llm-ecosystem/llm-gateway:${{ github.sha }}
        docker push llm-ecosystem/prompt-store:${{ github.sha }}
    
    - name: Deploy to EKS
      run: |
        aws eks update-kubeconfig --name llm-ecosystem
        
        # Update image tags
        sed -i 's|image: llm-ecosystem/llm-gateway:latest|image: llm-ecosystem/llm-gateway:${{ github.sha }}|g' k8s/llm-gateway.yaml
        
        # Apply manifests
        kubectl apply -f k8s/
        
        # Wait for rollout
        kubectl rollout status deployment/llm-gateway -n llm-ecosystem
        kubectl rollout status deployment/prompt-store -n llm-ecosystem
```

### **Helm Charts**
```yaml
# Chart.yaml
apiVersion: v2
name: llm-ecosystem
description: LLM Documentation Ecosystem Helm Chart
version: 1.0.0
appVersion: "1.0.0"

# values.yaml
global:
  environment: production
  imageRegistry: "your-registry.com"
  imageTag: "latest"

llmGateway:
  replicaCount: 3
  image:
    repository: llm-ecosystem/llm-gateway
    pullPolicy: IfNotPresent
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

promptStore:
  replicaCount: 2
  image:
    repository: llm-ecosystem/prompt-store
    pullPolicy: IfNotPresent
  persistence:
    enabled: true
    size: 20Gi
```

---

## 🔧 **Operational Procedures**

### **Health Monitoring**
```bash
# Check all service health
kubectl get pods -n llm-ecosystem
kubectl get services -n llm-ecosystem

# Service-specific health checks
kubectl exec -it deployment/llm-gateway -n llm-ecosystem -- curl localhost:5055/health
kubectl exec -it deployment/prompt-store -n llm-ecosystem -- curl localhost:5110/health

# View service logs
kubectl logs -f deployment/llm-gateway -n llm-ecosystem
kubectl logs -f deployment/prompt-store -n llm-ecosystem --tail=100
```

### **Scaling Operations**
```bash
# Manual scaling
kubectl scale deployment llm-gateway --replicas=5 -n llm-ecosystem
kubectl scale deployment prompt-store --replicas=3 -n llm-ecosystem

# Horizontal Pod Autoscaler
kubectl autoscale deployment llm-gateway --cpu-percent=70 --min=2 --max=10 -n llm-ecosystem
```

### **Database Operations**
```bash
# Redis cluster management
kubectl exec -it redis-cluster-0 -n llm-ecosystem -- redis-cli cluster info
kubectl exec -it redis-cluster-0 -n llm-ecosystem -- redis-cli cluster nodes

# Backup Redis data
kubectl exec redis-cluster-0 -n llm-ecosystem -- redis-cli bgsave
```

### **Troubleshooting**
```bash
# Pod debugging
kubectl describe pod <pod-name> -n llm-ecosystem
kubectl exec -it <pod-name> -n llm-ecosystem -- /bin/bash

# Network connectivity
kubectl exec -it <pod-name> -n llm-ecosystem -- nslookup redis-service
kubectl exec -it <pod-name> -n llm-ecosystem -- curl http://llm-gateway-service:5055/health

# Resource usage
kubectl top pods -n llm-ecosystem
kubectl top nodes
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] Secrets created and validated
- [ ] Resource quotas set appropriately
- [ ] Network policies configured
- [ ] Monitoring stack deployed
- [ ] Backup procedures established

### **Deployment**
- [ ] All 17 services deployed successfully
- [ ] Health checks passing
- [ ] Inter-service connectivity verified
- [ ] External access configured (ingress/load balancer)
- [ ] SSL/TLS certificates configured
- [ ] Monitoring dashboards accessible

### **Post-Deployment**
- [ ] End-to-end functionality tested
- [ ] Performance benchmarks run
- [ ] Security scan completed
- [ ] Backup verification performed
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## 🎯 **Performance Optimization**

### **Resource Allocation**
```yaml
# High-traffic services
llm-gateway:
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "8Gi"
      cpu: "4000m"

# Data-intensive services
prompt-store:
  resources:
    requests:
      memory: "4Gi"
      cpu: "2000m"
    limits:
      memory: "16Gi"
      cpu: "8000m"
```

### **Caching Configuration**
```yaml
# Redis configuration for optimal performance
redis:
  config:
    maxmemory: "4gb"
    maxmemory-policy: "allkeys-lru"
    tcp-keepalive: "60"
    timeout: "300"
```

---

## 🎉 **Deployment Complete!**

Your LLM Documentation Ecosystem is now deployed and ready for production use. The system provides:

- ✅ **17 Microservices** running with enterprise architecture
- ✅ **Complete AI Infrastructure** with LLM Gateway
- ✅ **Production-Grade Monitoring** with Prometheus and Grafana
- ✅ **Scalable Architecture** with Kubernetes orchestration
- ✅ **Security Best Practices** with RBAC and network policies
- ✅ **Operational Excellence** with comprehensive monitoring and logging

**Next Steps**: Monitor the deployment, run performance tests, and enjoy your enterprise-grade AI documentation ecosystem! 🚀
