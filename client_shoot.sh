#!/usr/bin/env bash
# Headless walk-cycle shoot: dev client (./gradlew runClient, user Dev) on Xvfb+llvmpipe joins mc-server over
# the private 'mc-test' network, RCON stages the scene, xdotool hides the HUD, ImageMagick grabs a burst.
# Shoots three walking bursts: front (walk_NN, toward the camera), side (side_NN, crossing left-right in profile) and
# back (back_NN, walking away). Side/back steer the mob with an invisible armor stand tagged colossus_lure.
# Usage: ./client_shoot.sh <outdir> [frames=10] [interval_s=0.45]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:?usage: client_shoot.sh <outdir> [frames] [interval]}"; N="${2:-10}"; DT="${3:-0.45}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
GH="${COLOSSUS_DATA:-$ROOT/.data}/gradle-home"
MOD="$ROOT/mod"
rcon() { docker exec mc-server rcon-cli -- "$@" </dev/null | sed "s/\x1b\[[0-9;]*m//g"; }

docker image inspect mc-client-img >/dev/null 2>&1 || \
  docker build -t mc-client-img -f "$ROOT/docker/client.Dockerfile" "$ROOT/docker" </dev/null
[ -n "$(docker ps -q -f name='^mc-server$')" ] || "$ROOT/server_up.sh" --no-selftest

# Game dir of the dev client is mod/run; pre-seed options so no onboarding/warning screens or pause menu appear.
mkdir -p "$MOD/run"
cat > "$MOD/run/options.txt" <<'OPT'
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
tutorialStep:none
pauseOnLostFocus:false
renderDistance:6
simulationDistance:5
maxFps:60
enableVsync:false
graphicsMode:0
renderClouds:"false"
narrator:0
soundCategory_master:0.0
realmsNotifications:false
guiScale:2
fov:0.0
OPT

docker rm -f mc-client >/dev/null 2>&1 || true
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)   # only count joins from this run
# grep reads all input (no -q): with pipefail, grep -q would SIGPIPE docker logs and look like a miss.
joined() { docker logs --since "$START" mc-server 2>&1 | grep -c 'Dev joined the game' >/dev/null; }
docker run -d --name mc-client --network mc-test --user "$(id -u):$(id -g)" \
  -e GRADLE_USER_HOME="$GH" -e HOME="$GH/home" \
  -e MC_CLIENT_ARGS="--username Dev --width 1280 --height 720 --quickPlayMultiplayer mc-server:25565" \
  -v "$MOD:$MOD" -v "$GH:$GH" -v "$OUT:/shots" -w "$MOD" \
  mc-client-img bash -c 'Xvfb :99 -screen 0 1280x720x24 -nolisten tcp >/tmp/xvfb.log 2>&1 & sleep 2; exec ./gradlew --no-daemon --console=plain runClient' >/dev/null
echo "mc-client starting; waiting for Dev to join (first run downloads assets)..."
for i in $(seq 1 240); do
  joined && break
  [ -n "$(docker ps -q -f name='^mc-client$')" ] || { docker logs --tail 80 mc-client; echo "mc-client died" >&2; exit 1; }
  sleep 5
done
joined || { docker logs --tail 80 mc-client; echo "timeout: Dev never joined" >&2; exit 1; }
echo "Dev joined; staging scene"
rcon gamemode survival Dev
rcon difficulty peaceful
rcon time set day
rcon gamerule doDaylightCycle false
rcon gamerule doWeatherCycle false
rcon weather clear
rcon kill '@e[type=colossus:colossus]'
# Camera: stand at (0.5,-60,0.5) looking due south (+Z, yaw 0), pitch -8 (slightly up so the 3-block mob fits).
rcon tp Dev 0.5 -60 0.5 0 -8
sleep 15   # let chunks mesh on llvmpipe
X="docker exec -e DISPLAY=:99 mc-client"
$X xdotool mousemove 640 360 </dev/null || true
WID=$($X xdotool search --name 'Minecraft' </dev/null | head -1 || true)
[ -n "$WID" ] && $X xdotool windowfocus "$WID" </dev/null || true
$X xdotool key F1 </dev/null
sleep 1
$X import -window root /shots/before_summon.png </dev/null
# Mob 14 blocks in front, facing the camera (yaw 180 = north); its goal walks it to ~3 blocks from Dev.
rcon summon colossus:colossus 0.5 -60 14.5 '{Rotation:[180f,0f]}'
sleep 0.3
for i in $(seq -w 1 "$N"); do
  $X import -window root "/shots/walk_$i.png" </dev/null
  sleep "$DT"
done
rcon data get entity '@e[type=colossus:colossus,limit=1]' Pos
burst() {  # burst <prefix>
  for i in $(seq -w 1 "$N"); do $X import -window root "/shots/${1}_$i.png" </dev/null; sleep "$DT"; done
}
lure() { rcon summon armor_stand "$@" '{Invisible:1b,Marker:1b,NoGravity:1b,Tags:["colossus_lure"]}'; }
stage_reset() { rcon tp '@e[type=colossus:colossus]' 0.5 -120 0.5 >/dev/null; rcon kill '@e[type=colossus:colossus]' >/dev/null; rcon kill '@e[tag=colossus_lure]' >/dev/null; rcon tp Dev 0.5 -60 0.5 0 -8 >/dev/null; sleep 2; }
# Side view: mob walks +X (east) along z=5.5 (5 blocks from the camera); Dev faces south, so east is screen-left and the mob is seen in profile
# facing left, like the reference SIDE view. A lure at x=+14.5 steers it.
stage_reset
lure 14.5 -60 5.5
rcon summon colossus:colossus -12.5 -60 5.5 '{Rotation:[-90f,0f]}'
sleep 3
burst side
rcon data get entity '@e[type=colossus:colossus,limit=1]' Pos
# Back view: mob walks away from the camera (+Z) toward a lure 30 blocks out.
stage_reset
lure 0.5 -60 30.5
rcon summon colossus:colossus 0.5 -60 3.5 '{Rotation:[0f,0f]}'
sleep 0.5
burst back
rcon data get entity '@e[type=colossus:colossus,limit=1]' Pos
stage_reset
docker logs mc-client 2>&1 | grep -iE 'colossus|exception' | grep -v DEBUG | tail -20 || true
rcon kick Dev >/dev/null || true; sleep 2   # clean disconnect (no netty reset in server log)
docker stop mc-client >/dev/null   # left stopped (not removed); the next run recreates it
ls -l "$OUT"
