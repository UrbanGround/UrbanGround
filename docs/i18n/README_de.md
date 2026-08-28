<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround: Von lokaler Wahrnehmung zu räumlicher Handlungsfähigkeit in einer Stadt im realen Maßstab">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>Projektseite</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#anwendungsdownloads"><strong>App herunterladen</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#zitation"><strong>Publikation &amp; Zitation</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>MIT-Lizenz</strong></a>
</p>

<p align="center">
  <a href="https://huggingface.co/papers/2608.27456">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Paper%202608.27456-FFD21E?style=flat-square" alt="Hugging Face Paper 2608.27456">
  </a>
</p>

<p align="center">
  <a href="../../README.md">English</a> &middot;
  <a href="README_zh.md">简体中文</a> &middot;
  <a href="README_fr.md">Français</a> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <strong>Deutsch</strong> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="Demo zur Treppenbewältigung"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="Demo zur Erkundung auf Straßenebene"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="Demo zur Steuerung der Kartenansicht"></td>
  </tr>
  <tr>
    <td align="center"><strong>Treppenbewältigung</strong></td>
    <td align="center"><strong>Erkundung auf Straßenebene</strong></td>
    <td align="center"><strong>Steuerung der Kartenansicht</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="Demo zur Ortssuche"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="Demo zur Teleportation über die Karte"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="Demo zur Fußgängernavigation"></td>
  </tr>
  <tr>
    <td align="center"><strong>Ortssuche</strong></td>
    <td align="center"><strong>Teleportation über die Karte</strong></td>
    <td align="center"><strong>Fußgängernavigation</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="Demo zur Wettersteuerung"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="Demo zur Tageszeitsteuerung"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="Demo zur Agentenintegration"></td>
  </tr>
  <tr>
    <td align="center"><strong>Wettersteuerung</strong></td>
    <td align="center"><strong>Tageszeitsteuerung</strong></td>
    <td align="center"><strong>Agentenintegration</strong></td>
  </tr>
</table>

UrbanGround ist eine urbane Sandbox im realen Maßstab für die Closed-Loop-Evaluation von
Agenten auf Basis multimodaler großer Sprachmodelle. Sie überführt flächendeckende
georäumliche 3D-Daten Hongkongs in eine kontinuierlich gerenderte und physisch interaktive
Unity-Umgebung. Ein Agent beobachtet die Stadt durch eine Kamera aus der Ich-Perspektive, handelt über
eine kompakte Steuerungsschnittstelle und wird anhand der in der Umgebung ausgeführten
Trajektorie evaluiert.

Die zugehörigen experimentellen Aufgaben reichen vom lokalen Szenenverständnis über explizite
Navigation, implizite Zielbestimmung und Planung mit mehreren Zwischenstopps bis hin zur
Neuplanung nach Veränderungen der Umgebung. Jede zugrunde liegende Aufgabe wurde in der
veröffentlichten Anwendung manuell ausgeführt und überprüft.

## Anwendungsdownloads

