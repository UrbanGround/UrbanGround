<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround：局所知覚から実スケール都市における空間的エージェンシーへ">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>プロジェクトページ</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#アプリケーションのダウンロード"><strong>アプリをダウンロード</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#引用"><strong>論文・引用</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>MIT ライセンス</strong></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> &middot;
  <a href="README_zh.md">简体中文</a> &middot;
  <a href="README_fr.md">Français</a> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <strong>日本語</strong> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <a href="README_de.md">Deutsch</a> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="階段移動のデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="路上探索のデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="地図ビュー操作のデモ"></td>
  </tr>
  <tr>
    <td align="center"><strong>階段の移動</strong></td>
    <td align="center"><strong>路上探索</strong></td>
    <td align="center"><strong>地図ビューの操作</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="場所検索のデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="地図テレポートのデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="歩行者ナビゲーションのデモ"></td>
  </tr>
  <tr>
    <td align="center"><strong>場所検索</strong></td>
    <td align="center"><strong>地図テレポート</strong></td>
    <td align="center"><strong>歩行者ナビゲーション</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="天候制御のデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="時刻制御のデモ"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="エージェント統合のデモ"></td>
  </tr>
  <tr>
    <td align="center"><strong>天候制御</strong></td>
    <td align="center"><strong>時刻制御</strong></td>
    <td align="center"><strong>エージェント統合</strong></td>
  </tr>
</table>

UrbanGround は、マルチモーダル大規模言語モデル（MLLM）エージェントを閉ループで評価するための、
実スケール都市サンドボックスです。香港全域の 3D 地理空間データを、連続的にレンダリングされ、
物理的なインタラクションが可能な Unity 環境へ変換します。エージェントは一人称視点カメラを通して
都市を観察し、コンパクトな操作インターフェースを介して行動します。その評価は、環境内で実行した
軌跡に基づいて行われます。

付属する実験タスクは、局所的なシーン理解から、明示的なナビゲーション、暗黙的な目的地の推論、
複数地点の計画、環境変化後の再計画へと段階的に進みます。元となる各タスクは、公開アプリケーション上で
手動で実行・検証済みです。

## アプリケーションのダウンロード

