# Docker Usage Guide for EgyptAgri-Pulse

## Quick Reference

### Start All Services
```bash
docker-compose up --build
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

---

## Common Tasks

### 1. First-Time Setup

```bash
# Navigate to project
cd egypt-agri-pulse

# Build and start all services
docker-compose up --build

# Wait for data generation and model training (2-3 minutes)
# Then access:
# - Dashboard: http://localhost:8501
# - API: http://localhost:5000/api/health
```

### 2. Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### 3. View Service Logs

```bash
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Follow logs in real-time
docker-compose logs -f --timestamps
```

### 4. Execute Commands in Containers

```bash
# Access backend shell
docker-compose exec backend bash

# Run tests
docker-compose exec backend python test_api.py

# Check Python version
docker-compose exec backend python --version

# Access frontend shell
docker-compose exec frontend bash
```

### 5. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get governorates
curl http://localhost:5000/api/governorates

# Get weather for Cairo
curl http://localhost:5000/api/weather/Cairo

# Crop recommendation
curl -X POST http://localhost:5000/api/recommend-crop \
  -H "Content-Type: application/json" \
  -d '{"n": 60, "p": 30, "k": 200, "ph": 7.2}'

# Yield forecast
curl -X POST http://localhost:5000/api/forecast-yield \
  -H "Content-Type: application/json" \
  -d '{"crop": "Wheat", "year": 2026}'

# 5.1 Plant Doctor API (Crop Disease Detection)
# Test prediction with an image
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/leaf_image.jpg"
```

### 6. View Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats egyptagri-backend

# Memory usage
docker stats --no-stream
```

### 7. Rebuild Images

```bash
# Rebuild all images
docker-compose build --no-cache

# Rebuild specific service
docker-compose build --no-cache backend

# Build and restart
docker-compose up --build -d
```

### 8. Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (data loss!)
docker-compose down -v

# Remove images
docker image rm egyptagri-pulse_backend egyptagri-pulse_frontend

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Verify health check
docker-compose ps

# Rebuild
docker-compose build --no-cache backend
docker-compose up backend
```

### Frontend Can't Connect to Backend

```bash
# Test connectivity from frontend container
docker-compose exec frontend curl http://backend:5000/api/health

# Check if backend is running
docker-compose ps backend

# Restart both
docker-compose restart backend frontend
```

### Port Already in Use

```bash
# Find what's using port 5000
lsof -i :5000

# Find what's using port 8501
lsof -i :8501

# Kill process (if needed)
kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Reduce model size in train_models.py
# Or increase Docker memory limit
```

### Data Not Persisting

```bash
# Check volumes
docker volume ls

# Verify volume mount
docker-compose exec backend ls -la /app/data

# Inspect volume
docker volume inspect egypt-agri-pulse_data
```

---

## Environment Configuration

### Using Environment Variables

Create `.env` file:

```env
OPENWEATHER_API_KEY=your_api_key_here
FLASK_ENV=production
```

Then run:

```bash
docker-compose up
```

### Override Variables at Runtime

```bash
# Set variable when running
OPENWEATHER_API_KEY=your_key docker-compose up

# Or use env file
docker-compose --env-file custom.env up
```

---

## Development Workflow

### Modify Code and Rebuild

```bash
# Edit backend.py
nano backend.py

# Rebuild and restart
docker-compose up --build backend

# Restart frontend to pick up changes
docker-compose restart frontend
```

### Add New Dependencies

```bash
# Edit requirements.txt
nano requirements.txt

# Rebuild
docker-compose build --no-cache backend

# Restart
docker-compose up backend
```

### Retrain Models

```bash
# Access backend container
docker-compose exec backend bash

# Regenerate data
python generate_datasets.py

# Retrain models
python train_models.py

# Exit
exit
```

---

## Performance Optimization

### Increase Backend Workers

Edit `Dockerfile.backend`:

```dockerfile
# Change workers from 4 to 8
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", ...]
```

Then rebuild:

```bash
docker-compose build --no-cache backend
docker-compose up backend
```

### Increase Timeout

