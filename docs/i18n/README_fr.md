<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround : de la perception locale à l’autonomie spatiale dans une ville à l’échelle réelle">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>Page du projet</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#téléchargements-de-lapplication"><strong>Télécharger l’application</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>Licence MIT</strong></a>
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
  <a href="README_zh.md">简体中文</a> &middot;
  <strong>Français</strong> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <a href="README_de.md">Deutsch</a> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="Démonstration du franchissement d’escaliers"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="Démonstration de l’exploration au niveau de la rue"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="Démonstration du contrôle de la vue cartographique"></td>
  </tr>
  <tr>
    <td align="center"><strong>Franchissement d’escaliers</strong></td>
    <td align="center"><strong>Exploration au niveau de la rue</strong></td>
    <td align="center"><strong>Contrôle de la vue cartographique</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="Démonstration de la recherche de lieux"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="Démonstration de la téléportation via la carte"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="Démonstration de la navigation piétonne"></td>
  </tr>
  <tr>
    <td align="center"><strong>Recherche de lieux</strong></td>
    <td align="center"><strong>Téléportation via la carte</strong></td>
    <td align="center"><strong>Navigation piétonne</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="Démonstration du contrôle de la météo"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="Démonstration du contrôle de l’heure de la journée"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="Démonstration de l’intégration d’agents"></td>
  </tr>
  <tr>
    <td align="center"><strong>Contrôle de la météo</strong></td>
    <td align="center"><strong>Contrôle de l’heure de la journée</strong></td>
    <td align="center"><strong>Intégration d’agents</strong></td>
  </tr>
</table>

UrbanGround est un bac à sable urbain à l’échelle réelle destiné à l’évaluation en boucle fermée
d’agents fondés sur de grands modèles de langage multimodaux. Il transforme les données
géospatiales 3D couvrant l’ensemble du territoire de Hong Kong en un environnement Unity au
rendu continu et doté d’interactions physiques. Un agent observe la ville au moyen d’une caméra
à la première personne, agit par l’intermédiaire d’une interface de contrôle compacte et est
évalué à partir de la trajectoire qu’il exécute dans l’environnement.

Les tâches expérimentales associées progressent de la compréhension de scènes locales à la
navigation explicite, à l’inférence implicite de la destination, à la planification d’itinéraires
à plusieurs arrêts et à la replanification après une modification de l’environnement. Chaque
tâche source a été exécutée manuellement et vérifiée dans l’application publiée.

## Téléchargements de l’application

