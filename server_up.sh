#!/usr/bin/env bash
# Start (or restart) the NeoForge 1.21.1 test server 'mc-server' with the built colossus jar, then self-test it.
# Network: private docker network 'mc-test' only (no published ports). RCON password lives in
# $COLOSSUS_DATA/secrets/rcon_password (default ./.data; never printed). Usage: ./server_up.sh [--no-selftest]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${COLOSSUS_DATA:-$ROOT/.data}"
DATA=$BASE/server; SECRETS=$BASE/secrets
NEO=$(sed -n 's/^neo_version=//p' "$ROOT/mod/gradle.properties")
JAR=""
for f in "$ROOT"/mod/build/libs/colossus-*.jar; do
  case "$f" in *-sources.jar) ;; *) [ -f "$f" ] && { JAR=$f; break; } ;; esac
done
[ -n "$JAR" ] || { echo "no jar - run ./build.sh first" >&2; exit 1; }
mkdir -p "$DATA" "$SECRETS"; chmod 700 "$SECRETS"
if [ ! -s "$SECRETS/rcon_password" ]; then
  (umask 077; head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 32 > "$SECRETS/rcon_password")
fi
docker network inspect mc-test >/dev/null 2>&1 || docker network create mc-test >/dev/null
docker rm -f mc-server >/dev/null 2>&1 || true
docker run -d --name mc-server --network mc-test --restart no \
  -e EULA=TRUE -e TYPE=NEOFORGE -e VERSION=1.21.1 -e NEOFORGE_VERSION="$NEO" \
  -e ONLINE_MODE=FALSE -e LEVEL_TYPE=minecraft:flat -e DIFFICULTY=peaceful -e MODE=survival \
  -e GENERATOR_SETTINGS='{"layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"biome":"minecraft:plains"}' \
  -e UID="$(id -u)" -e GID="$(id -g)" \
  -e SPAWN_PROTECTION=0 -e ENABLE_RCON=true -e RCON_PASSWORD_FILE=/run/secrets/rcon_password \
  -e MEMORY=2G -e VIEW_DISTANCE=8 -e SIMULATION_DISTANCE=6 -e TZ=UTC \
  -v "$DATA:/data" -v "$SECRETS/rcon_password:/run/secrets/rcon_password:ro" \
  -v "$JAR:/mods/colossus.jar:ro" \
  itzg/minecraft-server:java21 >/dev/null
echo "mc-server starting (NeoForge $NEO, jar $(basename "$JAR"))"
for i in $(seq 1 180); do
  docker logs mc-server 2>&1 | grep -q 'Done (' && break
  docker ps -q -f name='^mc-server$' | grep -q . || { docker logs --tail 50 mc-server; echo "mc-server died" >&2; exit 1; }
  sleep 5
done
docker logs mc-server 2>&1 | grep -q 'Done (' || { echo "timeout waiting for server" >&2; exit 1; }
echo "server ready"
rcon() { docker exec mc-server rcon-cli -- "$@" </dev/null | sed "s/\x1b\[[0-9;]*m//g"; }
[ "${1:-}" = "--no-selftest" ] && exit 0
echo "== self-test =="
LOG=$DATA/logs/latest.log
grep -E '\[colossus\]' "$LOG" || true
rcon kill '@e[tag=selftest]' >/dev/null || true
rcon summon colossus:colossus 4.5 -60 4.5 '{Tags:["selftest"]}'
rcon execute if entity '@e[type=colossus:colossus,tag=selftest]'
T0=$(rcon time query gametime | grep -o '[0-9]*$')
sleep 12
T1=$(rcon time query gametime | grep -o '[0-9]*$')
ALIVE=$(rcon execute if entity '@e[type=colossus:colossus,tag=selftest]')
echo "ticks elapsed: $((T1-T0)) ; after: $ALIVE"
rcon data get entity '@e[type=colossus:colossus,tag=selftest,limit=1]' Health
rcon kill '@e[tag=selftest]' >/dev/null
ERR=$(grep -ciE 'exception|/ERROR\]' "$LOG" || true)
echo "exception/ERROR lines in latest.log: $ERR"
if [ "$((T1-T0))" -ge 200 ] && echo "$ALIVE" | grep -q 'Test passed' && [ "$ERR" = 0 ]; then
  echo "SELFTEST PASS"
else
  echo "SELFTEST FAIL" >&2; exit 2
fi
