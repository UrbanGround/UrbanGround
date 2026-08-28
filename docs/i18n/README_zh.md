<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround：从局部感知到真实尺度城市中的空间自主能力">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>项目主页</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#应用下载"><strong>应用下载</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>MIT 许可证</strong></a>
</p>

<p align="center">
  <a href="https://huggingface.co/papers/2608.27456">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Paper%202608.27456-FFD21E?style=flat-square" alt="Hugging Face Paper 2608.27456">
  </a>
  <a href="https://arxiv.org/abs/2608.27456">
    <img src="https://img.shields.io/badge/arXiv-2608.27456-b31b1b?style=flat-square&logo=arxiv&logoColor=white" alt="arXiv 2608.27456">
  </a>
</p>

<p align="center">
  <a href="../../README.md">English</a> &middot;
  <strong>简体中文</strong> &middot;
  <a href="README_fr.md">Français</a> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <a href="README_de.md">Deutsch</a> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="楼梯通行演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="街道级探索演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="地图视图控制演示"></td>
  </tr>
  <tr>
    <td align="center"><strong>楼梯通行</strong></td>
    <td align="center"><strong>街道级探索</strong></td>
    <td align="center"><strong>地图视图控制</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="地点搜索演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="地图传送演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="行人导航演示"></td>
  </tr>
  <tr>
    <td align="center"><strong>地点搜索</strong></td>
    <td align="center"><strong>地图传送</strong></td>
    <td align="center"><strong>行人导航</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="天气控制演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="时段控制演示"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="智能体集成演示"></td>
  </tr>
  <tr>
    <td align="center"><strong>天气控制</strong></td>
    <td align="center"><strong>时段控制</strong></td>
    <td align="center"><strong>智能体集成</strong></td>
  </tr>
</table>

UrbanGround 是一个用于多模态大语言模型智能体闭环评估的真实尺度城市沙盒。它将香港全域的三维地理空间数据转化为持续渲染、支持物理交互的 Unity 环境。智能体通过第一人称相机观察城市，借助精简的控制接口采取行动，并根据其在环境中实际执行的轨迹接受评估。

配套实验任务从局部场景理解逐步扩展到显式导航、隐式目的地推断、多站点规划，以及环境变化后的重新规划。每项原始任务均已在发布的应用程序中手动执行并核验。

## 应用下载

