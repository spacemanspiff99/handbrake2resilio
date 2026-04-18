# Phase 8: Deployment Fix & Stabilization

## 📝 Context & Rules
This execution phase adheres to the **Senior DevOps Engineering Rules** defined in `.cursor/rules/rules.mdc`.
**Role**: Senior DevOps Engineer.
**Objective**: Fix the broken production build caused by missing dependencies and incorrect entrypoints in the Docker configuration.

## 🚨 Current Status
The deployment to `192.168.10.18` failed during the build step:
1.  **Missing File**: `requirements.production.txt` was requested by Dockerfiles but not provided (we used `requirements.simple.txt`).
2.  **Incorrect Entrypoint**: Dockerfiles reference `api_server.py` and `docker-entrypoint.sh`, which do not exist in the simple deployment package.
3.  **Permission Issues**: Previous deployment attempts encountered SCP permission denied errors on the server.

## 🛠️ Execution Plan

### Step 1: Fix `Dockerfile.api`
Modify `Dockerfile.api` to match the actual file structure:
-   **Change Dependency File**: Replace `COPY requirements.production.txt ...` with `COPY requirements.simple.txt /tmp/requirements.txt`.
-   **Update CMD**: Change `CMD ["python3", "api_server.py"]` to `CMD ["python3", "api_gateway_simple.py"]`.
-   **Remove Entrypoint**: Remove `ENTRYPOINT ["/app/docker-entrypoint.sh"]` line entirely (simplification).
-   **Remove hardening scripts**: Remove `RUN chmod 755 /app/handbrake2resilio.sh` and `docker-entrypoint.sh` lines if those files aren't in the tarball.

### Step 2: Fix `Dockerfile.handbrake`
Modify `Dockerfile.handbrake` similarly:
-   **Change Dependency File**: Replace `COPY requirements.production.txt ...` with `COPY requirements.simple.txt /tmp/requirements.txt`.
-   **Update CMD**: Change `CMD ["python3", "api_server.py"]` to `CMD ["python3", "handbrake_service_simple.py"]`.
-   **Remove Entrypoint**: Remove `ENTRYPOINT` line.

### Step 3: Enhance `deploy_simple.sh`
Update the deployment script to be more robust:
-   **Explicit File Copying**: Ensure `requirements.simple.txt` is explicitly included in the tarball.
-   **Directory Management**: Change the remote directory to `~/hb2r-simple-v2` to avoid the permission lock on the old folder.
-   **Logs**: Add `docker compose logs` output if health checks fail.

### Step 4: Local Verification (Pre-flight)
Before deploying, verify the build locally:
```bash
# Verify API build
docker build -t test-api -f Dockerfile.api .

# Verify Handbrake build
docker build -t test-hb -f Dockerfile.handbrake .
```

### Step 5: Execute Deployment
Run the updated script:
```bash
./deploy_simple.sh
```

## ✅ Verification Checklist
After `./deploy_simple.sh` completes:
1.  [ ] **Build Success**: Ensure no `failed to calculate checksum` errors in output.
2.  [ ] **Container Status**: `docker ps` on server shows all 3 containers `Up`.
3.  [ ] **Health Check**:
    -   API: `curl http://192.168.10.18:8080/health` -> `{"status": "healthy"}`
    -   Frontend: `curl -I http://192.168.10.18:3000` -> `HTTP/1.1 200 OK`
4.  [ ] **Logs**: No immediate crash loops in `docker logs`.

## 📦 Git Operations
Upon successful verification:
1.  `git add .`
2.  `git commit -m "Fix deployment: Correct Dockerfiles and requirements for simple architecture"`
3.  `git push origin main`

## Next Phase
STOP. This completes the immediate recovery.
