#!/usr/bin/env bash
# Self-authenticating capture: HUD + F3 debug overlay on, Dev (op) types /summon in chat, ffmpeg x11grab records the
# client's Xvfb display while the Colossus walks up. F3 shows "Minecraft 1.21.1 (21.1.256/neoforge)" and, with the
# crosshair on the mob, "Targeted Entity colossus:colossus".
# Output: <outdir>/raw.mp4 (40 s, 1280x720, 15 fps) + still_*.png. Usage: ./record_video.sh <outdir>
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:?usage: record_video.sh <outdir>}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
BASE="${COLOSSUS_DATA:-$ROOT/.data}"
GH="$BASE/gradle-home"
MOD="$ROOT/mod"
rcon() { docker exec mc-server rcon-cli -- "$@" </dev/null | sed "s/\x1b\[[0-9;]*m//g"; }
ts() { date -u +%H:%M:%S; }

docker image inspect mc-client-img >/dev/null 2>&1 || \
  docker build -t mc-client-img -f "$ROOT/docker/client.Dockerfile" "$ROOT/docker" </dev/null || exit 1
echo "$(ts) build recording image (client image + ffmpeg)"
docker build -q -t mc-client-live-img - <<'DF' >/dev/null || { echo "image build failed"; exit 1; }
FROM mc-client-img
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
DF
echo "$(ts) server up"
"$ROOT/server_up.sh" --no-selftest || exit 1
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
joined() { docker logs --since "$START" mc-server 2>&1 | grep -c 'Dev joined the game' >/dev/null; }
docker run -d --name mc-client --network mc-test --user "$(id -u):$(id -g)" \
  -e GRADLE_USER_HOME="$GH" -e HOME="$GH/home" \
  -e MC_CLIENT_ARGS="--username Dev --width 1280 --height 720 --quickPlayMultiplayer mc-server:25565" \
  -v "$MOD:$MOD" -v "$GH:$GH" -v "$OUT:/live" -w "$MOD" \
  mc-client-live-img bash -c 'Xvfb :99 -screen 0 1280x720x24 -nolisten tcp >/tmp/xvfb.log 2>&1 & sleep 2; exec ./gradlew --no-daemon --console=plain runClient' >/dev/null
echo "$(ts) client starting; waiting for Dev to join (first run downloads assets)..."
for i in $(seq 1 240); do
  joined && break
  [ -n "$(docker ps -q -f name='^mc-client$')" ] || { docker logs --tail 80 mc-client; echo "mc-client died"; exit 1; }
  sleep 5
done
joined || { echo "timeout: Dev never joined"; exit 1; }
echo "$(ts) Dev joined"
rcon op Dev
rcon gamemode survival Dev
rcon difficulty peaceful
rcon time set day
rcon gamerule doDaylightCycle false
rcon gamerule doWeatherCycle false
rcon weather clear
rcon kill '@e[type=colossus:colossus]'
rcon kill '@e[tag=colossus_lure]'
rcon tp Dev 0.5 -60 0.5 0 -8
sleep 20   # let chunks mesh on llvmpipe
X="docker exec -e DISPLAY=:99 mc-client"
$X xdotool mousemove 640 360 </dev/null || true
WID=$($X xdotool search --name 'Minecraft' </dev/null | head -1 || true)
[ -n "$WID" ] && $X xdotool windowfocus "$WID" </dev/null || true
$X xdotool key F3 </dev/null
sleep 3
$X import -window root /live/still_01_f3_before_summon.png </dev/null
echo "$(ts) start recording"
docker exec -d -e DISPLAY=:99 mc-client sh -c 'ffmpeg -hide_banner -y -f x11grab -video_size 1280x720 -framerate 15 -draw_mouse 0 -i :99 -t 40 -c:v libx264 -preset ultrafast -crf 20 -pix_fmt yuv420p /live/raw.mp4 >/live/ffmpeg.log 2>&1'
sleep 2
$X xdotool key t </dev/null; sleep 1.5
$X xdotool type --delay 60 '/summon colossus:colossus ~ ~ ~12' </dev/null; sleep 1
$X import -window root /live/still_02_chat_typed.png </dev/null
$X xdotool key Return </dev/null
echo "$(ts) summon sent via chat"
sleep 1.5
$X import -window root /live/still_03_walking.png </dev/null
sleep 3
$X import -window root /live/still_04_walking.png </dev/null
sleep 3
$X import -window root /live/still_05_walking.png </dev/null
sleep 6
rcon data get entity '@e[type=colossus:colossus,limit=1]' Pos
$X import -window root /live/still_06_close.png </dev/null
echo "$(ts) waiting for the recording to finish"
for i in $(seq 1 40); do $X pgrep ffmpeg </dev/null >/dev/null || break; sleep 2; done
tail -1 "$OUT/ffmpeg.log"
grep -E 'Dev|Summoned|colossus' "$BASE/server/logs/latest.log" | tail -8
rcon kick Dev >/dev/null || true; sleep 2   # clean disconnect
docker stop mc-client >/dev/null
ls -l "$OUT"
echo "$(ts) DONE"
