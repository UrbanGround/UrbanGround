"use strict";

/* MetroBench Visualization Console -- vanilla-JS single-page app.
 * Three views, driven by location.hash:
 *   #/                                -> model list
 *   #/models/<model>                  -> model summary + task-type groups (each with its own
 *                                        curated metrics table -- there is no separate global
 *                                        "Metrics" section)
 *   #/models/<model>/tasks/<task_id>  -> task detail (steps / frames / video)
 */

const APP_ROOT = document.getElementById("app");
const BREADCRUMB = document.getElementById("breadcrumb");
const METRIC_TOOLTIP = document.getElementById("metric-tooltip");

// ---------------------------------------------------------------- utilities

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "class") el.className = value;
      else if (key === "html") el.innerHTML = value;
      else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2), value);
      else if (value !== null && value !== undefined) el.setAttribute(key, value);
    }
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    el.appendChild(typeof child === "string" || typeof child === "number" ? document.createTextNode(child) : child);
  }
  return el;
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(body.error || `Request failed: ${response.status}`);
  }
  return response.json();
}

function fmtNumber(value, digits = 3) {
  if (value === null || value === undefined) return "\u2013";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(digits);
  return String(value);
}

function fmtPercent(value) {
  if (value === null || value === undefined) return "\u2013";
  return `${(value * 100).toFixed(1)}%`;
}

// Render a metric value according to its declared format (see METRIC_DEFINITIONS in server.py).
function fmtByFormat(value, format) {
  if (value === null || value === undefined) return "\u2013";
  switch (format) {
    case "boolean":
      return value ? "true" : "false";
    case "percent":
    case "ratio":
      return fmtPercent(value);
    case "meters":
      return `${fmtNumber(value, 1)} m`;
    case "seconds":
      return `${fmtNumber(value, 1)} s`;
    case "count":
      return fmtNumber(value, 0);
    default:
      return fmtNumber(value);
  }
}

function statusBadge(status) {
  return h("span", { class: `badge status-${status}` }, status);
}

// Renders the benchmark result of a *finished* episode: "success" (the agent accomplished the
// task) or "failed" (it ran to completion without doing so). This is distinct from the run
// status (completed/failed/running), which this site otherwise never surfaces per-task since
// only finished episodes are ever listed.
function outcomeBadge(outcome) {
  const label = outcome || "unknown";
  return h("span", { class: `badge status-${outcome === "success" ? "completed" : "failed"}` }, label);
}

// Metric name -> one-line English description, shown in a small tooltip on click. The name
// itself is rendered as a dotted-underline "term" so it reads like a glossary reference.
function metricTerm(label, description) {
  const el = h("span", { class: "metric-term", tabindex: "0" }, label);
  if (!description) return el;
  el.addEventListener("click", (evt) => {
    evt.stopPropagation();
    showMetricTooltip(el, description);
  });
  el.addEventListener("keydown", (evt) => {
    if (evt.key === "Enter" || evt.key === " ") {
      evt.preventDefault();
      showMetricTooltip(el, description);
    }
  });
  return el;
}

function showMetricTooltip(anchor, description) {
  if (!METRIC_TOOLTIP) return;
  const isSame = METRIC_TOOLTIP.dataset.anchor === description && !METRIC_TOOLTIP.hidden;
  if (isSame) {
    hideMetricTooltip();
    return;
  }
  METRIC_TOOLTIP.textContent = description;
  METRIC_TOOLTIP.dataset.anchor = description;
  METRIC_TOOLTIP.hidden = false;
  const rect = anchor.getBoundingClientRect();
  const top = window.scrollY + rect.bottom + 8;
  let left = window.scrollX + rect.left;
  const maxLeft = window.scrollX + document.documentElement.clientWidth - METRIC_TOOLTIP.offsetWidth - 16;
  left = Math.max(16, Math.min(left, Math.max(16, maxLeft)));
  METRIC_TOOLTIP.style.top = `${top}px`;
  METRIC_TOOLTIP.style.left = `${left}px`;
}

function hideMetricTooltip() {
  if (!METRIC_TOOLTIP) return;
  METRIC_TOOLTIP.hidden = true;
  delete METRIC_TOOLTIP.dataset.anchor;
}

document.addEventListener("click", hideMetricTooltip);
window.addEventListener("hashchange", hideMetricTooltip);