[项目主页](https://urbanground.github.io/#play-online)提供可直接使用的浏览器版。你可以用键盘和鼠标以第一人称进行探索，也可以提供兼容 OpenAI 的端点、API 密钥、模型名称和指令，让 MLLM 对其进行控制。密钥仅保留在当前浏览器会话中，UrbanGround 不会记录该密钥。

桌面应用程序二进制文件与任务 JSON 文件一并通过 GitHub Release 压缩包分发，不存储在 Git 仓库中。桌面软件包采用经过优化的非开发版 Unity IL2CPP 构建，而不是 Mono 构建。相应的 Release 资源发布后，下方下载链接即可使用。

| 平台 | 应用程序 | 安装说明 |
| --- | --- | --- |
| Web | [在浏览器中运行 UrbanGround](https://urbanground.github.io/#play-online) | 无需安装 |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

下载适用于你的操作系统的压缩包，并将其解压到对应的本地目录。每个软件包都会将 `sandbox.cfg` 和已发布的 `task` 目录与应用程序放在同一目录下：

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

评估器仅从所选软件包的 `<build-folder>/task` 目录解析任务，不使用仓库根目录级别的任务路径。因此，切换应用程序软件包时，也会一并选择随该软件版本发布的任务集。

## 系统概览

UrbanGround 是一个基于香港全域三维地理空间数据构建的真实尺度城市沙盒。它通过同一套接口支持直接的第一人称操作，以及由 MLLM 智能体进行的程序化控制。我们提供 Web 版沙盒以及适用于 macOS、Windows 和 Linux 的原生构建版本。此外，它还包含多样化任务，用于研究多模态智能体如何感知真实城市并在其中行动。

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="UrbanGround 环境及其交互模式概览">
</p>

## 环境

UrbanGround 由三层组成。

- **地理空间层。** 环境以地理配准的 Cesium 3D Tiles 形式流式加载[香港地政总署](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)发布的三维可视化地图（3D Visualisation Map）。[三维行人网络（3D Pedestrian Network）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)在同一 WGS84 坐标系中对齐，并保留为用于路线分析的连通图。
- **仿真层。** Unity 场景提供连续的第一人称移动、与建筑物及地形的碰撞、可控时钟、雨雾效果，以及在已配准行人网络上移动的动画行人。
- **智能体层。** 本地 HTTP 接口提供 RGB 观测、物理动作、地图交互、任务加载和评估器状态。智能体始终处于连续空间中；行人图仅用于分析，而不作为移动约束。

*（可选）* 公共瓦片服务便于交互式使用，但当实验需要反复切换位置时，全域数据的流式加载可能较慢。对于重复运行或大规模运行，请在本地 HTTP 服务器上镜像官方的三棵 3D Tiles 目录树，并保持以下布局：

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

编辑应用程序旁的 `sandbox.cfg`，将 `internal_base_url` 指向该 HTTP 根地址：

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

请用提供瓦片服务的机器地址替换示例 IP。UrbanGround 启动时会探测该镜像；若镜像不可用，则回退到地政总署的服务。可通过 `GET /tileset_source` 查看当前使用的数据源。将瓦片数据保留在本地网络中，可显著缩短反复传送和大规模评估运行时的加载时间。

## 控制与 API

手动控制、地图交互、HTTP 端点、动作模式定义、任务加载、屏幕截图和 Python 示例均记录在 [`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md) 中。桌面应用程序默认在 `http://127.0.0.1:8081` 提供 API 服务。

## 实验数据与评估

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="五级实验任务层次结构">
</p>

论文使用由五个层级组成的实验任务集合，对智能体在环境中的行为进行分析和验证。该任务集作为实验数据随应用程序一起发布，而非作为独立的软件组件发布。

| 层级 | 能力 | 任务类型 |
| --- | --- | --- |
| 1 | 局部环境理解 | 视觉识别（Visual Recognition，VR）、方位理解（Orientation Understanding，OU）、主动探索问题（Active Exploration Questions，AEQ） |
| 2 | 明确指令下的导航 | 短程目标导航（Short-range Goal Navigation，SGN）、长程目标导航（Long-range Goal Navigation，LGN）、指令导航（Instructional Navigation，IN）、约束导航（Constrained Navigation，CN） |
| 3 | 隐式指令下的探索 | 地点类型搜索（Place-Type Search，PTS）、隐式意图推断（Implicit Intent Inference，III） |
| 4 | 多任务规划 | 时间窗口调度（Time-Window Scheduling，TWS）、多站点路线规划（Multi-Stop Route Planning，MSP） |
| 5 | 动态环境交互 | 动态道路封闭重新规划（Dynamic Road-Closure Replanning，DCR）、行人间导航（Navigation among Pedestrians，NP） |

发布的实验协议包含 700 个经过人工核验的基础实例。实验数据分布在香港多个不同的城区。下图汇总了其地理覆盖范围，以及五个阶段各自的任务实例数量。

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="实验任务在香港各地的空间分布"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="五个实验阶段的任务实例数量"></td>
  </tr>
</table>

## 安装

评估代码要求 Python 3.10 或更高版本。运行回合前，请先下载适用于主机操作系统的应用程序软件包。

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

配置兼容 OpenAI 的多模态模型端点。若省略 `AGENT_API_BASE`，则默认使用 OpenAI API。

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

从公共服务首次加载瓦片可能需要几分钟，具体取决于所选区域和网络连接。对于重复实验，建议使用[环境](#环境)一节所述的本地镜像。

## 运行评估

按 ID 运行一项任务：

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

评估器会根据主机操作系统自动选择 `Builds/macOS`、`Builds/Windows` 或 `Builds/Linux`。可用 `--build-folder` 选择另行解压的软件包。

使用 glob 模式选择一个任务族：

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

运行完整的实验协议，包括生成的条件变体：

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround 在端口 `8081` 上使用本地动作服务器，因此发布的运行器每次仅评估一个应用程序实例。添加 `--attach` 可使用已经打开的应用程序。后续运行会复用成功的报告；添加 `--force-rerun` 可替换这些报告。

评估产物写入：

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

每个任务目录包含 `report.json` 或 `run_failure.json`；启用相应选项时，还会包含回合视频和源帧。批处理汇总写入 `batch_report.json`。

## 评分与检查

汇总一个模型的结果：

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

比较已完成的模型目录：

```bash
python AgentEvaluation/compare_models.py
```

通过只读结果查看器浏览轨迹、帧、视频和任务级指标：

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

然后打开 `http://localhost:8000`。

## 即将推出

- [ ] 多智能体交互
- [ ] 修复模糊或不完整的场景几何结构
- [ ] 更丰富的车辆和行人类型
- [ ] 精选室内环境

## 数据与第三方组件

UrbanGround 使用香港特别行政区政府发布的[三维可视化地图（3D Visualisation Map）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)和[三维行人网络（3D Pedestrian Network）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)。这些数据集未在本仓库中重新分发，仍受各自原始条款约束。应用程序软件包还包含 Unity 运行时组件、Cesium for Unity 和 Microsoft Rocketbox 虚拟形象；它们分别受各自上游许可证约束。

## 引用

```bibtex
@misc{ju2026urbangroundlocalperceptionspatial,
      title={UrbanGround: From Local Perception to Spatial Agency in a Real-Scale City},
      author={Tianjie Ju and Zheng Wu and Yueqing Sun and Yuhan Cui and Bobo Li and Shengqiong Wu and Pengzhou Cheng and Haodong Zhao and Zongru Wu and Xinbei Ma and Doris Zhang and Kunling Li and Mong-Li Lee and Wynne Hsu and Hao Fei and Qi Gu and Gongshen Liu and Zhuosheng Zhang},
      year={2026},
      eprint={2608.27456},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2608.27456},
}
```

## 许可证

[MIT](../../LICENSE)。
