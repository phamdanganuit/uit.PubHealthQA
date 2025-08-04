# 🐳 Docker Deployment Guide

## Quick Start

### 1. Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc:

```bash
# Groq API Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here

# MongoDB Configuration  
MONGODB_URL=mongodb+srv://an:dangan123@cluster.ju2jwqz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster

# JWT Security Configuration
SECRET_KEY=your-super-secret-jwt-key-please-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Chạy ứng dụng

#### Sử dụng Docker Compose (Khuyến nghị)

```bash
# Build và chạy
docker-compose up --build

# Chạy ở background
docker-compose up -d --build

# Xem logs
docker-compose logs -f web

# Dừng services
docker-compose down
```

#### Sử dụng Docker trực tiếp

```bash
# Build image
docker build -t pubhealth-qa .

# Chạy container
docker run -d \
  --name pubhealth-qa \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_api_key \
  -e MONGODB_URL=your_mongodb_url \
  -e SECRET_KEY=your_secret_key \
  -v $(pwd)/app/static/uploads:/app/app/static/uploads \
  -v $(pwd)/data/gold:/app/data/gold:ro \
  pubhealth-qa
```

### 3. Truy cập ứng dụng

- **Web App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Production Deployment

### Environment Variables bắt buộc

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key | ❌ Required |
| `MONGODB_URL` | MongoDB connection string | ❌ Required |
| `SECRET_KEY` | JWT secret key | ❌ Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry time | `30` |

### Security Best Practices

1. **Change default SECRET_KEY**:
   ```bash
   # Generate secure secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use strong MongoDB credentials**
3. **Enable HTTPS in production**
4. **Use Docker secrets for sensitive data**

### Scaling

```bash
# Scale web service
docker-compose up --scale web=3

# Use reverse proxy (nginx)
# Add nginx service to docker-compose.yml
```

## 🔧 Development

### Build development image

```bash
# Development mode với live reload
docker build -f Dockerfile.dev -t pubhealth-qa:dev .
```

### Debug container

```bash
# Exec into running container
docker exec -it pubhealth-qa bash

# Check logs
docker logs pubhealth-qa

# Monitor resources
docker stats pubhealth-qa
```

## 📦 Container Details

- **Base Image**: python:3.11-slim
- **User**: Non-root user `app`
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Volumes**:
  - `/app/app/static/uploads` - User uploaded files
  - `/app/data/gold` - Vector database (read-only)

## 🚨 Troubleshooting

### Common Issues

1. **Health check failing**:
   ```bash
   # Check if app is running
   docker exec pubhealth-qa curl http://localhost:8000/health
   ```

2. **MongoDB connection issues**:
   ```bash
   # Verify environment variables
   docker exec pubhealth-qa printenv | grep MONGODB
   ```

3. **Permission issues**:
   ```bash
   # Fix uploads directory permissions
   sudo chown -R 1000:1000 app/static/uploads
   ```

### Performance Tuning

```bash
# Allocate more memory
docker run --memory=2g pubhealth-qa

# Use multi-stage build for smaller image
docker build --target production -t pubhealth-qa:prod .
``` 