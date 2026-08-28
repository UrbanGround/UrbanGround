<p align="center">
  <img src="../assets/urbanground-header.png" width="940" alt="UrbanGround: من الإدراك المحلي إلى الفاعلية المكانية في مدينة بمقياس حقيقي">
</p>

<p align="center">
  <a href="https://urbanground.github.io"><strong>صفحة المشروع</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="#تنزيلات-التطبيق"><strong>تنزيل التطبيق</strong></a>
  &nbsp;&nbsp;&middot;&nbsp;&nbsp;
  <a href="../../LICENSE"><strong>ترخيص MIT</strong></a>
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
  <a href="README_fr.md">Français</a> &middot;
  <a href="README_zh-Hant.md">繁體中文</a> &middot;
  <a href="README_ja.md">日本語</a> &middot;
  <a href="README_ko.md">한국어</a> &middot;
  <strong>العربية</strong> &middot;
  <a href="README_de.md">Deutsch</a> &middot;
  <a href="README_ru.md">Русский</a>
</p>

<table>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/stair-traversal.webp" width="100%" alt="عرض توضيحي لاجتياز السلالم"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/street-exploration.webp" width="100%" alt="عرض توضيحي للاستكشاف على مستوى الشارع"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-view-control.webp" width="100%" alt="عرض توضيحي للتحكم في عرض الخريطة"></td>
  </tr>
  <tr>
    <td align="center"><strong>اجتياز السلالم</strong></td>
    <td align="center"><strong>الاستكشاف على مستوى الشارع</strong></td>
    <td align="center"><strong>التحكم في عرض الخريطة</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/place-search.webp" width="100%" alt="عرض توضيحي للبحث عن الأماكن"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/map-teleportation.webp" width="100%" alt="عرض توضيحي للانتقال الآني عبر الخريطة"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/pedestrian-navigation.webp" width="100%" alt="عرض توضيحي لملاحة المشاة"></td>
  </tr>
  <tr>
    <td align="center"><strong>البحث عن الأماكن</strong></td>
    <td align="center"><strong>الانتقال الآني عبر الخريطة</strong></td>
    <td align="center"><strong>ملاحة المشاة</strong></td>
  </tr>
  <tr>
    <td width="33.33%" align="center"><img src="../assets/demos/weather-control.webp" width="100%" alt="عرض توضيحي للتحكم في الطقس"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/time-of-day-control.webp" width="100%" alt="عرض توضيحي للتحكم في وقت اليوم"></td>
    <td width="33.33%" align="center"><img src="../assets/demos/agent-integration.webp" width="100%" alt="عرض توضيحي لتكامل الوكيل"></td>
  </tr>
  <tr>
    <td align="center"><strong>التحكم في الطقس</strong></td>
    <td align="center"><strong>التحكم في وقت اليوم</strong></td>
    <td align="center"><strong>تكامل الوكيل</strong></td>
  </tr>
</table>

UrbanGround بيئة محاكاة حضرية بمقياس حقيقي لتقييم الحلقة المغلقة لوكلاء نماذج
اللغة الكبيرة متعددة الوسائط. وهي تحوّل البيانات الجغرافية المكانية ثلاثية الأبعاد
التي تغطي كامل إقليم هونغ كونغ إلى بيئة Unity ذات تصيير مستمر وتفاعل فيزيائي. يرصد
الوكيل المدينة عبر كاميرا بمنظور الشخص الأول، ويتصرف من خلال واجهة تحكم موجزة،
ويُقيَّم استنادًا إلى المسار الذي ينفذه داخل البيئة.

تتدرج المهام التجريبية المصاحبة من فهم المشهد المحلي إلى الملاحة الصريحة، واستنتاج
الوجهة الضمني، والتخطيط متعدد المحطات، وإعادة التخطيط بعد تغيّر البيئة. وقد نُفِّذت
كل مهمة أصلية يدويًا وفُحصت في التطبيق المنشور.

## تنزيلات التطبيق

