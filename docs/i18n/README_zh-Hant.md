<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround：從局部感知到真實尺度城市中的空間自主能力">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>項目專頁</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#應用程式下載"><strong>應用程式下載</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#引用"><strong>論文與引用</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>MIT 授權條款</strong></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> &middot;
  <a href="README_zh.md">简体中文</a> &middot;
  <a href="README_fr.md">Français</a> &middot;
  <strong>繁體中文</strong> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="樓梯通行示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="街道層級探索示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="地圖檢視控制示範"></td>
  </tr>
  <tr>
    <td align="center"><strong>樓梯通行</strong></td>
    <td align="center"><strong>街道層級探索</strong></td>
    <td align="center"><strong>地圖檢視控制</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="地點搜尋示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="地圖傳送示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="行人導航示範"></td>
  </tr>
  <tr>
    <td align="center"><strong>地點搜尋</strong></td>
    <td align="center"><strong>地圖傳送</strong></td>
    <td align="center"><strong>行人導航</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="天氣控制示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="時段控制示範"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="智能體整合示範"></td>
  </tr>
  <tr>
    <td align="center"><strong>天氣控制</strong></td>
    <td align="center"><strong>時段控制</strong></td>
    <td align="center"><strong>智能體整合</strong></td>
  </tr>
</table>

UrbanGround 是一個用於多模態大型語言模型智能體閉環評估的真實尺度城市沙盒。它將全港的三維地理空間資料轉換成持續渲染且支援物理互動的 Unity 環境。智能體透過第一人稱攝影機觀察城市，藉由精簡的控制介面採取行動，並依據其在環境中實際執行的軌跡接受評估。

隨附的實驗任務從局部場景理解逐步延伸至顯式導航、隱式目的地推斷、多站點規劃，以及環境變化後的重新規劃。每項原始任務均已在發布的應用程式中手動執行並核驗。

## 應用程式下載