// Build a described-metrics table (used both per task-group on the model page and, in a
// single-row form, on the task detail page).
//
// A metric that started out boolean (e.g. "reached destination: yes/no") is pre-aggregated by
// the server into a single success-rate percentage (see server.py's _group_metric_summary),
// with min/max left null since "the minimum of a set of true/false values" isn't a meaningful
// statistic. Those rows render the rate under "Mean" and leave Min/Max blank, rather than the
// confusing `true`/`false` text a naive per-boolean min/max would have shown.
function metricsTable(caption, entries) {
  return h("table", { class: "data-table metrics-table" },
    h("caption", null, caption),
    h("thead", null, h("tr", null,
      h("th", null, "Metric"), h("th", { class: "num" }, "N"),
      h("th", { class: "num" }, "Mean"), h("th", { class: "num" }, "Min"), h("th", { class: "num" }, "Max"))),
    h("tbody", null, entries.map((entry) => {
      const isRate = entry.min === null && entry.max === null;
      return h("tr", null,
        h("td", null, metricTerm(entry.label, entry.description)),
        h("td", { class: "num" }, entry.count),
        h("td", { class: "num" }, fmtByFormat(entry.mean, entry.format)),
        h("td", { class: "num" }, isRate ? "\u2013" : fmtByFormat(entry.min, entry.format)),
        h("td", { class: "num" }, isRate ? "\u2013" : fmtByFormat(entry.max, entry.format)));
    })),
  );
}

function setBreadcrumb(items) {
  BREADCRUMB.innerHTML = "";
  items.forEach((item, index) => {
    if (index > 0) BREADCRUMB.appendChild(h("span", { class: "sep" }, "\u203a"));
    if (item.href && index !== items.length - 1) {
      BREADCRUMB.appendChild(h("a", { href: item.href }, item.label));
    } else {
      BREADCRUMB.appendChild(h("span", { class: "current" }, item.label));
    }
  });
}

function renderLoading() {
  APP_ROOT.innerHTML = "";
  APP_ROOT.appendChild(h("div", { class: "loading" }, "Loading\u2026"));
}

function renderError(message) {
  APP_ROOT.innerHTML = "";
  APP_ROOT.appendChild(
    h("div", { class: "empty-state" },
      h("p", null, "Could not load this view."),
      h("p", { class: "mono" }, message))
  );
}

// ---------------------------------------------------------------- router

