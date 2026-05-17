# Docker Usage Guide for ARDY Smart Agriculture

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
cd ardy-smart-agriculture

# Build and start all services
docker-compose up --build

# Wait for data generation and model training (2-3 minutes)
# Then access:
# - Dashboard: http://localhost:8501
```

### 2. Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart frontend
```

### 3. View Service Logs

```bash
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f frontend

# Follow logs in real-time
docker-compose logs -f --timestamps
```

### 4. Execute Commands in Containers

```bash
# Access frontend shell
docker-compose exec frontend bash
```

### 5. Access the Wizard

Open http://localhost:8501 in your browser. The wizard handles all predictions and report generation in-app.

### 6. View Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats ardy-frontend

# Memory usage
docker stats --no-stream
```

### 7. Rebuild Images

```bash
# Rebuild all images
docker-compose build --no-cache

# Rebuild specific service
docker-compose build --no-cache frontend

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
docker image rm ardy-pulse_frontend

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune
```

---

## Troubleshooting

### Frontend Won't Start

```bash
# Check logs
docker-compose logs frontend

# Verify status
docker-compose ps

# Rebuild
docker-compose build --no-cache frontend
docker-compose up frontend
```

### Port Already in Use

```bash
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
docker-compose exec frontend ls -la /app/data

# Inspect volume
docker volume inspect ardy-smart-agriculture_data
```

---

## Environment Configuration

### Using Environment Variables

Create `.env` file:

```env
OPENWEATHER_API_KEY=your_api_key_here
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
# Example: edit app_wizard.py
nano app_wizard.py

# Rebuild and restart frontend
docker-compose up --build frontend
```

### Add New Dependencies

```bash
# Edit requirements-frontend.txt
nano requirements-frontend.txt

# Rebuild
docker-compose build --no-cache frontend

# Restart
docker-compose up frontend
```

### Retrain Models

```bash
# Run model trainer
docker-compose up model-trainer
```



---

## Performance Optimization

### Set Memory Limits

Edit `docker-compose.yml`:

```yaml
services:
  frontend:
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
docker stack deploy -c docker-compose.yml ardy

# View services
docker service ls
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
docker tag ardy-pulse_frontend myregistry/ardy-frontend:1.0.0

# Push to registry
docker push myregistry/ardy-frontend:1.0.0

# Pull from registry
docker pull myregistry/ardy-frontend:1.0.0
```

---

## Monitoring & Logging

### View Container Logs

```bash
# Real-time logs
docker-compose logs -f frontend

# Last 50 lines
docker-compose logs --tail=50 frontend

# With timestamps
docker-compose logs -f --timestamps frontend
```

### Inspect Container

```bash
# Get container info
docker inspect ardy-frontend

# Get IP address
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ardy-frontend

# Get environment variables
docker inspect -f '{{.Config.Env}}' ardy-frontend
```

### Health Check Status

```bash
# Check health
docker-compose ps
```

---

## Backup & Restore

### Backup Data

```bash
# Backup data volume
docker run --rm -v ardy-smart-agriculture_data:/data -v $(pwd):/backup \
  busybox tar czf /backup/data-backup.tar.gz -C /data .

# Backup models volume
docker run --rm -v ardy-smart-agriculture_models:/models -v $(pwd):/backup \
  busybox tar czf /backup/models-backup.tar.gz -C /models .
```

### Restore Data

```bash
# Restore data
docker run --rm -v ardy-smart-agriculture_data:/data -v $(pwd):/backup \
  busybox tar xzf /backup/data-backup.tar.gz -C /data

# Restore models
docker run --rm -v ardy-smart-agriculture_models:/models -v $(pwd):/backup \
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

### Quick Test

```bash
# (Wizard is accessible via browser at http://localhost:8501)
```

### Check All Ports

```bash
docker-compose ps
```

### Access Container Shell

```bash
docker-compose exec frontend bash
```

### Copy Files from Container

```bash
docker cp ardy-frontend:/app/data/soil_chemistry.csv ./
```

### Copy Files to Container

```bash
docker cp ./data/soil_chemistry.csv ardy-frontend:/app/data/
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

🌾 **ARDY Smart Agriculture: Precision Agriculture for National Food Security** 🌾
