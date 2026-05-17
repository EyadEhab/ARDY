# ARDY Smart Agriculture: Docker Deployment Guide

This guide explains how to run ARDY Smart Agriculture using Docker and Docker Compose.

## 📋 Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)
- At least 4GB RAM available
- 15GB disk space (for models and data)

## 🚀 Quick Start with Docker Compose

### 1. Clone/Navigate to Project Directory

```bash
cd ardy-smart-agriculture
```

### 2. Build and Start Services

```bash
docker-compose up --build
```

This command will:
- Build Docker images for all services
- Generate datasets (2000 soil samples, 350 yield records)
- Train ML models (XGBoost, Random Forest, yield forecasting)
- Start the frontend dashboard (Streamlit)

### 3. Access the Application

- **Dashboard**: http://localhost:8501

### 4. Stop Services

```bash
docker-compose down
```

---

## 🏗️ Architecture

### Services

**1. Frontend Service (Streamlit Dashboard)**
- Container: `ardy-frontend`
- Port: 8501
- Image: Python 3.11 + Streamlit
- Depends On: Backend service (healthy)
- Restart Policy: Unless stopped

**3. Data Generator Service**
- Container: `ardy-data-generator`
- Runs once on startup
- Generates datasets and trains models
- Restart Policy: No (runs once)

### Network

- Network Name: `ardy-network`
- Driver: Bridge
- Allows inter-service communication

---

## 📁 Docker Files

### docker-compose.yml
Main orchestration file defining all services, networks, and volumes.

### Dockerfile.frontend
- Base Image: python:3.11-slim
- Installs: Streamlit, ML libraries, system dependencies
- Exposes: Port 8501
- Runs: Streamlit server

### Dockerfile.data-generator
- Base Image: python:3.11-slim
- Installs: All dependencies
- Runs: generate_datasets.py + train_models.py
- One-time execution

### .dockerignore
Excludes unnecessary files from Docker build context to reduce image size.

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root (optional):

```env
# OpenWeatherMap API Key (optional)
OPENWEATHER_API_KEY=your_api_key_here

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

If `OPENWEATHER_API_KEY` is not set, the system uses synthetic weather data.

### Port Mapping

- Frontend Dashboard: `8501:8501` (host:container)

Change port mappings in `docker-compose.yml` if needed:

```yaml
ports:
  - "8080:8501"  # Access frontend at localhost:8080
```

---

## 📊 Volumes

### Shared Volumes

- `./data:/app/data` - Dataset files (read-only for services)
- `./models:/app/models` - Trained models (read-only for services)

### First Run

On first run, the data-generator service will:
1. Create `data/` directory
2. Generate 2000 soil chemistry samples
3. Generate 350 FAO yield records
4. Create 22 governorate reference data
5. Train ML models
6. Save models to `models/` directory

This process takes approximately 2-3 minutes.

---

## 🚨 Troubleshooting

### Frontend Service Won't Start

```bash
# Check logs
docker-compose logs frontend

# Verify status
docker-compose ps

# Rebuild image
docker-compose build --no-cache frontend
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8501

# Change ports in docker-compose.yml
# Or stop other services using these ports
```

### Data Not Persisting

```bash
# Check volume mounts
docker-compose exec frontend ls -la /app/data

# Verify volumes in docker-compose.yml
docker volume ls
```

---

## 🧪 Testing

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

---

---

## 🔐 Security Considerations

### Production Deployment

1. **Change Secret Keys**
   - Update `SECRET_KEY` in environment
   - Use strong, random values

2. **API Authentication**
   - Add API key validation
   - Implement rate limiting
   - Use HTTPS/TLS

3. **Data Protection**
   - Encrypt sensitive data
   - Use secure volume mounts
   - Implement access controls

4. **Image Security**
   - Use specific base image versions
   - Scan images for vulnerabilities
   - Keep dependencies updated

### Example Production Setup

```yaml
services:
  frontend:
    build: .
    ports:
      - "8501:8501"
    restart: always
```

---

## 🚀 Advanced Usage

### Custom Model Training

```bash
# Run the model trainer service
docker-compose up model-trainer
```

### Scaling

For production with multiple replicas:

```yaml
services:
  frontend:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

### Monitoring

Add monitoring services:

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

---

## 📚 Docker Commands Reference

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec frontend bash

# Remove volumes
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache

# Scale service
docker-compose up -d --scale frontend=3

# View resource usage
docker stats

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: docker-compose build
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASS }}
          docker-compose push
```

---

## 📖 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Python Docker Best Practices](https://docs.docker.com/language/python/)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)

---

## 🆘 Support

For issues:

1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Review README.md for documentation
4. Check QUICKSTART.md for general troubleshooting

---

**Version**: 1.0.0  
**Last Updated**: April 23, 2026

🌾 **ARDY Smart Agriculture: Precision Agriculture for National Food Security** 🌾
