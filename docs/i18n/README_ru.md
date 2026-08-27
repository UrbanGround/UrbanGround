<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround: от локального восприятия к пространственной автономности в городе реального масштаба">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>Страница проекта</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#загрузка-приложения"><strong>Скачать приложение</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#цитирование"><strong>Статья и цитирование</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>Лицензия MIT</strong></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> &middot;
  <a href="README_zh.md">简体中文</a> &middot;
  <a href="README_fr.md">Français</a> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <a href="README_ar.md">العربية</a> &middot;
  <strong>Русский</strong>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="Демонстрация преодоления лестниц"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="Демонстрация исследования на уровне улиц"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="Демонстрация управления видом карты"></td>
  </tr>
  <tr>
    <td align="center"><strong>Преодоление лестниц</strong></td>
    <td align="center"><strong>Исследование на уровне улиц</strong></td>
    <td align="center"><strong>Управление видом карты</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="Демонстрация поиска мест"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="Демонстрация телепортации через карту"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="Демонстрация пешеходной навигации"></td>
  </tr>
  <tr>
    <td align="center"><strong>Поиск мест</strong></td>
    <td align="center"><strong>Телепортация через карту</strong></td>
    <td align="center"><strong>Пешеходная навигация</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="Демонстрация управления погодой"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="Демонстрация управления временем суток"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="Демонстрация интеграции агента"></td>
  </tr>
  <tr>
    <td align="center"><strong>Управление погодой</strong></td>
    <td align="center"><strong>Управление временем суток</strong></td>
    <td align="center"><strong>Интеграция агента</strong></td>
  </tr>
</table>

UrbanGround — это городская среда-песочница реального масштаба для оценки по замкнутому
циклу агентов на базе мультимодальных больших языковых моделей. Она преобразует
трёхмерные геопространственные данные всего Гонконга в непрерывно визуализируемую среду
Unity с физическим взаимодействием. Агент наблюдает за городом через камеру от первого
лица, действует посредством компактного интерфейса управления и оценивается на основе
пройденной им в среде траектории.

Сопутствующие экспериментальные задачи последовательно охватывают понимание локальной
сцены, навигацию по явным указаниям, неявный вывод о пункте назначения, планирование
маршрута с несколькими остановками и перепланирование после изменений среды. Каждая
исходная задача была вручную выполнена и проверена в опубликованном приложении.

## Загрузка приложения

