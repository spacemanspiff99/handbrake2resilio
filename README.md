# handbrake2resilio

Convert video files with HandBrakeCLI and sync output to Resilio Sync — managed via a web UI.

## Quick Start

```bash
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY and media paths
docker compose -f deployment/docker-compose.yml up --build
```

Open http://localhost:7474 — login with `admin` / `admin123`.

## Prerequisites

- Docker + Docker Compose v2
- HandBrake input directory (read-only mount)
- Output directory (writable mount)

## Architecture

| Service | Port | Role |
|---------|------|------|
| `api-gateway` | 8080 | Flask REST + WebSocket gateway, auth, SQLite |
| `handbrake-service` | 8081 | HandBrakeCLI worker, job queue, process management |
| `frontend` | 7474 | React UI (Nginx) |

## Environment Variables

See [`.env.example`](.env.example) for all variables.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | ✅ | — | Random string ≥16 chars (`openssl rand -base64 32`) |
| `MEDIA_INPUT_PATH` | ✅ | `/tmp/media_input` | Host path for input video files |
| `MEDIA_OUTPUT_PATH` | ✅ | `/tmp/media_output` | Host path for converted output |
| `MAX_CONCURRENT_JOBS` | | `2` | Max parallel HandBrake jobs |
| `API_PORT` | | `8080` | API gateway host port |
| `FRONTEND_PORT` | | `7474` | Frontend host port |

## Documentation

- [Architecture overview](documentation/MICROSERVICES_ARCHITECTURE.md)
- [Deployment guide](documentation/DEPLOYMENT_GUIDE.md)
- [Next steps](documentation/NEXT_STEPS.md)