Die [Projektseite](https://urbanground.github.io/#play-online) enthält eine Browserversion zur
direkten Nutzung. Sie kann mit Tastatur und Maus aus der Ich-Perspektive erkundet oder
durch Angabe eines OpenAI-kompatiblen Endpunkts, API-Schlüssels, Modellnamens und einer
Anweisung unter die Kontrolle eines MLLM gestellt werden. Der Schlüssel verbleibt in der
aktuellen Browsersitzung und wird von UrbanGround nicht aufgezeichnet.

Binärdateien der Desktopanwendung und Aufgaben im JSON-Format werden gemeinsam als Archive
über GitHub Releases bereitgestellt und nicht im Git-Repository gespeichert. Die
Desktoppakete verwenden optimierte Unity-IL2CPP-Builds ohne Entwicklungsfunktionen anstelle
von Mono-Builds. Die nachstehenden Downloadlinks werden verfügbar, sobald die entsprechenden
Release-Assets veröffentlicht sind.

| Plattform | Anwendung | Installation |
| --- | --- | --- |
| Web | [UrbanGround im Browser ausführen](https://urbanground.github.io/#play-online) | Keine Installation |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

Laden Sie das Archiv für Ihr Betriebssystem herunter und entpacken Sie es in das passende
lokale Zielverzeichnis. In jedem Paket liegen `sandbox.cfg` und das mitgelieferte
`task`-Verzeichnis neben der Anwendung:

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

Der Evaluator lädt Aufgaben ausschließlich aus dem Verzeichnis `<build-folder>/task` des
ausgewählten Pakets auf. Ein Aufgabenpfad auf Repository-Ebene wird nicht verwendet. Durch den
Wechsel des Anwendungspakets wird daher zugleich der mit dieser Softwareversion veröffentlichte
Aufgabensatz ausgewählt.

## Systemübersicht

UrbanGround ist eine urbane Sandbox im realen Maßstab, die aus flächendeckenden georäumlichen
3D-Daten erstellt wurde. Sie unterstützt sowohl die direkte Nutzung aus der
Ich-Perspektive als auch die programmatische Steuerung durch MLLM-Agenten über
dieselbe Schnittstelle. Wir veröffentlichen die Sandbox im Web und als native Builds für
macOS, Windows und Linux. Darüber hinaus umfasst sie vielfältige Aufgaben zur Untersuchung,
wie multimodale Agenten eine reale Stadt wahrnehmen und in ihr handeln.

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="Überblick über die UrbanGround-Umgebung und ihre Interaktionsmodi">
</p>

## Umgebung

UrbanGround ist in drei Ebenen gegliedert.

- **Geodatenebene.** Die Umgebung streamt die vom
  [Hong Kong Lands Department](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
  veröffentlichte 3D Visualisation Map als georeferenzierte Cesium 3D Tiles. Das
  [3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
  ist im selben WGS84-Bezugssystem ausgerichtet und wird als zusammenhängender Graph für die
  Routenanalyse vorgehalten.
- **Simulationsebene.** Die Unity-Szene bietet kontinuierliche Bewegung aus der
  Ich-Perspektive, Kollisionen mit Gebäuden und Gelände, eine steuerbare Uhr, Regen
  und Nebel sowie animierte Fußgänger, die sich auf dem georeferenzierten Fußgängernetz bewegen.
- **Agentenebene.** Eine lokale HTTP-Schnittstelle stellt RGB-Beobachtungen, physische
  Aktionen, Karteninteraktion, das Laden von Aufgaben und den Evaluatorzustand bereit. Die
  Agenten verbleiben im kontinuierlichen Raum; der Fußgängergraph dient der Analyse und stellt
  keine Bewegungseinschränkung dar.

*(Optional)* Der öffentliche Kacheldienst eignet sich gut für die interaktive Nutzung, doch das
flächendeckende Streaming kann langsam sein, wenn ein Experiment wiederholt den Standort
wechselt. Spiegeln Sie für wiederholte oder groß angelegte Durchläufe die drei offiziellen
3D-Tiles-Verzeichnisbäume auf einem lokalen HTTP-Server und behalten Sie dabei die folgende
Struktur bei:

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

Bearbeiten Sie die `sandbox.cfg` neben der Anwendung und setzen Sie `internal_base_url` auf
dieses HTTP-Stammverzeichnis:

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

Verwenden Sie anstelle der Beispiel-IP die Adresse des Rechners, der die Kacheln bereitstellt.
UrbanGround prüft den Spiegelserver beim Start und greift auf den Dienst des Hong Kong Lands Department
zurück, wenn er nicht verfügbar ist. Die aktive Quelle lässt sich über `GET /tileset_source`
abfragen. Werden die Kacheldaten im lokalen Netzwerk vorgehalten, verkürzt sich die Ladezeit bei
wiederholter Teleportation und umfangreichen Evaluationsdurchläufen erheblich.

## Steuerung und API

Manuelle Steuerung, Karteninteraktion, HTTP-Endpunkte, Aktionsschemata, das Laden von Aufgaben,
Screenshots und Python-Beispiele sind in
[`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md) dokumentiert. Die Desktopanwendung stellt
die API standardmäßig unter `http://127.0.0.1:8081` bereit.

## Experimentelle Daten und Evaluation

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="Fünfstufige Hierarchie der experimentellen Aufgaben">
</p>

Die Publikation verwendet eine fünfstufige Sammlung experimenteller Aufgaben, um das Verhalten
von Agenten in der Umgebung zu analysieren und zu validieren. Sie wird gemeinsam mit der
Anwendung als experimenteller Datensatz und nicht als separate Softwarekomponente
veröffentlicht.

| Stufe | Fähigkeit | Aufgabentypen |
| --- | --- | --- |
| 1 | Lokales Verständnis der Umgebung | Visual Recognition (VR), Orientation Understanding (OU), Active Exploration Questions (AEQ) |
| 2 | Navigation anhand expliziter Anweisungen | Short-range Goal Navigation (SGN), Long-range Goal Navigation (LGN), Instructional Navigation (IN), Constrained Navigation (CN) |
| 3 | Exploration anhand impliziter Anweisungen | Place-Type Search (PTS), Implicit Intent Inference (III) |
| 4 | Planung mehrerer Aufgaben | Time-Window Scheduling (TWS), Multi-Stop Route Planning (MSP) |
| 5 | Interaktion mit einer dynamischen Umgebung | Dynamic Road-Closure Replanning (DCR), Navigation among Pedestrians (NP) |

Das veröffentlichte Protokoll enthält 700 manuell verifizierte Basisinstanzen. Die
experimentellen Daten verteilen sich über verschiedene Stadtgebiete Hongkongs. Ihre
geografische Abdeckung sowie die Anzahl der Aufgabeninstanzen in jeder der fünf Stufen sind
nachstehend zusammengefasst.

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="Räumliche Verteilung der experimentellen Aufgaben in Hongkong"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="Anzahl der Aufgabeninstanzen in den fünf experimentellen Stufen"></td>
  </tr>
</table>

## Installation

Für den Evaluationscode ist Python 3.10 oder neuer erforderlich. Laden Sie vor der Ausführung
einer Episode das Anwendungspaket für das Betriebssystem des Hostrechners herunter.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Konfigurieren Sie einen OpenAI-kompatiblen Endpunkt für ein multimodales Modell. Wenn
`AGENT_API_BASE` nicht angegeben ist, wird standardmäßig die OpenAI API verwendet.

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

Das erstmalige Laden der Kacheln aus dem öffentlichen Dienst kann je nach ausgewähltem Gebiet
und Verbindung mehrere Minuten dauern. Für wiederholte Experimente wird der unter
[Umgebung](#umgebung) beschriebene lokale Spiegelserver empfohlen.

## Durchführung einer Evaluation

Führen Sie eine einzelne Aufgabe anhand ihrer ID aus:

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Der Evaluator wählt je nach Betriebssystem des Hostrechners automatisch `Builds/macOS`,
`Builds/Windows` oder `Builds/Linux` aus. Ein separat entpacktes Paket kann mit
`--build-folder` ausgewählt werden.

Wählen Sie eine Aufgabenfamilie mit einem Glob-Muster aus:

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Führen Sie das vollständige experimentelle Protokoll einschließlich der generierten
Bedingungsvarianten aus:

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround verwendet einen lokalen Aktionsserver auf Port `8081`; daher evaluiert das
veröffentlichte Ausführungsprogramm jeweils nur eine Anwendungsinstanz. Verwenden Sie
`--attach`, um eine bereits geöffnete Anwendung zu nutzen. Berichte erfolgreicher Läufe werden bei
späteren Durchläufen wiederverwendet; mit `--force-rerun` können sie ersetzt werden.

Evaluationsartefakte werden in folgendes Verzeichnis geschrieben:

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

Jedes Aufgabenverzeichnis enthält `report.json` oder `run_failure.json` und, sofern aktiviert,
ein Video der Episode sowie die Quellframes. Die Zusammenfassung des Batchlaufs wird in
`batch_report.json` geschrieben.

## Bewertung und Überprüfung

Fassen Sie die Ergebnisse eines Modells zusammen:

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

Vergleichen Sie die Verzeichnisse abgeschlossener Modellläufe:

```bash
python AgentEvaluation/compare_models.py
```

Durchsuchen Sie Trajektorien, Frames, Videos und Metriken auf Aufgabenebene mit der
schreibgeschützten Ergebnisansicht:

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

Öffnen Sie anschließend `http://localhost:8000`.

## Demnächst

- [ ] Interaktion mehrerer Agenten
- [ ] Reparatur unscharfer oder unvollständiger Szenengeometrie
- [ ] Eine größere Vielfalt an Fahrzeugen und Fußgängern
- [ ] Ausgewählte Innenräume

## Daten und Komponenten Dritter

UrbanGround verwendet die von der Regierung der Sonderverwaltungsregion Hongkong
veröffentlichte
[3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
und das
[3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network).
Diese Datensätze werden nicht über das Repository weiterverbreitet und unterliegen weiterhin ihren
ursprünglichen Bedingungen. Die Anwendungspakete enthalten außerdem Unity-Laufzeitkomponenten,
Cesium for Unity und Microsoft-Rocketbox-Avatare; für alle gelten weiterhin die jeweiligen
Lizenzen der Originalprojekte.

## Zitation

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

## Lizenz

[MIT](../../LICENSE).
