# 🚀 PrintFarm v3.3.4 - Production Deployment Guide

## 📋 Overview

This guide explains how to deploy PrintFarm v3.3.4 to a remote server using Docker, with automatic handling of port conflicts and comprehensive testing.

**Key Features v3.3.4:**
- Reserve Stock Integration in production planning
- Critical hotfix for 146+ products visibility  
- Alternative ports for conflict resolution
- Automated deployment with rollback capability

---

## 🏗️ Architecture & Ports

### Port Mapping (Modified for Production)

| Service | Local Port | Production Port | Purpose |
|---------|------------|-----------------|----------|
| **Backend API** | 8000 | **8001** | Django REST API (changed due to conflict) |
| **Frontend** | 3000 | **3001** | React application |
| **Nginx** | 80 | **8080** | Reverse proxy & static files |
| **PostgreSQL** | 5432 | **5433** | Database |
| **Redis** | 6379 | **6380** | Cache & Celery broker |

### Service URLs After Deployment
- **🌐 Main Application**: `http://your-server:8080`
- **🔧 Backend API**: `http://your-server:8001/api/v1/`
- **⚛️ Frontend**: `http://your-server:3001`
- **📊 System Info**: `http://your-server:8001/api/v1/settings/system-info/`

---

## 🔧 Prerequisites

### Local Machine
```bash
# Required tools
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
rsync --version           # For file synchronization
ssh-keygen -t rsa         # SSH key authentication
```

### Remote Server
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

---

## ⚙️ Configuration

### 1. Environment Setup

Copy and customize the production environment file:

```bash
cp .env.prod .env.prod.local
```

**Critical Settings to Update in .env.prod:**

```bash
# Security - MUST CHANGE
SECRET_KEY=your-super-secret-production-key

# Server details - UPDATE THESE
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP,your-domain.com
REACT_APP_API_URL=http://YOUR_SERVER_IP:8001/api/v1

# Database - SECURE PASSWORDS
POSTGRES_PASSWORD=super-secure-database-password

# MoySklad API
MOYSKLAD_TOKEN=your-actual-moysklad-token
MOYSKLAD_DEFAULT_WAREHOUSE=your-warehouse-id
```

### 2. SSH Key Authentication

```bash
# Generate SSH key (if needed)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key to server  
ssh-copy-id user@your-server-ip

# Test connection
ssh user@your-server-ip "echo 'SSH connection successful'"
```

---

## 🚀 Deployment Process

### Quick Deployment

```bash
# 1. Test connection and ports (dry run)
./deploy.sh user@your-server-ip --dry-run

# 2. Deploy to production
./deploy.sh user@your-server-ip

# 3. Test deployment
./test-deployment.sh user@your-server-ip
```

### Deployment Steps

The deployment script automatically:
1. 📦 Creates backup of current deployment
2. 🔄 Syncs project files to server  
3. 🛑 Stops old containers
4. 🏗️ Builds new Docker images
5. 🚀 Starts new containers
6. ⏳ Waits for services to be ready
7. ✅ Shows deployment status

---

## 🔍 Verification & Testing

### Health Checks

```bash
# Quick API health check
curl http://your-server:8001/api/v1/settings/system-info/

# Expected response:
{
  "version": "v3.3.4",
  "build_date": "2025-08-14 09:34:25 +0300"
}
```

### Comprehensive Testing

```bash
# Run full test suite
./test-deployment.sh user@your-server-ip
```

Tests include:
- 🐳 Container health status
- 🌐 Port accessibility 
- 🔌 API endpoint responses
- 📱 Frontend accessibility
- 🗄️ Database connectivity
- 📋 Log analysis for errors
- 🎯 **Reserve stock functionality (v3.3.4 critical feature)**

### Critical v3.3.4 Feature Test

```bash
# Verify reserve stock integration
curl -s http://your-server:8001/api/v1/tochka/production/ | grep -c '"reserved_stock":[^0]'
# Should return > 0 (products with reserve stock)
```

---

## 🔄 Rollback Procedures

### Quick Rollback

```bash
# Rollback to latest backup
./rollback.sh user@your-server-ip

# Rollback to specific backup
./rollback.sh user@your-server-ip backup-20250814-143022
```

The rollback script:
- Lists available backups
- Creates pre-rollback backup
- Restores specified backup
- Restarts services
- Verifies rollback success

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using the port
ssh user@your-server-ip "sudo ss -tlnp | grep 8001"

# Deploy with force flag to ignore conflicts
./deploy.sh user@your-server-ip --force
```

#### 2. API Not Responding
```bash
# Check backend container logs
ssh user@your-server-ip "cd /opt/printfarm-production && docker-compose -f docker-compose.server.prod.yml logs backend"
```

#### 3. Frontend Issues
```bash
# Check frontend logs
ssh user@your-server-ip "cd /opt/printfarm-production && docker-compose -f docker-compose.server.prod.yml logs frontend"

# Verify API URL in .env.prod
grep REACT_APP_API_URL .env.prod
```

#### 4. Database Connection
```bash
# Test database connection
ssh user@your-server-ip "cd /opt/printfarm-production && docker-compose -f docker-compose.server.prod.yml exec backend python manage.py check --database default"
```

### Log Locations
```bash
# Application logs inside containers
docker-compose -f docker-compose.server.prod.yml logs [service-name]

# System logs
sudo journalctl -u docker.service -f
```

---

## 📊 Monitoring & Maintenance

### Quick Status Check
```bash
# Run deployment test
./test-deployment.sh user@your-server-ip

# Check container status
ssh user@your-server-ip "cd /opt/printfarm-production && docker-compose -f docker-compose.server.prod.yml ps"
```

### Performance Monitoring
```bash
# Container resource usage
ssh user@your-server-ip "docker stats"

# Check disk space
ssh user@your-server-ip "df -h"
```

---

## 📞 Quick Reference

### Commands Summary
```bash
# Deploy
./deploy.sh user@server-ip [--dry-run] [--force]

# Test  
./test-deployment.sh user@server-ip

# Rollback
./rollback.sh user@server-ip [backup-name]

# Status
ssh user@server-ip "cd /opt/printfarm-production && docker-compose -f docker-compose.server.prod.yml ps"
```

### Service URLs
- **Main App**: `http://your-server:8080` 
- **API**: `http://your-server:8001/api/v1/`
- **Frontend**: `http://your-server:3001`
- **System Info**: `http://your-server:8001/api/v1/settings/system-info/`

### File Structure
```
printfarm-production/
├── deploy.sh                        # Deployment script
├── test-deployment.sh               # Testing script
├── rollback.sh                      # Rollback script  
├── docker-compose.server.prod.yml   # Production compose
├── .env.prod                        # Production config
├── DEPLOYMENT.md                    # This guide
├── backend/                         # Django app
├── frontend/                        # React app
└── docker/                          # Docker configs
```

---

**🎉 PrintFarm v3.3.4 is ready for production deployment\!**

The system includes critical Reserve Stock Integration ensuring all 146+ products with reserve are visible in production planning.
README_EOF < /dev/null