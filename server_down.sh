#!/usr/bin/env bash
# Stop and remove the test containers (world data stays in $COLOSSUS_DATA/server (default ./.data/server)).
docker rm -f mc-client mc-server >/dev/null 2>&1 || true
echo "mc-client/mc-server removed"