[項目專頁](https://urbanground.github.io/#play-online)提供可直接使用的瀏覽器版本。你可以使用鍵盤和滑鼠以第一人稱進行探索，也可以提供與 OpenAI 相容的端點、API 密鑰、模型名稱和指令，交由 MLLM 控制。密鑰僅保留在目前的瀏覽器工作階段中，UrbanGround 不會記錄該密鑰。

桌面應用程式的二進制檔案與任務 JSON 檔案一併透過 GitHub Release 壓縮檔發布，不會儲存在 Git 儲存庫中。桌面套件採用經過優化的非開發版 Unity IL2CPP 組建，而非 Mono 組建。對應的 Release 檔案發布後，下方下載連結即可使用。

| 平台 | 應用程式 | 安裝說明 |
| --- | --- | --- |
| Web | [在瀏覽器中執行 UrbanGround](https://urbanground.github.io/#play-online) | 無須安裝 |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

下載適用於你的作業系統的壓縮檔，並將其解壓縮至對應的本地目錄。每個套件都會將 `sandbox.cfg` 和已發布的 `task` 目錄與應用程式放在同一目錄下：

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

評估器僅從所選套件的 `<build-folder>/task` 目錄解析任務，不會使用儲存庫根目錄層級的任務路徑。因此，切換應用程式套件時，也會一併選擇隨該軟件版本發布的任務集。

## 系統概覽

UrbanGround 是一個以全港三維地理空間資料建構的真實尺度城市沙盒。它透過同一套介面支援直接的第一人稱操作，以及由 MLLM 智能體進行的程式化控制。我們提供 Web 版沙盒，以及適用於 macOS、Windows 和 Linux 的原生組建版本。此外，它也包含多樣化任務，用於研究多模態智能體如何感知真實城市並在其中行動。

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="UrbanGround 環境及其互動模式概覽">
</p>

## 環境

UrbanGround 由三層組成。

- **地理空間層。** 環境以經過地理配準的 Cesium 3D Tiles 串流載入[香港地政總署](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)發布的三維視像化地圖（3D Visualisation Map）。[三維行人網絡（3D Pedestrian Network）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)在同一 WGS84 坐標系中對齊，並保留為用於路線分析的連通圖。
- **模擬層。** Unity 場景提供連續的第一人稱移動、與建築物及地形的碰撞、可控制的時鐘、雨霧效果，以及在已配準行人網絡上移動的動畫行人。
- **智能體層。** 本地 HTTP 介面提供 RGB 觀測、物理動作、地圖互動、任務載入和評估器狀態。智能體始終處於連續空間中；行人圖僅用於分析，而不作為移動約束。

*（選用）* 公共圖磚服務方便互動式使用，但當實驗需要反覆切換位置時，全港資料的串流載入可能較慢。若需重複執行或進行大規模執行，請在本地 HTTP 伺服器上鏡像三棵官方 3D Tiles 目錄樹，並保持以下目錄結構：

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

編輯應用程式旁的 `sandbox.cfg`，將 `internal_base_url` 指向該 HTTP 根地址：

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

請以提供圖磚服務的主機地址取代示例 IP。UrbanGround 啟動時會探測該鏡像；若鏡像無法使用，則改用地政總署的服務。可透過 `GET /tileset_source` 檢查目前使用的資料來源。將圖磚資料保留在本地網絡中，可大幅縮短反覆傳送及大規模評估執行時的載入時間。

## 控制與 API

手動控制、地圖互動、HTTP 端點、動作結構定義、任務載入、屏幕截圖和 Python 示例均記錄於 [`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md)。桌面應用程式預設在 `http://127.0.0.1:8081` 提供 API 服務。

## 實驗資料與評估

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="五級實驗任務階層">
</p>

論文採用由五個層級組成的實驗任務集合，分析並驗證智能體在環境中的行為。此任務集以實驗資料的形式隨應用程式一併發布，而非作為獨立的軟件組件發布。

| 層級 | 能力 | 任務類型 |
| --- | --- | --- |
| 1 | 局部環境理解 | 視覺識別（Visual Recognition，VR）、方位理解（Orientation Understanding，OU）、主動探索問題（Active Exploration Questions，AEQ） |
| 2 | 明確指令下的導航 | 短程目標導航（Short-range Goal Navigation，SGN）、長程目標導航（Long-range Goal Navigation，LGN）、指令導航（Instructional Navigation，IN）、約束導航（Constrained Navigation，CN） |
| 3 | 隱式指令下的探索 | 地點類型搜尋（Place-Type Search，PTS）、隱式意圖推斷（Implicit Intent Inference，III） |
| 4 | 多任務規劃 | 時間窗口調度（Time-Window Scheduling，TWS）、多站點路線規劃（Multi-Stop Route Planning，MSP） |
| 5 | 動態環境互動 | 動態道路封閉重新規劃（Dynamic Road-Closure Replanning，DCR）、行人之間的導航（Navigation among Pedestrians，NP） |

發布的實驗協議包含 700 個經過人工核驗的基礎實例。實驗資料分布在香港多個不同的城區。下圖彙總其地理涵蓋範圍，以及五個階段各自的任務實例數量。

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="實驗任務在香港各地的空間分布"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="五個實驗階段的任務實例數量"></td>
  </tr>
</table>

## 安裝

評估程式碼需要 Python 3.10 或更新版本。執行回合前，請先下載適用於主機作業系統的應用程式套件。

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

設定與 OpenAI 相容的多模態模型端點。若省略 `AGENT_API_BASE`，則預設使用 OpenAI API。

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

首次從公共服務載入圖磚可能需要數分鐘，實際時間取決於所選區域及網絡連線。若要重複進行實驗，建議使用[環境](#環境)一節所述的本地鏡像。

## 執行評估

依 ID 執行一項任務：

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

評估器會依據主機作業系統自動選擇 `Builds/macOS`、`Builds/Windows` 或 `Builds/Linux`。可使用 `--build-folder` 選擇另外解壓縮的套件。

使用 glob 模式選擇一個任務族：

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

執行完整的實驗協議，包括生成的條件變體：

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround 在連接埠 `8081` 上使用本地動作伺服器，因此發布的執行器每次僅評估一個應用程式實例。加入 `--attach` 可使用已經開啟的應用程式。後續執行會重用成功的報告；加入 `--force-rerun` 可替換這些報告。

評估產物會寫入：

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

每個任務目錄包含 `report.json` 或 `run_failure.json`；啟用相應選項時，還會包含回合影片和原始幀。批量摘要會寫入 `batch_report.json`。

## 評分與檢查

彙總一個模型的結果：

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

比較已完成的模型目錄：

```bash
python AgentEvaluation/compare_models.py
```

透過只讀結果檢視器瀏覽軌跡、幀、影片和任務層級指標：

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

然後開啟 `http://localhost:8000`。

## 即將推出

- [ ] 多智能體互動
- [ ] 修復模糊或不完整的場景幾何結構
- [ ] 更多種類的車輛和行人
- [ ] 精選室內環境

## 資料與第三方組件

UrbanGround 使用香港特別行政區政府發布的[三維視像化地圖（3D Visualisation Map）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)和[三維行人網絡（3D Pedestrian Network）](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)。這些資料集不會在本儲存庫中重新發布，且仍受其原始條款約束。應用程式套件亦包含 Unity 運行時組件、Cesium for Unity 和 Microsoft Rocketbox 虛擬化身；各組件仍受其上游授權條款約束。

## 引用

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

## 授權條款

[MIT](../../LICENSE)。
