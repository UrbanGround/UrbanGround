<p align="center">
  <img src="docs/assets/urbanground-header.png" width="940" alt="UrbanGround: From Local Perception to Spatial Agency in a Real-Scale City">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>Project Page</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#application-downloads"><strong>App Download</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#citation"><strong>Paper &amp; Citation</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="LICENSE"><strong>MIT License</strong></a>
</p>

<p align="center">
  <a href="https://huggingface.co/papers/2608.27456">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Paper%202608.27456-FFD21E?style=flat-square" alt="Hugging Face Paper 2608.27456">
  </a>
</p>

<p align="center">
  <strong>English</strong> &middot;
  <a href="docs/i18n/README_zh.md">简体中文</a> &middot;
  <a href="docs/i18n/README_fr.md">Français</a> &middot;
  <a href="docs/i18n/README_zh-Hant.md">繁體中文</a> &middot;
  <a href="docs/i18n/README_ja.md">日本語</a> &middot;
  <a href="docs/i18n/README_ko.md">한국어</a> &middot;
  <a href="docs/i18n/README_ar.md">العربية</a> &middot;
  <a href="docs/i18n/README_de.md">Deutsch</a> &middot;
  <a href="docs/i18n/README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="docs/assets/demos/stair-traversal.webp" width="100%" alt="Stair Traversal demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/street-exploration.webp" width="100%" alt="Street-Level Exploration demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/map-view-control.webp" width="100%" alt="Map View Control demo"></td>
  </tr>
  <tr>
    <td align="center"><strong>Stair Traversal</strong></td>
    <td align="center"><strong>Street-Level Exploration</strong></td>
    <td align="center"><strong>Map View Control</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="docs/assets/demos/place-search.webp" width="100%" alt="Place Search demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/map-teleportation.webp" width="100%" alt="Map Teleportation demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/pedestrian-navigation.webp" width="100%" alt="Pedestrian Navigation demo"></td>
  </tr>
  <tr>
    <td align="center"><strong>Place Search</strong></td>
    <td align="center"><strong>Map Teleportation</strong></td>
    <td align="center"><strong>Pedestrian Navigation</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="docs/assets/demos/weather-control.webp" width="100%" alt="Weather Control demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/time-of-day-control.webp" width="100%" alt="Time-of-Day Control demo"></td>
    <td width="33.33%" align="center"><img src="docs/assets/demos/agent-integration.webp" width="100%" alt="Agent Integration demo"></td>
  </tr>
  <tr>
    <td align="center"><strong>Weather Control</strong></td>
    <td align="center"><strong>Time-of-Day Control</strong></td>
    <td align="center"><strong>Agent Integration</strong></td>
  </tr>
</table>

UrbanGround is a real-scale urban sandbox for closed-loop evaluation of multimodal large
language model agents. It transforms territory-wide 3D geospatial data of Hong Kong into a
continuously rendered and physically interactive Unity environment. An agent observes the city
through a first-person camera, acts through a compact control interface, and is evaluated from
the trajectory it executes in the environment.

The accompanying experimental tasks progress from local scene understanding to explicit
navigation, implicit destination inference, multi-stop planning, and replanning after
environmental change. Each source task was manually executed and checked in the released
application.

## Application downloads