На [странице проекта](https://urbanground.github.io/#play-online) доступна браузерная версия,
которую можно использовать напрямую. Город можно исследовать от первого лица с помощью
клавиатуры и мыши либо передать под управление MLLM, указав OpenAI-совместимую конечную
точку, ключ API, имя модели и инструкцию. Ключ остаётся в текущем сеансе браузера и не
записывается UrbanGround.

Исполняемые файлы настольного приложения и JSON-файлы задач распространяются вместе в
архивах GitHub Release и не хранятся в репозитории Git. В пакетах для настольных систем
используются оптимизированные сборки Unity IL2CPP, не предназначенные для разработки, а не
сборки Mono. Приведённые ниже ссылки становятся доступными после публикации ресурсов
соответствующего выпуска.

| Платформа | Приложение | Установка |
| --- | --- | --- |
| Веб | [Запустить UrbanGround в браузере](https://urbanground.github.io/#play-online) | Установка не требуется |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

Скачайте архив для своей операционной системы и распакуйте его в соответствующий локальный
каталог. В каждом пакете файл `sandbox.cfg` и опубликованный каталог `task` располагаются
рядом с приложением:

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

Оценщик загружает задачи только из каталога `<build-folder>/task` выбранного пакета. Путь
к задачам на уровне репозитория не используется. Поэтому при смене пакета приложения также
выбирается набор задач, опубликованный с этой версией программного обеспечения.

## Обзор системы

UrbanGround — это городская среда-песочница реального масштаба, построенная на основе
трёхмерных геопространственных данных, охватывающих всю территорию. Она поддерживает как
непосредственную игру от первого лица, так и программное управление агентами MLLM через
один и тот же интерфейс. Мы публикуем эту среду в веб-версии и в виде нативных сборок для
macOS, Windows и Linux. В неё также входят разнообразные задачи для изучения того, как
мультимодальные агенты воспринимают реальный город и действуют в нём.

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="Обзор среды UrbanGround и режимов взаимодействия">
</p>

## Среда

UrbanGround состоит из трёх слоёв.

- **Геопространственный слой.** Среда выполняет потоковую загрузку 3D Visualisation Map,
  опубликованной
  [Департаментом земельных ресурсов Гонконга](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models),
  в виде геопривязанных Cesium 3D Tiles. Набор
  [3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
  совмещён в той же системе координат WGS84 и сохранён в виде связного графа для анализа
  маршрутов.
- **Слой симуляции.** Сцена Unity обеспечивает непрерывное движение от первого лица,
  столкновения со зданиями и рельефом, управляемое время, дождь и туман, а также
  анимированных пешеходов, перемещающихся по геопривязанной пешеходной сети.
- **Слой агента.** Локальный интерфейс HTTP предоставляет RGB-наблюдения, физические
  действия, взаимодействие с картой, загрузку задач и состояние оценщика. Агенты остаются
  в непрерывном пространстве; пешеходный граф используется для анализа, а не в качестве
  ограничения движения.

*(Необязательно)* Публичный сервис тайлов удобен для интерактивной работы, однако потоковая
загрузка данных всей территории может быть медленной, если эксперимент часто меняет
местоположение. Для повторных или крупномасштабных запусков создайте зеркало трёх
официальных деревьев 3D Tiles на локальном HTTP-сервере, сохранив следующую структуру:

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

Измените файл `sandbox.cfg` рядом с приложением и направьте `internal_base_url` на этот
корневой HTTP-адрес:

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

Вместо IP-адреса из примера укажите адрес компьютера, который раздаёт тайлы. При запуске
UrbanGround проверяет зеркало и при его недоступности переключается на сервис Lands
Department. Активный источник можно проверить с помощью `GET /tileset_source`. Хранение
данных тайлов в локальной сети значительно сокращает время загрузки при многократной
телепортации и крупных сериях оценочных запусков.

## Управление и API

Ручное управление, взаимодействие с картой, конечные точки HTTP, схемы действий, загрузка
задач, снимки экрана и примеры на Python описаны в
[`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md). По умолчанию настольное приложение
предоставляет API по адресу `http://127.0.0.1:8081`.

## Экспериментальные данные и оценка

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="Пятиуровневая иерархия экспериментальных задач">
</p>

В статье используется пятиуровневый набор экспериментальных задач для анализа и проверки
поведения агентов в среде. Он публикуется вместе с приложением как экспериментальные
данные, а не как отдельный программный компонент.

| Уровень | Способность | Типы задач |
| --- | --- | --- |
| 1 | Понимание локальной среды | Визуальное распознавание (Visual Recognition, VR), понимание ориентации (Orientation Understanding, OU), вопросы активного исследования (Active Exploration Questions, AEQ) |
| 2 | Навигация по явным инструкциям | Навигация к близкой цели (Short-range Goal Navigation, SGN), навигация к удалённой цели (Long-range Goal Navigation, LGN), навигация по инструкциям (Instructional Navigation, IN), навигация с ограничениями (Constrained Navigation, CN) |
| 3 | Исследование по неявным инструкциям | Поиск по типу места (Place-Type Search, PTS), вывод неявного намерения (Implicit Intent Inference, III) |
| 4 | Многозадачное планирование | Составление расписания с временными окнами (Time-Window Scheduling, TWS), планирование маршрута с несколькими остановками (Multi-Stop Route Planning, MSP) |
| 5 | Взаимодействие с динамической средой | Перепланирование при динамическом перекрытии дороги (Dynamic Road-Closure Replanning, DCR), навигация среди пешеходов (Navigation among Pedestrians, NP) |

Опубликованный протокол содержит 700 вручную проверенных базовых экземпляров. Экспериментальные
данные распределены по различным городским районам Гонконга. Ниже приведены их географический
охват и число экземпляров задач на каждом из пяти этапов.

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="Пространственное распределение экспериментальных задач по Гонконгу"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="Число экземпляров задач на пяти экспериментальных этапах"></td>
  </tr>
</table>

## Установка

Для кода оценки требуется Python 3.10 или более новая версия. Перед запуском эпизода
скачайте пакет приложения для операционной системы хоста.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Настройте конечную точку OpenAI-совместимой мультимодальной модели. Если
`AGENT_API_BASE` не задана, по умолчанию используется API OpenAI.

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

Первичная загрузка тайлов из публичного сервиса может занять несколько минут в зависимости
от выбранного района и соединения. Для повторяющихся экспериментов рекомендуется локальное
зеркало, описанное в разделе [Среда](#среда).

## Запуск оценки

Запустите одну задачу по идентификатору:

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Оценщик автоматически выбирает `Builds/macOS`, `Builds/Windows` или `Builds/Linux` в
зависимости от операционной системы хоста. Отдельно распакованный пакет можно выбрать
параметром `--build-folder`.

Выберите семейство задач с помощью glob-шаблона:

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

Запустите полный экспериментальный протокол, включая сгенерированные варианты условий:

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

UrbanGround использует локальный сервер действий на порту `8081`, поэтому поставляемый
скрипт запуска одновременно оценивает только один экземпляр приложения. Добавьте
`--attach`, чтобы использовать уже открытое приложение. Отчёты об успешных запусках
повторно используются при последующих запусках; добавьте `--force-rerun`, чтобы заменить их.

Артефакты оценки записываются в:

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

Каждый каталог задачи содержит `report.json` или `run_failure.json`, а при включённой
соответствующей функции — видео эпизода и исходные кадры. Сводный отчёт пакетного запуска
записывается в `batch_report.json`.

## Подсчёт результатов и анализ

Сформируйте сводку по одной модели:

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

Сравните каталоги моделей с завершёнными запусками:

```bash
python AgentEvaluation/compare_models.py
```

Просмотрите траектории, кадры, видео и метрики отдельных задач в средстве просмотра
результатов, работающем только для чтения:

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

Затем откройте `http://localhost:8000`.

## Скоро

- [ ] Взаимодействие нескольких агентов
- [ ] Исправление размытой или неполной геометрии сцен
- [ ] Более широкий выбор транспортных средств и пешеходов
- [ ] Отдельные внутренние пространства

## Данные и сторонние компоненты

UrbanGround использует
[3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
и
[3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network),
опубликованные правительством Специального административного района Гонконг. Эти наборы
данных не распространяются через репозиторий и по-прежнему подпадают под действие исходных
условий. В пакеты приложения также входят компоненты среды выполнения Unity, Cesium for
Unity и аватары Microsoft Rocketbox; каждый из них остаётся под лицензией исходного проекта.

## Цитирование

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

## Лицензия

[MIT](../../LICENSE).