La [page du projet](https://urbanground.github.io/#play-online) propose une édition pour navigateur
utilisable directement. Elle peut être explorée à la première personne avec un clavier et une
souris, ou placée sous le contrôle d’un MLLM en indiquant un point de terminaison compatible avec
OpenAI, une clé API, un nom de modèle et une instruction. La clé reste dans la session actuelle du
navigateur et n’est pas enregistrée par UrbanGround.

Les exécutables de l’application de bureau et les fichiers JSON des tâches sont distribués
ensemble sous forme d’archives GitHub Release ; ils ne sont pas stockés dans le dépôt Git. Les
paquets pour ordinateur utilisent des builds Unity IL2CPP optimisés et non destinés au
développement, plutôt que des builds Mono. Les liens de téléchargement ci-dessous deviennent
disponibles lorsque les ressources de la version correspondante sont publiées.

| Plateforme | Application | Installation |
| --- | --- | --- |
| Web | [Utiliser UrbanGround dans le navigateur](https://urbanground.github.io/#play-online) | Aucune installation |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

Téléchargez l’archive correspondant à votre système d’exploitation et extrayez-la dans la
destination locale correspondante. Chaque paquet conserve `sandbox.cfg` et le répertoire
`task` publié à côté de l’application :

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

L’évaluateur ne recherche les tâches que dans le répertoire `<build-folder>/task` du paquet
sélectionné. Il n’utilise aucun chemin de tâches à la racine du dépôt. Changer de paquet
d’application sélectionne donc également l’ensemble de tâches publié avec cette version du
logiciel.

## Vue d’ensemble du système

UrbanGround est un bac à sable urbain à l’échelle réelle construit à partir de données
géospatiales 3D couvrant l’ensemble du territoire. Il permet aussi bien une utilisation directe à la
première personne qu’un contrôle programmatique par des agents MLLM au moyen de la même
interface. Nous publions le bac à sable sur le Web ainsi que sous forme de builds natifs pour
macOS, Windows et Linux. Il comprend également diverses tâches permettant d’étudier la manière
dont les agents multimodaux perçoivent une ville réelle et y agissent.

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="Vue d’ensemble de l’environnement UrbanGround et de ses modes d’interaction">
</p>

## Environnement

UrbanGround est organisé en trois couches.

- **Couche géospatiale.** L’environnement diffuse en continu la 3D Visualisation Map publiée par le
  [Hong Kong Lands Department](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
  sous forme de Cesium 3D Tiles géoréférencées. Le
  [3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
  est aligné dans le même référentiel WGS84 et conservé sous forme de graphe connexe pour
  l’analyse des itinéraires.
- **Couche de simulation.** La scène Unity fournit un déplacement continu à la première personne,
  des collisions avec les bâtiments et le terrain, une horloge réglable, de la pluie et du
  brouillard, ainsi que des piétons animés qui se déplacent sur le réseau piétonnier géoréférencé.
- **Couche des agents.** Une interface HTTP locale donne accès aux observations RGB, aux actions
  physiques, à l’interaction avec la carte, au chargement des tâches et à l’état de l’évaluateur.
  Les agents restent dans un espace continu ; le graphe piétonnier sert à l’analyse et ne
  constitue pas une contrainte de déplacement.

*(Facultatif)* Le service public de tuiles est pratique pour une utilisation interactive, mais la
diffusion à l’échelle de tout le territoire peut être lente lorsqu’une expérience change souvent
d’emplacement. Pour les exécutions répétées ou à grande échelle, créez un miroir des trois
arborescences 3D Tiles officielles sur un serveur HTTP local en conservant la structure suivante :

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

Modifiez le fichier `sandbox.cfg` situé à côté de l’application et faites pointer
`internal_base_url` vers cette racine HTTP :

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

Remplacez l’adresse IP d’exemple par celle de la machine qui sert les tuiles. Au démarrage,
UrbanGround sonde le miroir et se rabat sur le service du Lands Department si celui-ci est
indisponible. La source active peut être vérifiée au moyen de `GET /tileset_source`. Le maintien
des données de tuiles sur le réseau local réduit considérablement le temps de chargement lors des
téléportations répétées et des campagnes d’évaluation de grande ampleur.

## Commandes et API

Les commandes manuelles, l’interaction avec la carte, les points de terminaison HTTP, les schémas
d’action, le chargement des tâches, les captures d’écran et les exemples Python sont décrits dans
[`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md). Par défaut, l’application de bureau expose
l’API à l’adresse `http://127.0.0.1:8081`.

## Données expérimentales et évaluation

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="Hiérarchie à cinq niveaux des tâches expérimentales">
</p>

L’article utilise un ensemble de tâches expérimentales à cinq niveaux pour analyser et valider
le comportement des agents dans l’environnement. Cet ensemble est publié comme données
expérimentales avec l’application, et non comme composant logiciel distinct.

| Niveau | Capacité | Types de tâches |
| --- | --- | --- |
| 1 | Compréhension de l’environnement local | Reconnaissance visuelle (Visual Recognition, VR), compréhension de l’orientation (Orientation Understanding, OU), questions d’exploration active (Active Exploration Questions, AEQ) |
| 2 | Navigation selon des instructions explicites | Navigation vers un objectif à courte portée (Short-range Goal Navigation, SGN), navigation vers un objectif à longue portée (Long-range Goal Navigation, LGN), navigation guidée par des instructions (Instructional Navigation, IN), navigation sous contraintes (Constrained Navigation, CN) |
| 3 | Exploration selon des instructions implicites | Recherche par type de lieu (Place-Type Search, PTS), inférence d’intention implicite (Implicit Intent Inference, III) |
| 4 | Planification multitâche | Ordonnancement avec fenêtres temporelles (Time-Window Scheduling, TWS), planification d’itinéraire à plusieurs arrêts (Multi-Stop Route Planning, MSP) |
| 5 | Interaction avec un environnement dynamique | Replanification dynamique en cas de fermeture de route (Dynamic Road-Closure Replanning, DCR), navigation parmi les piétons (Navigation among Pedestrians, NP) |

Le protocole publié contient 700 instances de base vérifiées manuellement. Les données
expérimentales couvrent diverses zones urbaines de Hong Kong. Leur couverture géographique et le
nombre d’instances de tâches à chacune des cinq étapes sont résumés ci-dessous.

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="Répartition spatiale des tâches expérimentales à Hong Kong"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="Nombre d’instances de tâches dans les cinq étapes expérimentales"></td>
  </tr>
</table>

## Installation

Le code d’évaluation nécessite Python 3.10 ou une version ultérieure. Téléchargez le paquet
d’application correspondant au système d’exploitation hôte avant d’exécuter un épisode.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Configurez un point de terminaison compatible avec OpenAI pour un modèle multimodal.
Lorsque `AGENT_API_BASE` est omis, l’API OpenAI est utilisée par défaut.

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

Le chargement initial des tuiles depuis le service public peut prendre plusieurs minutes, selon
la zone sélectionnée et la connexion. Le miroir local décrit dans la section
[Environnement](#environnement) est recommandé pour les expériences répétées.

## Exécuter une évaluation

Exécutez une tâche à partir de son identifiant :

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

L’évaluateur sélectionne automatiquement `Builds/macOS`, `Builds/Windows` ou `Builds/Linux`
en fonction du système d’exploitation hôte. Un paquet extrait séparément peut être sélectionné
avec `--build-folder`.

Sélectionnez une famille de tâches à l’aide d’un motif glob :

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Exécutez l’intégralité du protocole expérimental, y compris les variantes de conditions générées :

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround utilise un serveur d’actions local sur le port `8081` ; le programme d’exécution
publié évalue donc une seule instance de l’application à la fois. Ajoutez `--attach` pour
utiliser une application déjà ouverte. Les rapports d’exécution réussie sont réutilisés lors des
exécutions suivantes ; ajoutez `--force-rerun` pour les remplacer.

Les artefacts d’évaluation sont enregistrés dans :

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

Chaque répertoire de tâche contient `report.json` ou `run_failure.json` et, lorsque cette
option est activée, une vidéo de l’épisode ainsi que les images sources. Le résumé du lot est
enregistré dans `batch_report.json`.

## Calcul des scores et inspection

Résumez les résultats d’un modèle :

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

Comparez les répertoires de modèles dont l’évaluation est terminée :

```bash
python AgentEvaluation/compare_models.py
```

Parcourez les trajectoires, les images, les vidéos et les métriques par tâche au moyen de la
visionneuse de résultats en lecture seule :

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

Ouvrez ensuite `http://localhost:8000`.

## Prochainement

- [ ] Interaction entre plusieurs agents
- [ ] Réparation de la géométrie floue ou incomplète des scènes
- [ ] Une plus grande diversité de véhicules et de piétons
- [ ] Une sélection d’environnements intérieurs

## Données et composants tiers

UrbanGround utilise la
[3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
et le
[3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
publiés par le gouvernement de la Région administrative spéciale de Hong Kong. Ces jeux de
données ne sont pas redistribués dans le dépôt et restent soumis à leurs conditions d’origine.
Les paquets de l’application comprennent également des composants d’exécution Unity, Cesium for
Unity et des avatars Microsoft Rocketbox ; chacun reste soumis à sa licence amont.

## Citation

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

## Licence

[MIT](../../LICENSE).