تتضمن [صفحة المشروع](https://urbanground.github.io/#play-online) إصدارًا يعمل في
المتصفح للاستخدام المباشر. ويمكن استكشافه بمنظور الشخص الأول باستخدام لوحة المفاتيح
والفأرة، أو وضعه تحت تحكم نموذج لغة كبير متعدد الوسائط (MLLM) عبر تزويده بنقطة نهاية
متوافقة مع OpenAI ومفتاح API واسم النموذج وتعليمة. يبقى المفتاح في جلسة المتصفح
الحالية ولا يسجله UrbanGround.

تُوزَّع الملفات التنفيذية لتطبيق سطح المكتب وملفات مهام JSON معًا في أرشيفات
GitHub Release، ولا تُخزَّن في مستودع Git. تستخدم حزم سطح المكتب إصدارات Unity
محسّنة وغير مخصصة للتطوير مبنية باستخدام IL2CPP بدلًا من Mono. تصبح روابط التنزيل
أدناه متاحة عند نشر أصول الإصدار المقابلة.

| المنصة | التطبيق | التثبيت |
| --- | --- | --- |
| الويب | [تشغيل UrbanGround في المتصفح](https://urbanground.github.io/#play-online) | لا يتطلب تثبيتًا |
| macOS | [UrbanGround-macOS.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-macOS.zip) | [`Builds/macOS`](../../Builds/macOS/README.md) |
| Windows | [UrbanGround-Windows.zip](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Windows.zip) | [`Builds/Windows`](../../Builds/Windows/README.md) |
| Linux | [UrbanGround-Linux.tar.gz](https://github.com/UrbanGround/UrbanGround/releases/download/v1.0.0/UrbanGround-Linux.tar.gz) | [`Builds/Linux`](../../Builds/Linux/README.md) |

نزّل الأرشيف الخاص بنظام تشغيلك واستخرجه إلى الوجهة المحلية المطابقة. تُبقي كل حزمة
الملف `sandbox.cfg` ودليل `task` المنشور بجانب التطبيق:

```text
Builds/<platform>/
├── <UrbanGround application>
├── sandbox.cfg
└── task/
    └── <task-id>.json
```

لا يحمّل المُقيِّم المهام إلا من دليل `<build-folder>/task` الخاص بالحزمة المحددة،
ولا يستخدم مسار مهام على مستوى المستودع. ولذلك يؤدي تبديل حزمة التطبيق أيضًا إلى
اختيار مجموعة المهام المنشورة مع ذلك الإصدار من البرنامج.

## نظرة عامة على النظام

UrbanGround بيئة محاكاة حضرية بمقياس حقيقي مبنية من بيانات جغرافية مكانية ثلاثية
الأبعاد تغطي كامل الإقليم. وهي تدعم اللعب المباشر بمنظور الشخص الأول والتحكم البرمجي
بواسطة وكلاء MLLM عبر الواجهة نفسها. ننشر البيئة على الويب وفي صورة إصدارات أصلية
لأنظمة macOS وWindows وLinux. كما تتضمن مهام متنوعة لدراسة كيفية إدراك الوكلاء
متعددي الوسائط لمدينة حقيقية وتصرفهم داخلها.

<p align="center">
  <img src="../assets/urbanground-overview.jpg" width="100%" alt="نظرة عامة على بيئة UrbanGround وأنماط التفاعل">
</p>

## البيئة

يتكون UrbanGround من ثلاث طبقات.

- **الطبقة الجغرافية المكانية.** تبث البيئة خريطة التصور ثلاثية الأبعاد
  ([3D Visualisation Map](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models))
  التي نشرتها دائرة الأراضي في هونغ كونغ في صورة Cesium 3D Tiles مسجلة جغرافيًا.
  وتُحاذى شبكة المشاة ثلاثية الأبعاد
  ([3D Pedestrian Network](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network))
  ضمن إطار WGS84 نفسه، ويُحتفظ بها كرسم بياني متصل لتحليل المسارات.
- **طبقة المحاكاة.** يتيح مشهد Unity حركة مستمرة بمنظور الشخص الأول، والاصطدام
  بالمباني والتضاريس، وساعة قابلة للتحكم، والمطر والضباب، وشخصيات مشاة متحركة
  تسير على شبكة المشاة المسجلة جغرافيًا.
- **طبقة الوكيل.** تعرض واجهة HTTP محلية مشاهدات RGB، وأفعالًا فيزيائية، والتفاعل
  مع الخريطة، وتحميل المهام، وحالة المُقيِّم. يبقى الوكلاء في فضاء مستمر؛ ويُستخدم
  الرسم البياني لشبكة المشاة للتحليل لا باعتباره قيدًا على الحركة.

*(اختياري)* تُعدّ خدمة البلاطات العامة ملائمة للاستخدام التفاعلي، لكن بث كامل الإقليم
قد يكون بطيئًا عندما تغيّر التجربة الموقع مرارًا. للتشغيل المتكرر أو واسع النطاق،
أنشئ مرآة للأشجار الرسمية الثلاثة لـ 3D Tiles على خادم HTTP محلي مع الحفاظ على
البنية الآتية:

```text
http://<host>:<port>/3d-tiles/
├── f2/tileset.json
├── building/tileset.json
└── infrastructure/tileset.json
```

عدّل `sandbox.cfg` الموجود بجانب التطبيق، واضبط `internal_base_url` ليشير إلى جذر
HTTP ذلك:

```ini
[tileset]
internal_base_url = http://192.168.1.20:8899/3d-tiles
probe_timeout_seconds = 2
```

استخدم عنوان الجهاز الذي يستضيف البلاطات بدلًا من عنوان IP في المثال. يفحص UrbanGround
المرآة عند بدء التشغيل، ويعود إلى خدمة دائرة الأراضي إذا لم تكن متاحة. ويمكن التحقق
من المصدر النشط عبر `GET /tileset_source`. يؤدي إبقاء بيانات البلاطات على الشبكة
المحلية إلى تقليل زمن التحميل بدرجة كبيرة أثناء الانتقال الآني المتكرر وعمليات
التقييم الواسعة.

## عناصر التحكم وواجهة API

وُثّقت عناصر التحكم اليدوية، والتفاعل مع الخريطة، ونقاط نهاية HTTP، ومخططات الأفعال،
وتحميل المهام، ولقطات الشاشة، وأمثلة Python في
[`docs/CONTROLS_AND_API.md`](../CONTROLS_AND_API.md). يقدّم تطبيق سطح المكتب واجهة
API افتراضيًا على `http://127.0.0.1:8081`.

## البيانات التجريبية والتقييم

<p align="center">
  <img src="../assets/experimental-task-hierarchy.jpg" width="100%" alt="تسلسل هرمي للمهام التجريبية من خمسة مستويات">
</p>

تستخدم الورقة البحثية مجموعة من المهام التجريبية ذات خمسة مستويات لتحليل سلوك الوكيل في
البيئة والتحقق منه. وتُنشر هذه المجموعة بوصفها بيانات تجريبية مع التطبيق، لا مكوّنًا
برمجيًا منفصلًا.

| المستوى | القدرة | أنواع المهام |
| --- | --- | --- |
| 1 | فهم البيئة المحلية | التعرف البصري (VR)، فهم الاتجاه (OU)، أسئلة الاستكشاف النشط (AEQ) |
| 2 | الملاحة وفق تعليمات صريحة | ملاحة هدف قصيرة المدى (SGN)، ملاحة هدف بعيدة المدى (LGN)، الملاحة الإرشادية (IN)، الملاحة المقيّدة (CN) |
| 3 | الاستكشاف وفق تعليمات ضمنية | البحث عن نوع مكان (PTS)، استنتاج النية الضمنية (III) |
| 4 | التخطيط متعدد المهام | جدولة النوافذ الزمنية (TWS)، تخطيط مسار متعدد المحطات (MSP) |
| 5 | التفاعل مع بيئة ديناميكية | إعادة التخطيط الديناميكية عند إغلاق الطرق (DCR)، الملاحة بين المشاة (NP) |

يحتوي البروتوكول المنشور على 700 مثيل أساسي جرى التحقق منها يدويًا. وتتوزع البيانات
التجريبية على مناطق حضرية متنوعة في هونغ كونغ. ويلخَّص أدناه نطاق تغطيتها الجغرافية
وعدد مثيلات المهام في كل مرحلة من المراحل الخمس.

<table>
  <tr>
    <td width="68%" align="center"><img src="../assets/figure-7-task-distribution.png" height="320" alt="التوزيع المكاني للمهام التجريبية في هونغ كونغ"></td>
    <td width="32%" align="center"><img src="../assets/figure-8-task-composition.png" height="320" alt="عدد مثيلات المهام عبر المراحل التجريبية الخمس"></td>
  </tr>
</table>

## التثبيت

يتطلب كود التقييم Python 3.10 أو أحدث. نزّل حزمة التطبيق الخاصة بنظام التشغيل
المضيف قبل تشغيل حلقة تقييم.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

هيّئ نقطة نهاية لنموذج متعدد الوسائط متوافقة مع OpenAI. تستخدم `AGENT_API_BASE`
واجهة OpenAI API افتراضيًا عند إغفالها.

```bash
export AGENT_API_KEY="..."
export AGENT_MODEL="gpt-4.1"
# export AGENT_API_BASE="https://api.openai.com/v1"
```

قد يستغرق التحميل الأولي للبلاطات من الخدمة العامة عدة دقائق، وفقًا للمنطقة
المحددة والاتصال. يُوصى باستخدام المرآة المحلية الموضحة في قسم
[البيئة](#البيئة) للتجارب المتكررة.

## إجراء تقييم

شغّل مهمة واحدة بواسطة معرّفها:

```bash
python AgentEvaluation/run_task.py LQ-20260713-151300 \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

يختار المُقيِّم تلقائيًا `Builds/macOS` أو `Builds/Windows` أو `Builds/Linux` وفقًا
لنظام التشغيل المضيف. ويمكن اختيار حزمة مستخرجة بصورة منفصلة باستخدام
`--build-folder`.

اختر فئة مهام باستخدام نمط glob:

```bash
python AgentEvaluation/run_task.py --task-glob 'SN-*.json' \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

شغّل البروتوكول التجريبي الكامل، بما في ذلك متغيرات الشروط المولّدة:

```bash
python AgentEvaluation/run_task.py --all \
  --model "$AGENT_MODEL" \
  --max-steps 100
```

يستخدم UrbanGround خادم إجراءات محليًا على المنفذ `8081`، ولذلك يقيّم المشغّل
المنشور مثيل تطبيق واحدًا في كل مرة. أضف `--attach` لاستخدام تطبيق مفتوح بالفعل.
يُعاد استخدام التقارير الناجحة في عمليات التشغيل اللاحقة؛ أضف `--force-rerun`
لاستبدالها.

تُكتب نواتج التقييم في:

```text
AgentEvaluation/output/tasks/<model>/<task-id>/
```

يحتوي دليل كل مهمة على `report.json` أو `run_failure.json`، ويحتوي أيضًا، عند
تمكين ذلك، على فيديو لحلقة التقييم والإطارات الأصلية. ويُكتب ملخص الدفعة في
`batch_report.json`.

## احتساب الدرجات والفحص

لخّص نتائج نموذج واحد:

```bash
python AgentEvaluation/score_model.py --model "$AGENT_MODEL"
```

قارن مجلدات النماذج المكتملة:

```bash
python AgentEvaluation/compare_models.py
```

تصفح المسارات والإطارات ومقاطع الفيديو والمقاييس على مستوى المهمة من خلال عارض
النتائج المخصص للقراءة فقط:

```bash
python AgentEvaluation/visualization_site/server.py --port 8000
```

ثم افتح `http://localhost:8000`.

## قريبًا

- [ ] التفاعل متعدد الوكلاء
- [ ] إصلاح هندسة المشهد المشوّشة أو غير المكتملة
- [ ] نطاق أوسع من المركبات والمشاة
- [ ] بيئات داخلية مختارة

## البيانات والمكونات التابعة لجهات خارجية

يستخدم UrbanGround
[خريطة التصور ثلاثية الأبعاد](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-visualisation-map-tile-based-models)
و[شبكة المشاة ثلاثية الأبعاد](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-3d-pedestrian-network)
اللتين نشرتهما حكومة منطقة هونغ كونغ الإدارية الخاصة. لا يُعاد توزيع مجموعتي
البيانات هاتين في المستودع، وتظلان خاضعتين لشروطهما الأصلية. كما تتضمن حزم التطبيق
مكونات وقت تشغيل Unity وCesium for Unity وشخصيات Microsoft Rocketbox؛ ويظل كل
منها خاضعًا لترخيص المنبع الخاص به.

## الاستشهاد

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

## الترخيص

[MIT](../../LICENSE).