Edit `Dockerfile.backend`:

```dockerfile
# Change timeout from 120 to 300 seconds
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", ...]
```

### Set Memory Limits

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml egyptagri

# View services
docker service ls

# Scale service
docker service scale egyptagri_backend=3
```

### Using Kubernetes

```bash
# Convert docker-compose to Kubernetes
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f *.yaml

# Check status
kubectl get pods
```

### Using Docker Registry

```bash
# Tag image
docker tag egyptagri-pulse_backend myregistry/egyptagri-backend:1.0.0

# Push to registry
docker push myregistry/egyptagri-backend:1.0.0

# Pull from registry
docker pull myregistry/egyptagri-backend:1.0.0
```

---

## Monitoring & Logging

### View Container Logs

```bash
# Real-time logs
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50 backend

# With timestamps
docker-compose logs -f --timestamps backend
```

### Inspect Container

```bash
# Get container info
docker inspect egyptagri-backend

# Get IP address
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' egyptagri-backend

# Get environment variables
docker inspect -f '{{.Config.Env}}' egyptagri-backend
```

### Health Check Status

```bash
# Check health
docker-compose ps

# Manual health check
docker exec egyptagri-backend curl http://localhost:5000/api/health
```

---

## Backup & Restore

### Backup Data

```bash
# Backup data volume
docker run --rm -v egypt-agri-pulse_data:/data -v $(pwd):/backup \
  busybox tar czf /backup/data-backup.tar.gz -C /data .

# Backup models volume
docker run --rm -v egypt-agri-pulse_models:/models -v $(pwd):/backup \
  busybox tar czf /backup/models-backup.tar.gz -C /models .
```

### Restore Data

```bash
# Restore data
docker run --rm -v egypt-agri-pulse_data:/data -v $(pwd):/backup \
  busybox tar xzf /backup/data-backup.tar.gz -C /data

# Restore models
docker run --rm -v egypt-agri-pulse_models:/models -v $(pwd):/backup \
  busybox tar xzf /backup/models-backup.tar.gz -C /models
```

---

## Docker Compose Commands

| Command | Description |
|---------|-------------|
| `docker-compose up` | Start services |
| `docker-compose up -d` | Start in background |
| `docker-compose down` | Stop services |
| `docker-compose build` | Build images |
| `docker-compose logs` | View logs |
| `docker-compose ps` | List services |
| `docker-compose exec` | Execute command |
| `docker-compose restart` | Restart services |
| `docker-compose pull` | Pull images |
| `docker-compose push` | Push images |
| `docker-compose config` | Validate config |

---

## Useful Docker Commands

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs` | View container logs |
| `docker exec` | Execute command in container |
| `docker inspect` | Get container details |
| `docker stats` | View resource usage |
| `docker images` | List images |
| `docker rmi` | Remove image |
| `docker volume ls` | List volumes |
| `docker network ls` | List networks |

---

## Tips & Tricks

### One-Liner to Start Fresh

```bash
docker-compose down -v && docker-compose up --build
```

### Watch Logs in Real-Time

```bash
docker-compose logs -f --tail=50
```

### Quick API Test

```bash
docker-compose exec backend python test_api.py
```

### Check All Ports

```bash
docker-compose ps
```

### Access Container Shell

```bash
docker-compose exec backend bash
```

### Copy Files from Container

```bash
docker cp egyptagri-backend:/app/data/soil_chemistry.csv ./
```

### Copy Files to Container

```bash
docker cp ./data/soil_chemistry.csv egyptagri-backend:/app/data/
```

---

## Security Best Practices

1. **Use specific image versions** (not `latest`)
2. **Scan images for vulnerabilities**: `docker scan image_name`
3. **Don't run as root** in containers
4. **Use secrets management** for sensitive data
5. **Keep images small** to reduce attack surface
6. **Update base images regularly**
7. **Use read-only volumes** where possible
8. **Implement network policies**

---

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)

---

**Version**: 1.0.0  
**Last Updated**: April 23, 2026

🌾 **EgyptAgri-Pulse: Precision Agriculture for National Food Security** 🌾
