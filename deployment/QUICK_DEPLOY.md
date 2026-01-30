# ⚡ Quick Deploy Reference

## 🚀 One-Command Deploy

```bash
cd handbrake2resilio/deployment/
./deploy_clean.sh && ./verify_clean_deployment.sh
```

## 🆘 Emergency Commands

### Deploy

```bash
./deploy_clean.sh
```

### Verify

```bash
./verify_clean_deployment.sh
```

### Rollback

```bash
./rollback_deployment.sh
```

### Manual Check

```bash
ssh akun@192.168.10.18 "docker ps && curl http://localhost:8080/health && curl http://localhost:3000"
```

## 🎯 URLs After Deploy

- **Frontend**: http://192.168.10.18:3000
- **API**: http://192.168.10.18:8080
- **Health**: http://192.168.10.18:8080/health
- **Tabs**: http://192.168.10.18:8080/api/tabs

## 🔧 Debug Commands

```bash
# Check containers
ssh akun@192.168.10.18 "docker ps -a"

# Check logs
ssh akun@192.168.10.18 "docker logs handbrake2resilio-api-gateway"
ssh akun@192.168.10.18 "docker logs handbrake2resilio-frontend"

# Check ports
ssh akun@192.168.10.18 "netstat -tlnp | grep -E '(8080|3000)'"
```

## ✅ Success Indicators

- Both containers show "Up" status
- API health returns HTTP 200
- Frontend loads without errors
- Tab creation works
- No errors in logs

## 🚨 Failure Indicators

- Container exits immediately
- HTTP 404/500 errors
- Connection refused
- Build failures
- Port conflicts

---

**Golden Rule**: When in doubt, run `./deploy_clean.sh` for a fresh start!