The [project page](https://urbanground.github.io/#play-online) includes a browser edition for
direct use. It can be explored in first person with keyboard and mouse, or placed under MLLM
control by supplying an OpenAI-compatible endpoint, API key, model name, and instruction. The
key remains in the current browser session and is not recorded by UrbanGround.

Desktop application binaries and task JSON files are distributed together as GitHub Release
archives, not stored in the Git repository. Desktop packages use optimized non-development Unity
IL2CPP builds rather than Mono builds. The download links below become available when the
corresponding release assets are published.

| Platform | Application | Installation |
| --- | --- | --- |
| Web | [Play UrbanGround in the browser](https://urbanground.github.io/#play-online) | No installation |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](Builds/Linux/README.md) |

Download the archive for your operating system and extract it into the matching local
destination. Each package keeps `sandbox.cfg` and the released `task` directory beside the
application:

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

The evaluator resolves tasks only from the selected package's `<build-folder>/task` directory.
It does not use a repository-level task path. Switching the application package therefore also
selects the task set released with that version of the software.

## System overview

UrbanGround is a real-scale urban sandbox built from territory-wide 3D geospatial data. It
supports direct first-person play and programmatic control by MLLM agents through the same
interface. We release the sandbox on the web and as native builds for macOS, Windows, and Linux.
It also includes diverse tasks for studying how multimodal agents perceive and act in a real
city.

<p align="center">
  <img src="docs/assets/urbanground-overview.jpg" width="100%" alt="Overview of the UrbanGround environment and interaction modes">
</p>

## Environment

UrbanGround is organized into three layers.

- **Geospatial layer.** The environment streams the 3D Visualisation Map released by the
  [Hong Kong Lands Department](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
  as georegistered Cesium 3D Tiles. The
  [3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
  is aligned in the same WGS84 frame and retained as a connected graph for route analysis.
- **Simulation layer.** The Unity scene provides continuous first-person motion, collision
  with buildings and terrain, a controllable clock, rain and fog, and animated pedestrians
  moving on the registered pedestrian network.
- **Agent layer.** A local HTTP interface exposes RGB observations, physical actions, map
  interaction, task loading, and evaluator state. Agents remain in continuous space; the
  pedestrian graph is used for analysis rather than as a movement constraint.

*(Optional)* The public tile service is convenient for interactive use, but territory-wide streaming can be
slow when an experiment repeatedly changes location. For repeated or large-scale runs, mirror
the three official 3D Tiles trees on a local HTTP server while preserving the following layout:

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

Edit the `sandbox.cfg` beside the application and point `internal_base_url` to that HTTP root:

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

Use the address of the machine serving the tiles in place of the example IP. UrbanGround probes
the mirror at startup and falls back to the Lands Department service if it is unavailable. The
active source can be checked through `GET /tileset_source`. Keeping the tile data on the local
network substantially reduces loading time during repeated teleportation and large evaluation
runs.

## Controls and API

Manual controls, map interaction, HTTP endpoints, action schemas, task loading, screenshots,
and Python examples are documented in
[`docs/CONTROLS_AND_API.md`](docs/CONTROLS_AND_API.md). The desktop application serves the API
at `http://127.0.0.1:8081` by default.

## Experimental data and evaluation

<p align="center">
  <img src="docs/assets/experimental-task-hierarchy.jpg" width="100%" alt="Five-level experimental task hierarchy">
</p>

The paper uses a five-level collection of experimental tasks to analyze and validate agent
behavior in the environment. It is released as experimental data with the application rather
than as a separate software component.

| Level | Capability | Task types |
| --- | --- | --- |
| 1 | Local environment understanding | Visual Recognition (VR), Orientation Understanding (OU), Active Exploration Questions (AEQ) |
| 2 | Navigation under explicit instructions | Short-range Goal Navigation (SGN), Long-range Goal Navigation (LGN), Instructional Navigation (IN), Constrained Navigation (CN) |
| 3 | Exploration under implicit instructions | Place-Type Search (PTS), Implicit Intent Inference (III) |
| 4 | Multi-task planning | Time-Window Scheduling (TWS), Multi-Stop Route Planning (MSP) |
| 5 | Dynamic environment interaction | Dynamic Road-Closure Replanning (DCR), Navigation among Pedestrians (NP) |

The released protocol contains 700 manually verified base instances. The experimental data is
distributed across diverse urban regions of Hong Kong. Its geographic coverage and the number
of task instances in each of the five stages are summarized below.

<table>
  <tr>
    <td width="68%" align="center"><img src="docs/assets/figure-7-task-distribution.png" height="320" alt="Spatial distribution of experimental tasks across Hong Kong"></td>
    <td width="32%" align="center"><img src="docs/assets/figure-8-task-composition.png" height="320" alt="Number of task instances across the five experimental stages"></td>
  </tr>
</table>

## Installation

Python 3.10 or later is required for the evaluation code. Download the application package for
the host operating system before running an episode.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Configure an OpenAI-compatible multimodal model endpoint. `AGENT_API_BASE` defaults to the
OpenAI API when omitted.

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

Initial tile loading from the public service can take several minutes, depending on the selected
region and connection. The local mirror described under [Environment](#environment) is
recommended for repeated experiments.

## Running an evaluation

Run one task by ID:

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

The evaluator automatically selects `Builds/macOS`, `Builds/Windows`, or `Builds/Linux` for the
host operating system. A separately extracted package can be selected with `--build-folder`.

Select a task family with a glob:

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Run the complete experimental protocol, including generated condition variants:

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround uses a local action server on port `8081`, so the released runner evaluates one
application instance at a time. Add `--attach` to use an application that is already open.
Successful reports are reused on subsequent runs; add `--force-rerun` to replace them.

Evaluation artifacts are written to:

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

Each task directory contains `report.json` or `run_failure.json` and, when enabled, an episode
video and source frames. The batch summary is written to `batch_report.json`.

## Scoring and inspection

Summarize one model:

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

Compare completed model directories:

```bash
python AgentEvaluation/compare_models.py
```

Browse trajectories, frames, videos, and task-level metrics through the read-only result viewer:

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

Then open `http://localhost:8000`.

## Coming soon

- [ ] Multi-agent interaction
- [ ] Repair of blurred or incomplete scene geometry
- [ ] A broader range of vehicles and pedestrians
- [ ] Selected indoor environments

## Data and third-party components

UrbanGround uses the
[3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
and
[3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
released by the Government of the Hong Kong Special Administrative Region. These datasets are
not redistributed in the repository and remain subject to their original terms. The application
packages also include Unity runtime components, Cesium for Unity, and Microsoft Rocketbox
avatars; each remains subject to its upstream license.

## Citation

```bibtex
@article{ju2026urbanground,
  title   = {UrbanGround: From Local Perception to Spatial Agency in a Real-Scale City},
  author  = {Ju, Tianjie and Wu, Zheng and Sun, Yueqing and Cui, Yuhan and Li, Bobo and
             Wu, Shengqiong and Cheng, Pengzhou and Zhao, Haodong and Wu, Zongru and
             Ma, Xinbei and Zhang, Doris and Li, Kunling and Lee, Mong-Li and Hsu, Wynne and
             Fei, Hao and Gu, Qi and Liu, Gongshen and Zhang, Zhuosheng},
  year    = {2026}
}
```

## License

[MIT](LICENSE).
