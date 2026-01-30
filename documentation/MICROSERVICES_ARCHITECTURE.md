# HandBrake2Resilio Microservices Architecture

## 🏗️ **Architecture Overview**

The HandBrake2Resilio system has been redesigned as a proper microservices architecture with clear separation of concerns, improved scalability, and better fault tolerance.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   API Gateway   │    │  HandBrake      │
│   (React)       │◄──►│   (Flask)       │◄──►│   Service       │
│   Port 3000     │    │   Port 8080     │    │   Port 8081     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │      Redis      │
                       │   (Cache/Queue) │
                       │   Port 6379     │
                       └─────────────────┘
```

## 🎯 **Service Breakdown**

### **1. API Gateway Service (`api_gateway.py`)**

- **Purpose**: Main entry point for all client requests
- **Responsibilities**:
  - Authentication and authorization
  - Request routing and load balancing
  - Service discovery and health checks
  - API versioning and rate limiting
  - WebSocket connections for real-time updates

**Key Features**:

- JWT-based authentication
- Request forwarding to HandBrake service
- Real-time WebSocket updates
- Health monitoring of all services
- CORS configuration

**Endpoints**:

- `GET /health` - Service health check
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `POST /api/jobs/add` - Add conversion job
- `GET /api/jobs/status/<job_id>` - Get job status
- `GET /api/jobs/list` - List all jobs
- `POST /api/jobs/cancel/<job_id>` - Cancel job
- `GET /api/system/status` - System status

### **2. HandBrake Service (`handbrake_service.py`)**

- **Purpose**: Dedicated video conversion service
- **Responsibilities**:
  - Video conversion using HandBrake CLI
  - Job queue management
  - Resource monitoring and throttling
  - Progress tracking and status updates

**Key Features**:

- Direct HandBrake CLI integration
- Resource-aware job scheduling
- Real-time progress monitoring
- Automatic retry mechanisms
- Redis-based job persistence

**Endpoints**:

- `GET /health` - Service health check
- `POST /convert` - Start video conversion
- `GET /job/<job_id>` - Get job status
- `GET /jobs` - List all jobs
- `POST /cancel/<job_id>` - Cancel job

### **3. Redis Service**

- **Purpose**: Distributed cache and message queue
- **Responsibilities**:
  - Job queue persistence
  - Session storage
  - Inter-service communication
  - Caching frequently accessed data

**Key Features**:

- Persistent job storage
- Session management
- Pub/Sub for real-time updates
- Automatic failover support

### **4. Frontend Service**

- **Purpose**: React-based user interface
- **Responsibilities**:
  - User interface for job management
  - Real-time status updates
  - System monitoring dashboard
  - Authentication interface

## 🚀 **Deployment Architecture**

### **Docker Compose Configuration**

```yaml
services:
  api-gateway:
    build: { context: ., dockerfile: Dockerfile.api }
    ports: ["8080:8080"]
    environment:
      - REDIS_URL=redis://redis:6379
      - HANDBRAKE_SERVICE_URL=http://handbrake-service:8081

  handbrake-service:
    build: { context: ., dockerfile: Dockerfile.handbrake }
    ports: ["8081:8081"]
    volumes: [media mounts]
    environment:
      - REDIS_URL=redis://redis:6379

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis-data:/data]

  frontend:
    build: { context: ./handbrake2resilio/ui-frontend }
    ports: ["3000:3000"]
