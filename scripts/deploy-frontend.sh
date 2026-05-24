#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ecs-user/apps/agent_security_platform"

cd "$ROOT"

echo "[1/6] Git status"
git status --short

echo "[2/6] Pull latest code"
git pull

echo "[3/6] Build frontend"
cd "$ROOT/frontend"

if [ ! -f ".env.production" ]; then
  cat > .env.production <<'ENV'
VITE_API_BASE_URL=/api/v1
VITE_ENABLE_API_MOCK=false
ENV
fi

pnpm install --frozen-lockfile
pnpm build

echo "[4/6] Validate Nginx config"
cd "$ROOT"
docker exec asp-nginx nginx -t

echo "[5/6] Reload Nginx"
docker exec asp-nginx nginx -s reload

echo "[6/6] Smoke test"
curl -I http://127.0.0.1/ | head -n 5

echo "Frontend deploy finished."
