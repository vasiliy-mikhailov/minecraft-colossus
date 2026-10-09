# Colossus — a walking stone knight for Minecraft 1.21.1 (NeoForge)

A NeoForge mod that adds the **Colossus**: a 3-block-tall armoured stone knight with a crested great helm, glowing eye
slits, gold-trimmed plate, chainmail arms and a stone sword. It walks up to the nearest player and stops about 3 blocks
away. It is not hostile, so it also spawns on Peaceful.

| Front | Side | Back |
|---|---|---|
| ![front](docs/screenshots/walk_6.png) | ![side](docs/screenshots/side_4.png) | ![back](docs/screenshots/back_4.png) |

These are in-game frames from the Minecraft 1.21.1 client with NeoForge 21.1.256, captured by the test harness below.
The client is the NeoForge dev client, running headless on Xvfb with Mesa llvmpipe software rendering.
`docs/screenshots/` holds the full bursts: `walk_*` (toward the camera), `side_*` (profile) and `back_*` (walking away).

## Play

1. Install Minecraft 1.21.1 with NeoForge 21.1.x (tested on 21.1.256).
2. Get `colossus-1.0.0.jar`, either from the **colossus-jar** artifact of the latest
   [Build](../../actions/workflows/build.yml) run or by building it yourself (below).
3. Drop the jar into `mods/`. On a server, put it in the server's `mods/` too, since the model and renderer are client-side.
4. In game: `/summon colossus:colossus ~ ~ ~5`, or use the **Colossus Spawn Egg** from the Spawn Eggs creative tab.

| | |
|---|---|
| Health | 100 (50 hearts) |
| Speed | 0.23 (a heavy walk) |
| Knockback resistance | 1.0 |
| Hitbox | 1.5 × 3.3 blocks |
| AI | float → walk to the nearest player within 32 blocks (stops at ~3) → look at player → wander |

The approach goal prefers any living entity tagged `colossus_lure` within 32 blocks over the player. The harness uses an
invisible armor stand with that tag to film side and back views. Without a lure it behaves as described above.

## Build

```bash
./build.sh                      # Gradle inside eclipse-temurin:21-jdk; only Docker is needed
# or, with JDK 21 installed:
cd mod && ./gradlew build
```

Output: `mod/build/libs/colossus-1.0.0.jar`.

## Test harness (Docker)

The harness runs a real NeoForge server and a headless game client in Docker, then takes screenshots of the Colossus
walking. Nothing is published on host ports; the client and server talk over a private Docker network, `mc-test`.

```bash
./build.sh
./server_up.sh                  # NeoForge 1.21.1 server 'mc-server' + self-test -> prints SELFTEST PASS
./client_shoot.sh shots/run1    # dev client 'mc-client' joins as Dev; front/side/back walk bursts -> shots/run1/
./server_down.sh                # remove both containers (the world is kept)
```

- **Self-test:** loads the mod, summons a Colossus over RCON, checks it is still alive after 200+ ticks, and requires
  zero `Exception`/`ERROR` lines in the server log.
- **Client:** `./gradlew runClient` on Xvfb `:99` (1280×720) with Mesa llvmpipe, using `--quickPlayMultiplayer mc-server:25565`.
  The scene is staged over RCON, the HUD is hidden with `xdotool key F1`, and frames are grabbed with `import -window root`.
- **State:** the Gradle home, server world and RCON password live under `$COLOSSUS_DATA` (default `./.data`, gitignored).
  The first run downloads the NeoForge server, game assets and Gradle dependencies, a few GB in total.
- **Container names:** `mc-server`, `mc-client`, network `mc-test`, image `mc-client-img` (built from `docker/client.Dockerfile`).

## Model

`model/` holds the Colossus as a Minecraft entity model:

- `colossus.bbmodel`: Blockbench **Modded Entity** project. Open it to view or edit.
- `colossus.png` (128×128, box UV) and `colossus_eyes.png` (emissive eye slits, rendered with `RenderType.eyes`).
- Shape: 52 px (3.25 blocks) tall, 37 cubes.
- Bones: `root → body` (torso, belt, front/back tabard, back plate), `head` (helm + stepped crest), `right_arm → sword`,
  `left_arm`, `right_leg`, `left_leg`.
- Walk cycle in `ColossusModel.setupAnim`: legs swing `cos(limbSwing·0.6662)·1.4·limbSwingAmount` in opposite phase,
  arms counter-swing (the sword arm less), with a slight body bob. Set `STRIDE` lower for a heavier gait.
- `previews/`: offline renders of the box model (3/4 view, walk cycle, texture layout). These are not in-game.

`model/generator/` is the Python (NumPy + Pillow) source that built the model from a front | side | back turnaround
sheet. It writes the geometry, a texture sampled from the sheet, `ColossusModel.java`, `ColossusEyesLayer.java` and the
`.bbmodel` into `model/generator/out/`. The sheet itself is **not** included. Put your own as `model/generator/ref.png`
(794×422, front | side | back; crop boxes in `preview.py`) and run:

```bash
cd model/generator && python3 build.py && python3 export.py && python3 preview.py
```

The Java files in the mod (`mod/src/main/java/com/colossus/client/`) are the generated ones moved into the
`com.colossus.client` package and typed to `HierarchicalModel<ColossusEntity>`.

## Layout

```
mod/                  NeoForge 1.21.1 mod (ModDevGradle, Java 21), mod id `colossus`
  src/main/java/com/colossus/          Colossus (registration), ColossusEntity (AI + attributes)
  src/main/java/com/colossus/client/   ColossusModel, ColossusRenderer, ColossusEyesLayer, ColossusClient
  src/main/resources/assets/colossus/  textures, lang, spawn-egg item model
model/                Blockbench project, textures, offline previews, Python generator
docs/screenshots/     in-game frames from the harness
build.sh  server_up.sh  client_shoot.sh  server_down.sh  docker/client.Dockerfile
```

## License

MIT. See [LICENSE](LICENSE). The ModDevGradle template files are © NeoForged, also under MIT
([mod/TEMPLATE_LICENSE.txt](mod/TEMPLATE_LICENSE.txt)). The mod compiles against Mojang's official mappings, which are
covered by [their own license](https://github.com/NeoForged/NeoForm/blob/main/Mojang.md). This project is not affiliated
with Mojang or Microsoft.