```

### **Resource Allocation**

- **API Gateway**: 1 CPU, 1GB RAM
- **HandBrake Service**: 6 CPU, 6GB RAM
- **Redis**: 0.5 CPU, 512MB RAM
- **Frontend**: 0.5 CPU, 512MB RAM

## 🔧 **Service Communication**

### **Internal Communication**

1. **API Gateway ↔ HandBrake Service**: HTTP REST API
2. **API Gateway ↔ Redis**: Redis client for caching
3. **HandBrake Service ↔ Redis**: Redis client for job queue
4. **Frontend ↔ API Gateway**: HTTP REST API + WebSocket

### **External Communication**

- **Frontend**: Port 3000 (HTTP)
- **API Gateway**: Port 8080 (HTTP + WebSocket)
- **HandBrake Service**: Port 8081 (HTTP)
- **Redis**: Port 6379 (TCP)

## 🛡️ **Security Features**

### **Authentication & Authorization**

- JWT-based authentication
- Role-based access control (admin/user)
- Secure password hashing with bcrypt
- Session management with Redis

### **Network Security**

- CORS configuration for frontend
- Internal service communication over Docker network
- Non-root user execution in containers
- Read-only volume mounts for media

### **Data Security**

- Environment variable configuration
- No hardcoded secrets
- Secure JWT secret generation
- Input validation and sanitization

## 📊 **Monitoring & Observability**

### **Health Checks**

- **API Gateway**: `/health` endpoint
- **HandBrake Service**: `/health` endpoint
- **Redis**: `redis-cli ping`
- **Frontend**: HTTP response check

### **Logging**

- Structured JSON logging with structlog
- Centralized log collection
- Request/response logging
- Error tracking and alerting

### **Metrics**

- System resource usage (CPU, memory, disk)
- Job queue metrics
- Service response times
- Error rates and success rates

## 🔄 **Deployment Process**

### **Automated Deployment**

```bash
# Deploy microservices
./deploy_microservices.sh
```

### **Manual Deployment Steps**

1. **Build Services**:

   ```bash
   docker-compose -f docker-compose.microservices.yml build
   ```

2. **Start Services**:

   ```bash
   docker-compose -f docker-compose.microservices.yml up -d
   ```

3. **Verify Deployment**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8081/health
   curl http://localhost:3000
   ```

## 🎯 **Benefits of Microservices Architecture**

### **Scalability**

- Independent scaling of services
- Resource allocation based on service needs
- Horizontal scaling capabilities

### **Fault Tolerance**

- Service isolation prevents cascading failures
- Automatic retry mechanisms
- Graceful degradation under load

### **Maintainability**

- Clear separation of concerns
- Independent development and deployment
- Technology-specific optimizations

### **Performance**

- Dedicated resources for video conversion
- Efficient caching with Redis
- Optimized service communication

## 🔧 **Configuration Management**

### **Environment Variables**

```bash
# API Gateway
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379
HANDBRAKE_SERVICE_URL=http://handbrake-service:8081

# HandBrake Service
REDIS_URL=redis://redis:6379
MAX_CONCURRENT_JOBS=8
CPU_LIMIT=80
MEMORY_LIMIT=80

# Frontend
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
```

### **Volume Mounts**

- **Media**: Read-only access to video sources
- **Logs**: Persistent logging across restarts
- **Data**: Job persistence and user data
- **Redis**: Persistent cache and queue data

## 🚀 **Next Steps**

### **Immediate Actions**

1. Deploy microservices architecture
2. Test service communication
3. Verify authentication system
4. Test video conversion workflow

### **Future Enhancements**

1. **Load Balancing**: Add nginx reverse proxy
2. **Monitoring**: Integrate Prometheus/Grafana
3. **CI/CD**: Automated testing and deployment
4. **Scaling**: Kubernetes orchestration
5. **Security**: Network policies and secrets management

## 📋 **Troubleshooting**

### **Common Issues**

1. **Service Communication**: Check Docker network connectivity
2. **Authentication**: Verify JWT_SECRET_KEY environment variable
3. **Job Failures**: Check HandBrake CLI installation and permissions
4. **Resource Limits**: Monitor CPU/memory usage and adjust limits

### **Debug Commands**

```bash
# Check service logs
docker-compose -f docker-compose.microservices.yml logs -f api-gateway
docker-compose -f docker-compose.microservices.yml logs -f handbrake-service

# Check service health
curl http://localhost:8080/health
curl http://localhost:8081/health

# Check Redis connectivity
docker exec handbrake2resilio-redis redis-cli ping

# Monitor resource usage
docker stats handbrake2resilio-api handbrake2resilio-handbrake
```

This microservices architecture provides a robust, scalable, and maintainable foundation for the HandBrake2Resilio system, with clear separation of concerns and improved fault tolerance.