[プロジェクトページ](https://urbanground.github.io/#play-online)では、すぐに利用できるブラウザ版を
提供しています。キーボードとマウスを使って一人称視点で探索できるほか、OpenAI 互換エンドポイント、
API キー、モデル名、および指示を指定して、MLLM による制御下に置くこともできます。キーは現在の
ブラウザセッション内にのみ保持され、UrbanGround によって記録されることはありません。

デスクトップアプリケーションのバイナリとタスク JSON ファイルは、Git リポジトリには格納せず、
GitHub Release のアーカイブとしてまとめて配布しています。デスクトップパッケージには Mono ビルドではなく、
開発用ではない最適化済みの Unity IL2CPP ビルドを使用しています。以下のダウンロードリンクは、対応する
リリースアセットが公開されると利用可能になります。

| プラットフォーム | アプリケーション | インストール |
| --- | --- | --- |
| Web | [ブラウザで UrbanGround を実行](https://urbanground.github.io/#play-online) | インストール不要 |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

使用するオペレーティングシステム向けのアーカイブをダウンロードし、対応するローカルの配置先へ展開してください。
各パッケージでは、`sandbox.cfg` と公開済みの `task` ディレクトリがアプリケーションと同じ場所に配置されます。

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

評価プログラムがタスクを読み込む場所は、選択したパッケージの `<build-folder>/task` ディレクトリのみです。
リポジトリ直下のタスクパスは使用しません。したがって、アプリケーションパッケージを切り替えると、
同時にそのソフトウェアバージョンとともに公開されたタスクセットが選択されます。

## システム概要

UrbanGround は、香港全域の 3D 地理空間データから構築された実スケール都市サンドボックスです。
同一のインターフェースを通じて、一人称視点で直接プレイすることも、MLLM エージェントからプログラムで
制御することもできます。このサンドボックスは Web 版に加え、macOS、Windows、Linux 向けの
ネイティブビルドとして公開しています。また、マルチモーダルエージェントが現実の都市をどのように
知覚し、行動するかを研究するための多様なタスクも含まれています。

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="UrbanGround の環境とインタラクション方式の概要">
</p>

## 環境

UrbanGround は 3 つのレイヤーで構成されています。

- **地理空間レイヤー。** [香港地政総署](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)が
  公開する 3D Visualisation Map を、地理参照された Cesium 3D Tiles としてストリーミングします。
  [3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)は
  同じ WGS84 座標系に整合され、経路解析用の連結グラフとして保持されます。
- **シミュレーションレイヤー。** Unity シーンは、連続的な一人称視点移動、建物や地形との衝突、
  制御可能な時計、雨と霧、および位置合わせされた歩行者ネットワーク上を移動するアニメーション付きの
  歩行者を提供します。
- **エージェントレイヤー。** ローカル HTTP インターフェースを通じて、RGB 観測、物理アクション、
  地図操作、タスク読み込み、評価プログラムの状態を公開します。エージェントは連続空間内に留まり、
  歩行者グラフは移動の制約ではなく解析に使用されます。

*（任意）* 公開タイルサービスは対話的な利用には便利ですが、実験で場所を何度も変更する場合、全域の
ストリーミングには時間がかかることがあります。反復実行や大規模な実行では、以下の構成を維持したまま、
公式の 3 つの 3D Tiles ツリーをローカル HTTP サーバーへミラーリングしてください。

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

アプリケーションと同じ場所にある `sandbox.cfg` を編集し、`internal_base_url` にその HTTP ルートを
指定します。

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

例示した IP の代わりに、タイルを配信するマシンのアドレスを使用してください。UrbanGround は起動時に
ミラーを検査し、利用できない場合は地政総署のサービスへフォールバックします。現在使用中のソースは
`GET /tileset_source` で確認できます。タイルデータをローカルネットワーク上に置くことで、テレポートを
繰り返す場合や大規模な評価を実行する場合の読み込み時間を大幅に短縮できます。

## 操作方法と API

手動操作、地図操作、HTTP エンドポイント、アクションスキーマ、タスクの読み込み、スクリーンショット、
Python のサンプルについては、[`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md)を参照してください。
デスクトップアプリケーションは、デフォルトで `http://127.0.0.1:8081` に API を提供します。

## 実験データと評価

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="5 段階の実験タスク階層">
</p>

論文では、環境内におけるエージェントの挙動を分析・検証するために、5 段階からなる実験タスク群を
使用しています。これは独立したソフトウェアコンポーネントではなく、実験データとしてアプリケーションと
ともに公開されています。

| レベル | 能力 | タスクの種類 |
| --- | --- | --- |
| 1 | 局所環境の理解 | 視覚認識（Visual Recognition, VR）、方向理解（Orientation Understanding, OU）、能動的探索質問（Active Exploration Questions, AEQ） |
| 2 | 明示的な指示に基づくナビゲーション | 短距離目標ナビゲーション（Short-range Goal Navigation, SGN）、長距離目標ナビゲーション（Long-range Goal Navigation, LGN）、指示ナビゲーション（Instructional Navigation, IN）、制約付きナビゲーション（Constrained Navigation, CN） |
| 3 | 暗黙的な指示に基づく探索 | 場所タイプ検索（Place-Type Search, PTS）、暗黙的意図推論（Implicit Intent Inference, III） |
| 4 | マルチタスク計画 | 時間枠スケジューリング（Time-Window Scheduling, TWS）、複数地点経路計画（Multi-Stop Route Planning, MSP） |
| 5 | 動的環境とのインタラクション | 動的道路閉鎖時の再計画（Dynamic Road-Closure Replanning, DCR）、歩行者のいる環境でのナビゲーション（Navigation among Pedestrians, NP） |

公開プロトコルには、手作業で検証済みの基本インスタンスが 700 件含まれています。実験データは香港の
多様な都市地域に分布しています。その地理的な範囲と、5 つの各段階におけるタスクインスタンス数を
以下にまとめます。

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="香港全域における実験タスクの空間分布"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="5 つの実験段階におけるタスクインスタンス数"></td>
  </tr>
</table>

## インストール

評価コードには Python 3.10 以降が必要です。エピソードを実行する前に、ホストのオペレーティングシステム用の
アプリケーションパッケージをダウンロードしてください。

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

OpenAI 互換のマルチモーダルモデル用エンドポイントを設定します。`AGENT_API_BASE` を省略した場合は、
デフォルトで OpenAI API が使用されます。

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

公開サービスからの初回タイル読み込みには、選択した地域と接続状況によって数分かかることがあります。
実験を繰り返す場合は、[環境](#環境)で説明したローカルミラーの利用を推奨します。

## 評価の実行

ID を指定して 1 つのタスクを実行します。

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

評価プログラムは、ホストのオペレーティングシステムに応じて `Builds/macOS`、`Builds/Windows`、
`Builds/Linux` のいずれかを自動的に選択します。別の場所に展開したパッケージは、`--build-folder` で
選択できます。

glob パターンを使用してタスクファミリーを選択します。

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

生成された条件バリアントを含む完全な実験プロトコルを実行します。

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround はポート `8081` のローカルアクションサーバーを使用するため、配布されているランナーが一度に評価する
アプリケーションインスタンスは 1 つです。すでに起動しているアプリケーションを使用するには `--attach` を
追加してください。正常終了した実行のレポートは以降の実行で再利用されます。置き換える場合は `--force-rerun` を
追加してください。

評価成果物は次の場所に出力されます。

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

各タスクディレクトリには `report.json` または `run_failure.json` が格納され、有効にしている場合は
エピソード動画と元フレームも格納されます。バッチの概要は `batch_report.json` に出力されます。

## スコアリングと結果の確認

1 つのモデルについて集計します。

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

完了済みのモデルディレクトリを比較します。

```bash
python AgentEvaluation/compare_models.py
```

読み取り専用の結果ビューアーで、軌跡、フレーム、動画、タスク単位の指標を閲覧します。

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

続いて `http://localhost:8000` を開きます。

## 今後の予定

- [ ] マルチエージェントのインタラクション
- [ ] 不鮮明または不完全なシーンジオメトリの修復
- [ ] 車両と歩行者の種類の拡充
- [ ] 一部の屋内環境

## データおよびサードパーティ製コンポーネント

UrbanGround は、香港特別行政区政府が公開する
[3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)と
[3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)を
使用しています。これらのデータセットは本リポジトリでは再配布されず、それぞれの元の利用条件が引き続き
適用されます。また、アプリケーションパッケージには Unity ランタイムコンポーネント、Cesium for Unity、
Microsoft Rocketbox のアバターが含まれており、それぞれに提供元のライセンスが適用されます。

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

## ライセンス

このプロジェクトは [MIT ライセンス](../../LICENSE)の下で公開されています。
