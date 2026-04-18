# HandBrake2Resilio Production Deployment Guide

## Quick Deployment

1. Set secure JWT secret:
   export JWT_SECRET_KEY=$(openssl rand -base64 32)

2. Deploy to production:
   ./deploy_production.sh deploy

3. Check status:
   ./deploy_production.sh status

4. View logs:
   ./deploy_production.sh logs

## Health Check
curl http://192.168.10.18:8080/health

## Features Ready
- ✅ JWT Authentication
- ✅ Resource Management
- ✅ Job Queue System
- ✅ Security Hardening
- ✅ Monitoring & Logging
- ✅ Docker Deployment
