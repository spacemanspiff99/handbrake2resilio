# Repository Cleanup Summary

## Current layout (handbrake2resilio)

Canonical Python entry points are the `*_simple.py` services; Dockerfiles invoke those files only.

```
handbrake2resilio/
├── api-gateway/
│   ├── api_gateway_simple.py   # canonical API gateway
│   └── auth.py
├── handbrake-service/
│   └── handbrake_service_simple.py   # canonical HandBrake service
├── shared/
│   ├── config.py
│   ├── db.py
│   ├── job_queue.py
│   └── __init__.py
├── deployment/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.handbrake
│   ├── deploy_simple.sh
│   ├── deploy_h2r.sh
│   ├── requirements.simple.txt
│   ├── deployment_readiness_check.py
│   └── .env.example
├── testing/
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_config_simple.py   # smoke script for load_config()
│   └── test_job_queue.py
├── ui-frontend/
│   └── (React app)
└── documentation/
    └── (guides and architecture docs)
```

## Removed / consolidated (WEA-132 and prior cleanups)

- **testing/test_simple.py** — Removed: duplicate of other test modules; used try/except on import so `AuthService` / `JobQueue` / `ConversionJob` were often undefined; `Config()` calls did not match the current `Config` dataclass constructor. Use `test_auth.py`, `test_job_queue.py`, and `test_config.py` instead.
- Earlier phases removed non-canonical `api_gateway.py`, `handbrake_service.py`, and extra compose/Dockerfile variants; see git history.

## Security / .gitignore

- Large files, secrets, and common artifacts are excluded per project `.gitignore` and user security rules.

## Working components

- **API Gateway**: `api-gateway/api_gateway_simple.py`
- **HandBrake worker**: `handbrake-service/handbrake_service_simple.py`
- **Frontend**: `ui-frontend/`