const ROUTES = [
  { pattern: /^#\/?$/, view: viewModelList },
  { pattern: /^#\/models\/([^/]+)\/?$/, view: (m) => viewModelDetail(decodeURIComponent(m[1])) },
  { pattern: /^#\/models\/([^/]+)\/tasks\/([^/]+)\/?$/, view: (m) => viewTaskDetail(decodeURIComponent(m[1]), decodeURIComponent(m[2])) },
];

function router() {
  const hash = window.location.hash || "#/";
  for (const route of ROUTES) {
    const match = hash.match(route.pattern);
    if (match) {
      route.view(match);
      return;
    }
  }
  viewModelList();
}

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", router);

// ---------------------------------------------------------------- view: model list

async function viewModelList() {
  setBreadcrumb([{ label: "Models" }]);
  renderLoading();
  let data;
  try {
    data = await fetchJSON("/api/models");
  } catch (err) {
    renderError(err.message);
    return;
  }

  const section = h("section", { class: "view" },
    h("h2", { class: "view-title" }, "Evaluated Models"),
    h("p", { class: "view-lede" },
      `${data.models.length} model${data.models.length === 1 ? "" : "s"} found under `,
      h("code", null, "AgentEvaluation/output/tasks/"), "."),
  );

  if (data.models.length === 0) {
    section.appendChild(h("div", { class: "empty-state" }, "No evaluation output has been produced yet."));
    APP_ROOT.innerHTML = "";
    APP_ROOT.appendChild(section);
    return;
  }

  // Only finished episodes are shown anywhere on this site (see server.py's build_model_summary):
  // "Success" means the agent actually accomplished the task, "Failed" means it ran to
  // completion without accomplishing it. Runs that crashed or are still in progress are counted
  // here but never listed individually -- they aren't a benchmark result yet.
  const grid = h("div", { class: "model-grid" });
  for (const model of data.models) {
    const tile = h("a", { class: "model-tile", href: `#/models/${encodeURIComponent(model.model)}` },
      h("h3", null, model.model),
      h("div", { class: "stat-row" }, "Finished tasks", h("b", null, model.task_count)),
      h("div", { class: "stat-row" }, "Success", h("b", null, model.completed_count)),
      h("div", { class: "stat-row" }, "Failed", h("b", null, model.failed_count)),
      h("div", { class: "tag-row" }, model.task_groups.map((g) => h("span", { class: "badge" }, g))),
    );
    grid.appendChild(tile);
  }
  section.appendChild(grid);

  APP_ROOT.innerHTML = "";
  APP_ROOT.appendChild(section);
}

// ---------------------------------------------------------------- view: model detail

async function viewModelDetail(model) {
  setBreadcrumb([{ label: "Models", href: "#/" }, { label: model }]);
  renderLoading();
  let data;
  try {
    data = await fetchJSON(`/api/models/${encodeURIComponent(model)}`);
  } catch (err) {
    renderError(err.message);
    return;
  }

  const section = h("section", { class: "view" },
    h("h2", { class: "view-title" }, model),
    h("p", { class: "view-lede" }, "Aggregate results and per-task-type breakdown for this model."),
  );

  // `task_count` / `completed_count` / `failed_count` only ever cover finished episodes: a
  // crashed or still-running task isn't a benchmark result and is deliberately left out of every
  // list and count on this page (see server.py's build_model_summary).
  const bs = data.batch_report_summary;
  section.appendChild(h("div", { class: "stat-strip" },
    statCell("Finished tasks", data.task_count),
    statCell("Success", data.completed_count, "success"),
    statCell("Failed", data.failed_count, data.failed_count > 0 ? "accent" : ""),
    statCell("QA accuracy", bs && bs.accuracy !== null && bs.accuracy !== undefined ? fmtPercent(bs.accuracy) : "\u2013"),
    statCell("Nav arrival rate", bs && bs.navigation_arrival_rate !== null && bs.navigation_arrival_rate !== undefined ? fmtPercent(bs.navigation_arrival_rate) : "\u2013"),
    statCell("Closure violation rate", bs && bs.closure_violation_rate !== null && bs.closure_violation_rate !== undefined ? fmtPercent(bs.closure_violation_rate) : "\u2013", bs && bs.closure_violation_rate ? "accent" : ""),
  ));

  // Task-type groups are laid out along the benchmark difficulty ladder (Level 1-5, see
  // server.py's LADDER_LEVELS): the server sends a `ladder` array of levels, each carrying the
  // groups that actually have results plus their display labels (e.g. "Visual Recognition
  // (VR)"). The environmental-condition variants (weather / time-of-day) form their own level
  // rendered at the very bottom, below the ladder, since they replay Level-1/2 tasks under
  // harsher conditions rather than forming a difficulty rung of their own. Each group still
  // carries its own curated metrics table right below its task chips -- metrics are
  // task-type-specific (a QA task has no "path length"; a plain nav task has no "closure
  // violated"), so there is no separate global Metrics section.
  const groupsWrap = h("div", { class: "ladder", style: "margin-top: 24px;" });

  const renderGroup = (group, label, parent) => {
    const tasks = data.tasks_by_group[group] || [];
    const succeeded = tasks.filter((t) => t.outcome === "success").length;
    const failed = tasks.filter((t) => t.outcome === "failed").length;
    const groupMetrics = (data.group_metrics && data.group_metrics[group]) || [];

    const chipGrid = h("div", { class: "task-chip-grid" });
    for (const task of tasks) {
      const violated = task.metrics && task.metrics.closure_violated;
      chipGrid.appendChild(
        h("a", {
          class: "task-chip",
          href: `#/models/${encodeURIComponent(model)}/tasks/${encodeURIComponent(task.task_id)}`,
        },
          h("span", { class: "task-chip__id" }, task.task_id),
          outcomeBadge(task.outcome),
          violated ? h("span", { class: "badge status-failed", style: "margin-left:4px;" }, "closure") : null,
        )
      );
    }

    const groupSection = h("div", { class: "group-section" },
      h("div", { class: "group-heading" },
        h("h3", null, group),
        label ? h("span", { class: "group-label" }, label) : null,
        h("span", { class: "group-count" }, `${tasks.length} tasks \u00b7 ${succeeded} success \u00b7 ${failed} failed`)),
      chipGrid,
    );
    if (groupMetrics.length > 0) {
      groupSection.appendChild(
        h("div", { class: "group-metrics" }, metricsTable(`${group} metrics`, groupMetrics))
      );
    }
    parent.appendChild(groupSection);
  };

  // Older servers (or hand-built payloads) may not send `ladder`; fall back to rendering the
  // flat group list as a single untitled level so the page still works.
  const ladder = Array.isArray(data.ladder) && data.ladder.length > 0
    ? data.ladder
    : [{ key: "other", title: null,
         groups: (data.task_groups || []).map((g) => ({ group: g, label: null })) }];

  for (const level of ladder) {
    const levelSection = h("div", { class: `level-section level-${level.key || "other"}` });
    if (level.title) {
      const levelTasks = (level.groups || [])
        .reduce((total, entry) => total + ((data.tasks_by_group[entry.group] || []).length), 0);
      levelSection.appendChild(h("div", { class: "level-heading" },
        h("h3", null, level.title),
        h("span", { class: "level-count" }, `${levelTasks} tasks`)));
    }
    for (const entry of level.groups || []) {
      renderGroup(entry.group, entry.label, levelSection);
    }
    groupsWrap.appendChild(levelSection);
  }
  section.appendChild(groupsWrap);

  APP_ROOT.innerHTML = "";
  APP_ROOT.appendChild(section);
}

function statCell(label, value, accentClass) {
  return h("div", { class: "stat-cell" },
    h("div", { class: "stat-label" }, label),
    h("div", { class: `stat-value ${accentClass || ""}` }, String(value)));
}

// ---------------------------------------------------------------- view: task detail

let currentFrameIndex = 0;
let currentTaskFrames = [];

async function viewTaskDetail(model, taskId) {
  setBreadcrumb([
    { label: "Models", href: "#/" },
    { label: model, href: `#/models/${encodeURIComponent(model)}` },
    { label: taskId },
  ]);
  renderLoading();
  let data;
  try {
    data = await fetchJSON(`/api/models/${encodeURIComponent(model)}/tasks/${encodeURIComponent(taskId)}`);
  } catch (err) {
    renderError(err.message);
    return;
  }

  const report = data.report || {};
  const metrics = report.metrics || {};
  const steps = report.steps || [];
  currentTaskFrames = data.frames || [];
  currentFrameIndex = 0;

  const section = h("section", { class: "view" },
    h("h2", { class: "view-title" }, taskId),
    h("p", { class: "view-lede" }, `${data.task_group || "Task"} \u00b7 model ${model}`),
  );

  section.appendChild(h("dl", { class: "task-meta-grid" },
    metaItem("Result", outcomeBadge(data.outcome)),
    metaItem("Task type", data.task_type || "\u2013"),
    metaItem("Steps completed", report.steps_completed ?? "\u2013"),
  ));

  const metricEntries = data.metric_entries || [];
  if (metricEntries.length > 0) {
    section.appendChild(h("div", { class: "card" },
      h("p", { class: "card-title" }, "Metrics"),
      h("dl", { class: "metric-value-grid" }, metricEntries.flatMap((entry) => [
        h("dt", null, metricTerm(entry.label, entry.description)),
        h("dd", null, fmtByFormat(entry.value, entry.format)),
      ]))));
  }

  if (data.status === "failed" && data.failure) {
    section.appendChild(h("div", { class: "closure-alert" },
      h("b", null, "Run failed: "), data.failure.error || "unknown error"));
  }

  if (metrics.closure_violated && metrics.closure_violation) {
    const cv = metrics.closure_violation;
    section.appendChild(h("div", { class: "closure-alert" },
      h("b", null, "Closure violation: "),
      `crossed restricted edge(s) at step ${cv.step} (t=${fmtNumber(cv.elapsed_episode_seconds, 1)}s) \u2014 `,
      (cv.crossed_edges || []).map((e) => `${e.label}#${e.edge_index}`).join(", ")));
  }

  // Instructions / question block, tolerant of both nav-style and QA-style reports.
  if (report.instructions) {
    section.appendChild(h("blockquote", { class: "step-text" }, h("b", null, "Instructions"), report.instructions));
  }
  if (report.question) {
    const optionsList = h("ul", { class: "qa-options" });
    const answer = report.answer || {};
    const options = report.options || [];
    const letters = ["A", "B", "C", "D"];
    options.forEach((opt, idx) => {
      const letter = letters[idx];
      const isCorrect = metrics.correct_answer === letter;
      const isChosen = answer.answer === letter;
      optionsList.appendChild(h("li", { class: [isCorrect ? "is-correct" : "", isChosen ? "is-chosen" : ""].join(" ") },
        h("span", { class: "letter" }, letter), opt.text || ""));
    });
    section.appendChild(h("blockquote", { class: "step-text" }, h("b", null, "Question"), report.question));
    section.appendChild(h("div", { class: "card" }, h("p", { class: "card-title" }, "Options"), optionsList));
  }

  if (report.restricted_zones && report.restricted_zones.length) {
    const zoneTable = h("table", { class: "data-table" },
      h("caption", null, "Restricted zones (road-closure polylines)"),
      h("thead", null, h("tr", null, h("th", null, "Label"), h("th", { class: "num" }, "Waypoints"))),
      h("tbody", null, report.restricted_zones.map((z) => h("tr", null,
        h("td", null, z.label || "\u2013"),
        h("td", { class: "num" }, (z.vertices || []).length)))));
    section.appendChild(h("div", { class: "card" }, h("p", { class: "card-title" }, "Constraints"), zoneTable));
  }

  // Two-column layout: video/frame viewer on the left, step list on the right.
  const twoCol = h("div", { class: "two-col" });

  const leftCol = h("div", null);
  if (data.video_available) {
    leftCol.appendChild(h("p", { class: "section-title" }, "Episode video"));
    leftCol.appendChild(h("video", { class: "video-frame", controls: "controls", src: data.video_url }));
  }

  leftCol.appendChild(h("p", { class: "section-title" }, `Frames (${currentTaskFrames.length})`));
  const frameStrip = h("div", { class: "frame-strip", id: "frame-strip" });
  const frameViewer = h("div", { class: "frame-viewer", id: "frame-viewer" });
  currentTaskFrames.forEach((frame, index) => {
    const violated = frameViolatesClosure(frame, steps);
    const thumb = h("div", { class: `frame-thumb${violated ? " violation" : ""}`, "data-index": index },
      h("img", { src: `${data.frame_base_url}/${encodeURIComponent(frame.file)}`, loading: "lazy" }),
      h("div", { class: "frame-thumb__label" }, frameLabel(frame)));
    thumb.addEventListener("click", () => selectFrame(index, data, steps));
    frameStrip.appendChild(thumb);
  });
  leftCol.appendChild(frameStrip);
  leftCol.appendChild(frameViewer);
  twoCol.appendChild(leftCol);

  const rightCol = h("div", null);
  rightCol.appendChild(h("p", { class: "section-title" }, `Steps (${steps.length})`));
  const stepList = h("div", { class: "step-list", id: "step-list" });
  const stepDetail = h("div", { class: "step-detail card", id: "step-detail", style: "margin-top:14px;" },
    h("p", { class: "card-title" }, "Step detail"),
    h("p", { class: "empty-state" }, "Select a step to inspect its observation, reasoning, and action."));
  steps.forEach((step, index) => {
    const row = h("div", { class: "step-row", "data-index": index },
      h("div", { class: "step-row__head" },
        h("span", { class: "step-index" }, `Step ${step.step}`),
        h("span", { class: "step-row__meta" },
          step.closure_crossed ? "\u26a0 closure" : "",
          " ",
          step.progress_after && step.progress_after.distance_to_destination_meters != null
            ? `${fmtNumber(step.progress_after.distance_to_destination_meters, 1)} m`
            : "")),
      h("div", { class: "step-row__text" }, step.reason || step.observation || ""));
    row.addEventListener("click", () => selectStep(index, steps));
    stepList.appendChild(row);
  });
  rightCol.appendChild(stepList);
  rightCol.appendChild(stepDetail);
  twoCol.appendChild(rightCol);

  section.appendChild(twoCol);

  APP_ROOT.innerHTML = "";
  APP_ROOT.appendChild(section);

  if (currentTaskFrames.length > 0) selectFrame(0, data, steps);
}

function metaItem(label, value) {
  return h("div", null, h("dt", null, label), h("dd", null, value instanceof Node ? value : String(value)));
}

function frameLabel(frame) {
  if (frame.kind === "before" || frame.kind === "action") {
    return `${frame.step != null ? "s" + frame.step : ""} ${frame.kind}${frame.sub_index != null ? " " + frame.sub_index : ""}`.trim();
  }
  return frame.kind || "frame";
}

function frameViolatesClosure(frame, steps) {
  if (frame.step == null) return false;
  const step = steps.find((s) => s.step === frame.step);
  return !!(step && step.closure_crossed && frame.kind === "before");
}

function selectFrame(index, taskData, steps) {
  currentFrameIndex = index;
  const frame = currentTaskFrames[index];
  document.querySelectorAll(".frame-thumb").forEach((el) => el.classList.remove("active"));
  const activeThumb = document.querySelector(`.frame-thumb[data-index="${index}"]`);
  if (activeThumb) {
    activeThumb.classList.add("active");
    activeThumb.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  }
  const viewer = document.getElementById("frame-viewer");
  if (!viewer) return;
  viewer.innerHTML = "";
  viewer.appendChild(h("img", { src: `${taskData.frame_base_url}/${encodeURIComponent(frame.file)}` }));

  const relatedStep = frame.step != null ? steps.find((s) => s.step === frame.step) : null;
  const captionParts = [frame.file];
  if (relatedStep) {
    const prog = frame.kind === "action" || frame.kind === "before" ? relatedStep.progress_before : relatedStep.progress_after;
    if (relatedStep.progress_after && frame.kind !== "before") {
      captionParts.push(`completed=${fmtNumber(relatedStep.progress_after.task_completed)}`);
      captionParts.push(`dist=${fmtNumber(relatedStep.progress_after.distance_to_destination_meters, 1)}m`);
    } else if (relatedStep.progress_before) {
      captionParts.push(`completed=${fmtNumber(relatedStep.progress_before.task_completed)}`);
      captionParts.push(`dist=${fmtNumber(relatedStep.progress_before.distance_to_destination_meters, 1)}m`);
    }
    if (relatedStep.closure_check_active) {
      captionParts.push(relatedStep.closure_crossed ? "closure=VIOLATED" : "closure=clear");
    }
  }
  viewer.appendChild(h("p", { class: "step-row__meta", style: "margin-top:6px;" }, captionParts.join("  \u00b7  ")));

  if (relatedStep) {
    const stepRow = document.querySelector(`.step-row[data-index="${steps.indexOf(relatedStep)}"]`);
    if (stepRow) selectStep(steps.indexOf(relatedStep), steps, /*fromFrame=*/true);
  }
}

function selectStep(index, steps, fromFrame) {
  document.querySelectorAll(".step-row").forEach((el) => el.classList.remove("active"));
  const row = document.querySelector(`.step-row[data-index="${index}"]`);
  if (row) {
    row.classList.add("active");
    if (!fromFrame) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  const step = steps[index];
  const detail = document.getElementById("step-detail");
  if (!detail || !step) return;
  detail.innerHTML = "";
  detail.appendChild(h("p", { class: "card-title" }, `Step detail \u2014 step ${step.step}`));

  detail.appendChild(h("dl", { class: "kv-list" },
    kv("Action", JSON.stringify(step.action)),
    kv("Duration (s)", fmtNumber(step.duration_seconds)),
    kv("Model attempts", step.model_attempts),
    kv("Elapsed episode (s)", fmtNumber(step.elapsed_episode_seconds)),
    kv("Closure check active", step.closure_check_active ? "true" : "false"),
    kv("Closure crossed", step.closure_crossed ? "\u26a0 true" : "false"),
  ));

  if (step.closure_notice_injected) {
    detail.appendChild(h("div", { class: "closure-alert" }, h("b", null, "Notice injected this step: "), step.closure_notice_injected));
  }

  if (step.observation) detail.appendChild(h("blockquote", { class: "step-text" }, h("b", null, "Observation"), step.observation));
  if (step.reason) detail.appendChild(h("blockquote", { class: "step-text" }, h("b", null, "Reason"), step.reason));

  if (step.raw_response) {
    detail.appendChild(h("p", { class: "section-title" }, "Raw model response"));
    detail.appendChild(h("pre", { class: "raw-block" }, step.raw_response));
  }
}

function kv(label, value) {
  return [h("dt", null, label), h("dd", null, String(value))];
}
