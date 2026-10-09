#!/usr/bin/env bash
# Build the colossus NeoForge 1.21.1 mod jar inside eclipse-temurin:21-jdk.
# Output: mod/build/libs/colossus-<ver>.jar  (extra args are passed to gradle)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GH="${COLOSSUS_DATA:-$ROOT/.data}/gradle-home"
mkdir -p "$GH/home"
docker run --rm --user "$(id -u):$(id -g)" \
  -e GRADLE_USER_HOME="$GH" -e HOME="$GH/home" \
  -v "$ROOT/mod:$ROOT/mod" -v "$GH:$GH" -w "$ROOT/mod" \
  eclipse-temurin:21-jdk ./gradlew --no-daemon --console=plain build "$@" </dev/null
ls -l "$ROOT/mod/build/libs"
