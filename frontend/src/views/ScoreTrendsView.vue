<template>
  <StateDisplay v-if="loading && !personalReport" type="loading" skeleton="chart" />
  <div v-else class="score-trends-page assessment-typography">
    <header class="section-page-header">
      <div>
        <h1>Action Assessment / 动作评估</h1>
        <p>姿态纠错热力图与分项评估统计</p>
      </div>
    </header>

    <section
      v-if="showScoreHero || allDistribution.length"
      class="hero-top-row"
    >
      <section
        v-if="showScoreHero"
        class="score-hero-banner"
        :class="scoreFeedback.tone"
      >
        <div class="score-hero-main">
          <span class="score-hero-emoji">{{ scoreFeedback.emoji }}</span>
          <div class="score-hero-score-block">
            <p class="score-hero-label">{{ heroScoreLabel }}</p>
            <div class="score-hero-score-line">
              <strong class="score-hero-value">{{ heroScore }}</strong>
              <span class="score-hero-unit">分</span>
            </div>
          </div>
        </div>
        <div class="score-hero-message score-hero-message--compact">
          <strong>{{ scoreFeedback.title }}</strong>
          <p>{{ scoreFeedback.message }}</p>
        </div>
      </section>

      <article v-if="allDistribution.length" class="distribution-hero-card">
        <header>
          <h4>训练分布</h4>
          <span>全部动作</span>
        </header>
        <div ref="distributionRef" class="distribution-chart" />
      </article>
    </section>

    <section class="summary-filter-bar">
      <div class="summary-filter-controls">
        <label>
          <span>动作筛选 / Exercise</span>
          <select v-model="exerciseFilter" @change="() => loadData()">
            <option value="">全部动作</option>
            <option v-for="ex in EXERCISE_OPTIONS" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
          </select>
        </label>
        <label>
          <span>时间范围 / Range</span>
          <select v-model="rangePreset" @change="applyRange">
            <option value="7d">近 7 天</option>
            <option value="all">全部记录</option>
          </select>
        </label>
      </div>
      <div class="summary-card-grid merged-stats">
        <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
          <span>{{ item.label }}</span>
          <strong :class="item.tone">{{ item.value }}</strong>
          <small>{{ item.hint }}</small>
        </article>
      </div>
    </section>

    <p v-if="loadError" class="trend-load-error">{{ loadError }}</p>

    <section class="error-frames-section">
      <div class="section-head">
        <h2>动作评估 / Pose Assessment</h2>
        <p>实时评分低于 80 分阈值时自动记录该时刻骨架线条，橙色为待改进部位</p>
      </div>

      <div class="threshold-tabs">
        <button
          type="button"
          class="threshold-tab"
          :class="{ active: thresholdFilter === 'all' }"
          @click="thresholdFilter = 'all'"
        >全部</button>
        <button
          v-for="t in thresholds"
          :key="t"
          type="button"
          class="threshold-tab"
          :class="{ active: thresholdFilter === String(t) }"
          @click="thresholdFilter = String(t)"
        >{{ thresholdLabel(t) }}</button>
      </div>

      <div class="error-frames-layout">
        <div class="frame-thumbs">
          <button
            v-for="(frame, index) in visibleErrorFrames"
            :key="`${frame.session_id}-${frame.timestamp_ms}-${index}`"
            type="button"
            class="thumb-card"
            :class="{ active: selectedFrameIndex === index, blank: !frame.has_skeleton }"
            @click="selectedFrameIndex = index"
          >
            <span class="thumb-score" :class="frame.has_skeleton ? (frame.score < 60 ? 'bad' : frame.score < 80 ? 'warn' : 'ok') : (frame.in_threshold_band ? 'warn' : 'blank')">
              {{ frame.has_skeleton || frame.in_threshold_band ? frame.score : '—' }}
            </span>
            <strong>{{ frame.exercise_name }}</strong>
            <small>{{ frame.captured_at || frame.date }}</small>
            <small v-if="!frame.has_skeleton" class="thumb-blank-hint">未落入阈值</small>
          </button>
          <p v-if="!visibleErrorFrames.length" class="empty-hint">暂无训练记录，完成训练后将按每次会话显示骨架截图</p>
        </div>
        <ErrorPoseViewer
          :key="`${selectedErrorFrame?.session_id ?? 'none'}-${selectedErrorFrame?.timestamp_ms ?? 0}-${selectedFrameIndex}`"
          :frame="selectedErrorFrame"
          variant="error"
        />
      </div>
    </section>

    <div class="analytics-layout">
      <aside class="chart-nav">
        <h3>评估统计</h3>
        <button
          v-for="card in chartCards"
          :key="card.key"
          type="button"
          class="chart-nav-btn"
          :class="{ active: activeChart === card.key }"
          @click="activeChart = card.key"
        >
          <component :is="card.icon" :size="18" />
          <div>
            <strong>{{ card.label }}</strong>
            <small>{{ card.hint }}</small>
          </div>
        </button>
      </aside>

      <main class="chart-panel">
        <div class="chart-panel-body">
          <CalorieRingPanel
            v-if="activeChart === 'calorie'"
            class="chart-panel-fill"
            :total-calories="totalCalories"
            :goal="calorieGoal"
            :subtitle="calorieSubtitle"
            :breakdown="displayCharts.calorie_by_exercise"
          />

          <ReportCharts
            v-else-if="activeChart === 'trend' || activeChart === 'radar'"
            :key="activeChart"
            class="chart-panel-fill"
            fill-height
            :charts="displayCharts"
            :trend-series="trendSeries"
            :radar-subtitle="radarSubtitle"
            :trend-subtitle="trendSubtitle"
            :distribution-data="allDistribution"
            :show-trend="activeChart === 'trend'"
            :show-calorie="false"
            :show-radar="activeChart === 'radar'"
            :show-errors="false"
            :show-distribution="false"
          />

          <section v-else-if="activeChart === 'comparison'" class="comparison-card chart-panel-fill">
            <h2>动作对比详情</h2>
            <div v-if="comparisonRows.length" class="comparison-table-wrap">
              <table class="comparison-table">
                <thead>
                  <tr>
                    <th>动作</th>
                    <th>训练次数</th>
                    <th>平均分</th>
                    <th>最新分</th>
                    <th>最高分</th>
                    <th>有效率</th>
                    <th>错误数</th>
                    <th>卡路里</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in comparisonRows" :key="row.exercise">
                    <td><strong>{{ row.name }}</strong></td>
                    <td>{{ row.count }}</td>
                    <td>{{ row.avg_score }}</td>
                    <td>{{ row.latest_score }}</td>
                    <td>{{ row.best_score }}</td>
                    <td>{{ row.valid_rate }}%</td>
                    <td>{{ row.total_errors }}</td>
                    <td>{{ row.calories }} kcal</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <StateDisplay v-else type="empty" title="暂无对比数据" text="完成不同动作训练后将显示详细对比" />
            <div ref="comparisonChartRef" class="comparison-chart" />
          </section>

          <StateDisplay
            v-else
            class="chart-panel-fill"
            type="empty"
            title="暂无图表数据"
            text="完成训练后将生成分数趋势与质量分析"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "ScoreTrendsView" });

import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { BarChart3, Flame, Radar, Table2 } from "lucide-vue-next";
import {
  type ErrorFrameItem,
  type PersonalReport,
  type SessionPoseSlot,
} from "../api/reports";
import ErrorPoseViewer from "../components/ErrorPoseViewer.vue";
import CalorieRingPanel from "../components/CalorieRingPanel.vue";
import ReportCharts, { type TrendSeriesItem } from "../components/ReportCharts.vue";
import StateDisplay from "../components/StateDisplay.vue";
import { getScoreFeedback } from "../utils/scoreFeedback";
import { exercises } from "../stores/training";
import { getSessions } from "../api/sessions";
import { useReportsCacheStore } from "../stores/reportsCache";

const reportsCache = useReportsCacheStore();

const EXERCISE_OPTIONS = exercises.map((item) => ({ key: item.key, name: item.name }));

const chartCards = [
  { key: "trend", label: "评分趋势", hint: "近7日折线", icon: BarChart3 },
  { key: "calorie", label: "卡路里", hint: "按动作统计", icon: Flame },
  { key: "radar", label: "质量雷达", hint: "维度评分", icon: Radar },
  { key: "comparison", label: "动作对比", hint: "表格+柱状", icon: Table2 },
] as const;

type ChartKey = (typeof chartCards)[number]["key"];

const personalReport = ref<PersonalReport | null>(null);
const allExerciseReport = ref<PersonalReport | null>(null);
const errorFrames = ref<ErrorFrameItem[]>([]);
const sessionSlots = ref<SessionPoseSlot[]>([]);
const thresholds = ref<number[]>([80, 60]);
const thresholdFilter = ref("all");
const selectedFrameIndex = ref(0);
const loading = ref(true);
const loadError = ref("");
const exerciseFilter = ref("");
const rangePreset = ref("7d");
const dateFrom = ref("");
const dateTo = ref("");
const activeChart = ref<ChartKey>("trend");
const comparisonChartRef = ref<HTMLElement | null>(null);
const distributionRef = ref<HTMLElement | null>(null);
let comparisonChart: echarts.ECharts | null = null;
let distributionChart: echarts.ECharts | null = null;

const queryParams = computed(() => ({
  date_from: dateFrom.value || undefined,
  date_to: dateTo.value || undefined,
  exercise: exerciseFilter.value || undefined,
}));

const allDistribution = computed(() =>
  allExerciseReport.value?.charts?.exercise_distribution || [],
);

function enrichFrame(
  frame: ErrorFrameItem | null,
  items: ErrorFrameItem[],
  sessionId: string,
  predicate: (score: number) => boolean,
): ErrorFrameItem | null {
  if (frame?.landmarks?.length) return frame;
  const candidates = items.filter(
    (item) => item.session_id === sessionId && predicate(item.score) && item.landmarks?.length,
  );
  if (!candidates.length) return frame;
  return candidates.reduce((best, cur) => (cur.score < best.score ? cur : best));
}

function enrichSlot(slot: SessionPoseSlot, items: ErrorFrameItem[]): SessionPoseSlot {
  const sessionId = slot.session_id;
  const frameAny = enrichFrame(slot.frame_any, items, sessionId, (score) => score < 80)
    || (slot.average_score < 80 ? enrichFrame(null, items, sessionId, (score) => score < 80) : null);
  return {
    ...slot,
    frame_mid: enrichFrame(slot.frame_mid, items, sessionId, (score) => score >= 60 && score < 80),
    frame_low: enrichFrame(slot.frame_low, items, sessionId, (score) => score < 60),
    frame_any: frameAny,
  };
}

function buildSessionSlots(
  apiSlots: SessionPoseSlot[] | undefined,
  items: ErrorFrameItem[],
  report: PersonalReport | null,
): SessionPoseSlot[] {
  const slotMap = new Map<string, SessionPoseSlot>();

  const ensureSlot = (sessionId: string, seed: Partial<SessionPoseSlot>) => {
    if (!slotMap.has(sessionId)) {
      slotMap.set(sessionId, {
        session_id: sessionId,
        exercise: seed.exercise || "",
        exercise_name: seed.exercise_name || seed.exercise || sessionId,
        average_score: Number(seed.average_score ?? 0),
        captured_at: seed.captured_at || "",
        frame_mid: null,
        frame_low: null,
        frame_any: null,
      });
    }
    const slot = slotMap.get(sessionId)!;
    if (seed.exercise) slot.exercise = seed.exercise;
    if (seed.exercise_name) slot.exercise_name = seed.exercise_name;
    if (seed.average_score != null) slot.average_score = Number(seed.average_score);
    if (seed.captured_at && (!slot.captured_at || seed.captured_at > slot.captured_at)) {
      slot.captured_at = seed.captured_at;
    }
    return slot;
  };

  for (const slot of apiSlots || []) {
    slotMap.set(slot.session_id, { ...slot });
  }

  for (const item of items) {
    const slot = ensureSlot(item.session_id, {
      exercise: item.exercise,
      exercise_name: item.exercise_name,
      average_score: item.score,
      captured_at: item.captured_at || item.date,
    });
    const score = item.score;
    if (score >= 60 && score < 80) {
      if (!slot.frame_mid || score < slot.frame_mid.score) slot.frame_mid = item;
    } else if (score < 60) {
      if (!slot.frame_low || score < slot.frame_low.score) slot.frame_low = item;
    }
    if (score < 80) {
      if (!slot.frame_any || score < slot.frame_any.score) slot.frame_any = item;
    }
  }

  for (const session of report?.recent_sessions || []) {
    ensureSlot(session.session_id, {
      exercise: session.exercise,
      exercise_name: exerciseName(session.exercise),
      average_score: session.score,
      captured_at: session.created_at || "",
    });
  }

  return [...slotMap.values()]
    .map((slot) => enrichSlot(slot, items))
    .sort((a, b) => (b.captured_at || "").localeCompare(a.captured_at || ""));
}

function isScoreInThresholdFilter(score: number, filter: string): boolean {
  if (filter === "80") return score >= 60 && score < 80;
  if (filter === "60") return score < 60;
  return score < 80;
}

function slotToDisplayItem(slot: SessionPoseSlot, frame: ErrorFrameItem | null): ErrorFrameItem {
  const inThreshold = isScoreInThresholdFilter(slot.average_score, thresholdFilter.value);

  if (frame?.landmarks?.length) {
    return {
      ...frame,
      has_skeleton: true,
      in_threshold_band: inThreshold,
    };
  }

  if (frame) {
    return {
      ...frame,
      has_skeleton: false,
      in_threshold_band: inThreshold,
      blank_reason: "未能还原姿态关键点，请重新完成该动作训练",
    };
  }

  return {
    session_id: slot.session_id,
    exercise: slot.exercise,
    exercise_name: slot.exercise_name,
    date: slot.captured_at,
    captured_at: slot.captured_at,
    score: slot.average_score,
    timestamp_ms: 0,
    errors: [],
    landmarks: null,
    body_parts: [],
    source: "no_threshold",
    has_skeleton: false,
    in_threshold_band: inThreshold,
    blank_reason: inThreshold
      ? "未能还原姿态关键点，请重新完成该动作训练"
      : "本次训练得分未落入当前阈值区间，无骨架截图",
  };
}

const visibleErrorFrames = computed(() => {
  return sessionSlots.value.map((slot) => {
    let frame: ErrorFrameItem | null = null;
    if (thresholdFilter.value === "80") frame = slot.frame_mid;
    else if (thresholdFilter.value === "60") frame = slot.frame_low;
    else frame = slot.frame_any;
    return slotToDisplayItem(slot, frame);
  });
});

const selectedErrorFrame = computed(() =>
  visibleErrorFrames.value[selectedFrameIndex.value] ?? null,
);

const totalCalories = computed(() =>
  Number(personalReport.value?.total_calories ?? 0),
);

const calorieGoal = computed(() =>
  Math.max(300, Math.round(totalCalories.value * 1.2) || 500),
);

const calorieSubtitle = computed(() =>
  exerciseFilter.value
    ? `${exerciseName(exerciseFilter.value)} · 本期累计消耗`
    : "全部动作 · 本期累计消耗",
);

const displayCharts = computed(() => {
  const charts = personalReport.value?.charts;
  if (!charts) {
    return {
      score_trend: [],
      calorie_by_exercise: [],
      exercise_distribution: [],
      quality_radar: { dimensions: [], values: [] },
      error_by_exercise: [],
    };
  }
  if (!exerciseFilter.value) return charts;

  const perRadar = charts.per_exercise_radar?.[exerciseFilter.value];
  const targetName = exerciseName(exerciseFilter.value);
  const matchedCalories = charts.calorie_by_exercise.filter((c) => c.name === targetName);
  return {
    ...charts,
    quality_radar: perRadar?.dimensions?.length ? perRadar : charts.quality_radar,
    calorie_by_exercise: matchedCalories.length ? matchedCalories : charts.calorie_by_exercise,
  };
});

const trendSeries = computed<TrendSeriesItem[]>(() => {
  const trends = personalReport.value?.exercise_trends || personalReport.value?.charts?.score_trend_by_exercise || [];
  if (exerciseFilter.value) {
    const one = trends.find((t) => t.exercise === exerciseFilter.value);
    return one ? [{ name: one.name, trend: one.trend }] : [];
  }
  return trends.map((t) => ({ name: t.name, trend: t.trend }));
});

const trendSubtitle = computed(() =>
  exerciseFilter.value
    ? `${exerciseName(exerciseFilter.value)} · 近 7 日评分变化`
    : "全部动作分色对比 · 近 7 日评分变化",
);

const radarSubtitle = computed(() =>
  exerciseFilter.value
    ? `${exerciseName(exerciseFilter.value)} 质量维度`
    : "综合各维度动作质量评估",
);

const hasChartData = computed(() =>
  (personalReport.value?.total_sessions ?? 0) > 0
  || trendSeries.value.some((s) => s.trend.length > 0),
);

const comparisonRows = computed(() =>
  personalReport.value?.exercise_comparison
  || personalReport.value?.exercise_breakdown
  || [],
);

const recentSessions = computed(() => personalReport.value?.recent_sessions || []);

const heroScore = computed(() => {
  const recent = recentSessions.value[0];
  if (recent?.score != null) return Math.round(Number(recent.score) * 10) / 10;
  const avg = personalReport.value?.average_score;
  return avg != null ? Math.round(Number(avg) * 10) / 10 : 0;
});

const heroScoreLabel = computed(() => {
  const recent = recentSessions.value[0];
  if (recent) return `最近一次训练 · ${exerciseName(recent.exercise)}`;
  return exerciseFilter.value ? exerciseName(exerciseFilter.value) : "当前平均分";
});

const scoreFeedback = computed(() => getScoreFeedback(heroScore.value));

const showScoreHero = computed(() =>
  heroScore.value > 0 || (personalReport.value?.total_sessions ?? 0) > 0,
);

const stats = computed(() => {
  const report = personalReport.value;
  const trend = report?.trend || [];
  const trendScores = trend.map((d) => d.score);
  const scoreDelta = trendScores.length >= 2
    ? Math.round((trendScores[trendScores.length - 1] - trendScores[0]) * 10) / 10
    : 0;
  return [
    {
      label: "当前平均分",
      value: report?.average_score ?? "--",
      hint: exerciseFilter.value ? exerciseName(exerciseFilter.value) : "全部动作",
      tone: "",
    },
    {
      label: "趋势变化",
      value: trendScores.length >= 2 ? `${scoreDelta >= 0 ? "+" : ""}${scoreDelta}` : "--",
      hint: rangePreset.value === "7d" ? "近7天首尾对比" : "全部记录首尾对比",
      tone: scoreDelta >= 0 ? "tone-text-green" : "",
    },
    {
      label: "训练次数",
      value: report?.total_sessions ?? 0,
      hint: rangePreset.value === "7d" ? "近7天" : "全部",
      tone: "",
    },
    {
      label: "累计卡路里",
      value: report?.total_calories ? `${Math.round(report.total_calories)}` : "--",
      hint: "千卡",
      tone: "tone-text-orange",
    },
  ];
});

function exerciseName(key: string): string {
  return exercises.find((e) => e.key === key)?.name ?? key;
}

function thresholdLabel(t: number): string {
  if (t === 80) return "60-80 分（最低时刻）";
  if (t === 60) return "低于 60 分（最低时刻）";
  return `低于 ${t} 分`;
}

function applyRange() {
  const today = new Date();
  if (rangePreset.value === "7d") {
    const from = new Date(today);
    from.setDate(from.getDate() - 6);
    dateFrom.value = from.toISOString().slice(0, 10);
    dateTo.value = today.toISOString().slice(0, 10);
  } else {
    dateFrom.value = "";
    dateTo.value = "";
  }
  loadData();
}

function renderComparisonChart() {
  if (!comparisonChartRef.value || !comparisonRows.value.length) return;
  comparisonChart?.dispose();
  comparisonChart = echarts.init(comparisonChartRef.value);
  const rows = comparisonRows.value;
  comparisonChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["平均分", "最新分", "最高分"], textStyle: { color: "#94a3b8" } },
    grid: { left: 40, right: 20, top: 40, bottom: 50 },
    xAxis: { type: "category", data: rows.map((r) => r.name), axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", max: 100, axisLabel: { color: "#94a3b8" } },
    series: [
      { name: "平均分", type: "bar", data: rows.map((r) => r.avg_score), itemStyle: { color: "#60a5fa" } },
      { name: "最新分", type: "bar", data: rows.map((r) => r.latest_score ?? r.avg_score), itemStyle: { color: "#34d399" } },
      { name: "最高分", type: "bar", data: rows.map((r) => r.best_score ?? r.avg_score), itemStyle: { color: "#f59e0b" } },
    ],
  });
  comparisonChart.resize();
}

function renderDistributionChart() {
  if (!distributionRef.value || !allDistribution.value.length) return;
  distributionChart?.dispose();
  distributionChart = echarts.init(distributionRef.value);
  distributionChart.setOption({
    tooltip: { trigger: "item", formatter: "{b}<br/>{c} 次 · {d}%" },
    series: [{
      type: "pie",
      radius: ["40%", "76%"],
      center: ["50%", "48%"],
      data: allDistribution.value,
      label: { color: "#e2e8f0", fontSize: 10 },
      color: ["#3b82f6", "#8b5cf6", "#14b8a6", "#f59e0b", "#ef4444"],
    }],
  });
  distributionChart.resize();
}

async function loadData(silent = false) {
  const baseQuery = {
    date_from: dateFrom.value || undefined,
    date_to: dateTo.value || undefined,
  };
  const filteredQuery = {
    ...baseQuery,
    exercise: exerciseFilter.value || undefined,
  };

  const cachedReport = reportsCache.getPersonalCached(filteredQuery);
  const cachedAllReport = reportsCache.getPersonalCached(baseQuery);
  const cachedFrames = reportsCache.getErrorFramesCached(filteredQuery);
  if (cachedReport) personalReport.value = cachedReport;
  if (cachedAllReport) allExerciseReport.value = cachedAllReport;
  if (cachedFrames) {
    errorFrames.value = cachedFrames.items;
    thresholds.value = cachedFrames.thresholds.length ? cachedFrames.thresholds : [80, 60];
    sessionSlots.value = buildSessionSlots(
      cachedFrames.session_slots,
      cachedFrames.items,
      cachedReport || personalReport.value,
    );
  }

  if (!silent && !personalReport.value) {
    loading.value = true;
  }
  loadError.value = "";
  selectedFrameIndex.value = 0;
  try {
    const [reportRes, allReportRes, framesRes] = await Promise.all([
      reportsCache.fetchPersonalReport(filteredQuery),
      reportsCache.fetchPersonalReport(baseQuery),
      reportsCache.fetchErrorFrames(filteredQuery),
    ]);
    personalReport.value = reportRes;
    allExerciseReport.value = allReportRes;
    errorFrames.value = framesRes.items;
    let slots = buildSessionSlots(framesRes.session_slots, framesRes.items, reportRes);
    if (!slots.length && (reportRes.total_sessions ?? 0) > 0) {
      try {
        const sessRes = await getSessions({ limit: 80 });
        slots = buildSessionSlots(
          undefined,
          framesRes.items,
          {
            ...reportRes,
            recent_sessions: (sessRes.items || []).map((s) => ({
              session_id: s.session_id,
              exercise: s.exercise,
              score: s.average_score,
              created_at: s.created_at || "",
            })),
          },
        );
      } catch {
        // keep empty slots
      }
    }
    sessionSlots.value = slots;
    thresholds.value = framesRes.thresholds.length ? framesRes.thresholds : [80, 60];
  } catch (err: unknown) {
    loadError.value = err instanceof Error ? err.message : "加载失败";
  } finally {
    loading.value = false;
    await nextTick();
    renderComparisonChart();
    renderDistributionChart();
  }
}

watch([comparisonRows, activeChart], () => {
  if (activeChart.value === "comparison") {
    nextTick().then(renderComparisonChart);
  }
});

watch(activeChart, () => {
  nextTick().then(() => {
    if (activeChart.value === "comparison") {
      renderComparisonChart();
    }
    window.dispatchEvent(new Event("resize"));
  });
});

watch(allDistribution, () => {
  nextTick().then(renderDistributionChart);
});

watch(visibleErrorFrames, () => {
  if (selectedFrameIndex.value >= visibleErrorFrames.value.length) {
    selectedFrameIndex.value = 0;
  }
});

onMounted(() => applyRange());
onActivated(() => {
  if (personalReport.value) {
    void loadData(true);
  }
});
onBeforeUnmount(() => {
  comparisonChart?.dispose();
  distributionChart?.dispose();
});
</script>

<style scoped>
.assessment-typography :is(h1, h2, h3, h4, strong, .thumb-card strong, .chart-nav-btn strong) {
  font-weight: 800;
}
.assessment-typography .section-page-header h1 { font-size: 22px; font-weight: 800; }
.assessment-typography .section-page-header p { font-size: 13px; font-weight: 600; }
.assessment-typography .section-head h2 { font-size: 18px; font-weight: 800; }
.assessment-typography .section-head p { font-size: 13px; font-weight: 600; }
.assessment-typography .threshold-tab { font-size: 13px; font-weight: 700; }
.assessment-typography .thumb-card strong { font-size: 14px; }
.assessment-typography .thumb-card small { font-size: 12px; font-weight: 600; }
.assessment-typography .thumb-score { font-size: 12px; font-weight: 800; }
.assessment-typography .summary-card span { font-size: 11px; font-weight: 700; }
.assessment-typography .summary-card strong { font-size: 22px; font-weight: 900; }
.assessment-typography .summary-card small { font-size: 10px; font-weight: 600; }
.assessment-typography .chart-nav h3 { font-size: 16px; font-weight: 800; }
.assessment-typography .chart-nav-btn strong { font-size: 14px; }
.assessment-typography .chart-nav-btn small { font-size: 12px; font-weight: 600; }
.assessment-typography .distribution-hero-card h4 { font-size: 14px; font-weight: 800; }
.assessment-typography .score-hero-label { font-size: 15px; font-weight: 800; }
.assessment-typography .score-hero-value { font-size: 52px; }
.assessment-typography .score-hero-unit { font-size: 16px; }
.assessment-typography .score-hero-message strong { font-size: 17px; font-weight: 800; }
.assessment-typography .score-hero-message p { font-size: 14px; font-weight: 600; }
.assessment-typography .trend-filter-card label { font-size: 13px; font-weight: 700; }
.assessment-typography .trend-filter-card select { font-size: 13px; font-weight: 600; }
.assessment-typography .empty-hint { font-size: 13px; font-weight: 600; }
.assessment-typography .thumb-blank-hint { color: #64748b; font-size: 11px; font-weight: 600; }

.score-trends-page {
  display: grid;
  gap: 10px;
}
.section-page-header {
  margin: 0;
}
.summary-filter-bar {
  display: grid;
  grid-template-columns: minmax(200px, 240px) 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(15,23,42,0.96);
  border: 1px solid rgba(59,130,246,0.1);
}
.summary-filter-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  align-content: center;
}
.summary-filter-controls label,
.trend-filter-card label { display: grid; gap: 4px; color: #94a3b8; font-size: 11px; }
.summary-filter-controls select,
.trend-filter-card select {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(59,130,246,0.15);
  background: rgba(8,13,26,0.8);
  color: #f8fafc;
  font-size: 12px;
}
.summary-card-grid.merged-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.compact-summary {
  padding: 8px 10px;
  gap: 2px;
}
.trend-filter-card { display: flex; gap: 16px; flex-wrap: wrap; padding: 16px 20px; border-radius: 12px; background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); }
.trend-load-error { color: #f87171; font-size: 13px; margin: 0; }

.error-frames-section {
  padding: 10px 12px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(8,13,26,0.99));
  border: 1px solid rgba(239,68,68,0.15);
  display: grid;
  gap: 8px;
}
.section-head h2 { margin: 0 0 2px; color: #f8fafc; font-size: 15px; }
.section-head p { margin: 0; color: #64748b; font-size: 11px; }
.threshold-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.threshold-tab {
  padding: 5px 10px;
  border-radius: 8px;
  border: 1px solid rgba(59,130,246,0.12);
  background: rgba(8,13,26,0.5);
  color: #94a3b8;
  cursor: pointer;
  font-size: 12px;
}
.threshold-tab.active { border-color: rgba(239,68,68,0.4); background: rgba(239,68,68,0.1); color: #fecaca; }
.error-frames-layout {
  display: grid;
  grid-template-columns: minmax(200px, 3fr) minmax(280px, 7fr);
  gap: 14px;
  align-items: stretch;
  width: 100%;
}
.frame-thumbs {
  display: grid;
  gap: 6px;
  min-width: 0;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}
.error-frames-section :deep(.error-pose-viewer) {
  min-width: 0;
  width: 100%;
  min-height: 300px;
}
.error-frames-section :deep(.pose-canvas) {
  height: 300px;
}
.thumb-card.blank { opacity: 0.72; border-style: dashed; }
.thumb-score.blank { background: #475569; }
.thumb-card {
  display: grid;
  gap: 3px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(59,130,246,0.1);
  background: rgba(8,13,26,0.5);
  text-align: left;
  cursor: pointer;
  color: #94a3b8;
}
.thumb-card.active { border-color: rgba(239,68,68,0.35); background: rgba(239,68,68,0.08); }
.thumb-card strong { color: #f8fafc; font-size: 13px; }
.thumb-card small { font-size: 11px; }
.thumb-score {
  width: fit-content;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.thumb-score.bad { background: #dc2626; }
.thumb-score.warn { background: #d97706; }
.thumb-score.ok { background: #2563eb; }
.thumb-score.highlight { background: linear-gradient(135deg, #34d399, #10b981); color: #052e16; }
.thumb-card.highlight-thumb.active { border-color: rgba(52,211,153,0.45); background: rgba(52,211,153,0.1); }
.tone-text-yellow { color: #34d399 !important; }

.score-hero-banner {
  display: grid;
  grid-template-columns: minmax(130px, auto) 1fr;
  gap: 12px;
  align-items: stretch;
  padding: 8px 14px;
  border-radius: 14px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  min-width: 0;
  height: 100%;
}
.hero-top-row {
  display: grid;
  grid-template-columns: 6.5fr 3.5fr;
  gap: 10px;
  align-items: stretch;
  min-height: 148px;
  max-height: 148px;
}
.hero-top-row:has(.score-hero-banner):not(:has(.distribution-hero-card)) {
  grid-template-columns: 1fr;
  max-height: none;
}
.hero-top-row:not(:has(.score-hero-banner)):has(.distribution-hero-card) {
  grid-template-columns: 1fr;
  max-width: 280px;
}
.distribution-hero-card {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 2px;
  padding: 6px 10px 4px;
  border-radius: 14px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  min-height: 0;
  overflow: visible;
}
.distribution-hero-card header {
  margin: 0;
  line-height: 1.2;
}
.distribution-hero-card h4 {
  margin: 0;
  color: #f8fafc;
  font-size: 13px;
  font-weight: 800;
}
.distribution-hero-card span {
  color: #64748b;
  font-size: 10px;
}
.distribution-chart {
  width: 100%;
  height: 100%;
  min-height: 108px;
  margin-top: -2px;
}
.score-hero-banner.excellent { border-color: rgba(250, 204, 21, 0.35); box-shadow: 0 0 32px rgba(250, 204, 21, 0.08); }
.score-hero-banner.good { border-color: rgba(34, 197, 94, 0.3); }
.score-hero-banner.encourage { border-color: rgba(59, 130, 246, 0.3); }
.score-hero-banner.improve { border-color: rgba(249, 115, 22, 0.3); }
.score-hero-main { display: flex; align-items: center; gap: 12px; min-width: 0; flex-shrink: 0; }
.score-hero-score-block { min-width: 0; }
.score-hero-score-line { display: flex; align-items: baseline; gap: 4px; }
.score-hero-emoji { font-size: 30px; line-height: 1; flex-shrink: 0; }
.score-hero-label { margin: 0 0 4px; color: #94a3b8; font-size: 15px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.score-hero-value { font-size: 52px; font-weight: 900; color: #f8fafc; line-height: 0.95; letter-spacing: -0.02em; }
.score-hero-unit { color: #94a3b8; font-size: 16px; font-weight: 700; }
.score-hero-message--compact {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  min-width: 0;
  padding: 2px 0;
}
.score-hero-message--compact strong {
  display: block;
  color: #f8fafc;
  font-size: 17px;
  font-weight: 800;
  margin-bottom: 4px;
  white-space: normal;
  overflow: visible;
  text-overflow: unset;
  line-height: 1.25;
}
.score-hero-message--compact p {
  margin: 0;
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.highlight-frames-section {
  padding: 20px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(8,13,26,0.99));
  border: 1px solid rgba(52, 211, 153, 0.2);
  display: grid;
  gap: 14px;
}

.analytics-layout {
  --analytics-panel-height: 520px;
  display: grid;
  grid-template-columns: minmax(220px, 3fr) minmax(320px, 7fr);
  gap: 24px;
  align-items: start;
}
.chart-panel {
  min-width: 0;
  height: var(--analytics-panel-height);
}
.chart-panel-body {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.chart-panel-fill {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chart-panel :deep(.calorie-ring-panel) {
  height: 100%;
  min-height: 0;
  padding: 16px;
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: 10px;
  overflow: hidden;
  box-sizing: border-box;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  border: 1px solid rgba(59, 130, 246, 0.14);
}
.chart-panel :deep(.ring-stage) {
  max-width: none;
  width: 100%;
  height: 100%;
  max-height: 240px;
  margin: 0 auto;
  aspect-ratio: auto;
}
.chart-panel :deep(.food-equiv) {
  padding: 8px 10px;
}
.chart-panel :deep(.breakdown-rings) {
  overflow-x: auto;
}
.chart-panel :deep(.state-display) {
  height: 100%;
  min-height: 0;
  display: grid;
  place-content: center;
  border-radius: 14px;
  background: rgba(15,23,42,0.96);
  border: 1px solid rgba(59,130,246,0.1);
}
.chart-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-radius: 14px;
  background: rgba(15,23,42,0.96);
  border: 1px solid rgba(59,130,246,0.1);
  height: var(--analytics-panel-height);
  min-height: var(--analytics-panel-height);
  max-height: var(--analytics-panel-height);
  box-sizing: border-box;
}
.chart-nav h3 { margin: 0; color: #f8fafc; font-size: 14px; }
.chart-nav-btn {
  display: flex;
  gap: 10px;
  align-items: center;
  flex: 1;
  min-height: 72px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(59,130,246,0.08);
  background: rgba(8,13,26,0.4);
  color: #94a3b8;
  cursor: pointer;
  text-align: left;
}
.chart-nav-btn.active {
  border-color: rgba(59,130,246,0.35);
  background: rgba(59,130,246,0.1);
  color: #dbeafe;
}
.chart-nav-btn strong { display: block; color: #f8fafc; font-size: 13px; }
.chart-nav-btn small { font-size: 11px; }

.comparison-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(15,23,42,0.96);
  border: 1px solid rgba(59,130,246,0.1);
  height: 100%;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
}
.comparison-card h2 {
  margin: 0;
  font-size: 15px;
  color: #f8fafc;
  flex-shrink: 0;
}
.comparison-table-wrap {
  flex: 0 1 auto;
  max-height: 42%;
  overflow: auto;
  min-height: 0;
}
.comparison-chart {
  flex: 1;
  min-height: 220px;
  width: 100%;
}
.comparison-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.comparison-table th, .comparison-table td { padding: 10px 12px; border-bottom: 1px solid rgba(59,130,246,0.08); color: #cbd5e1; text-align: left; }
.comparison-table th { color: #64748b; font-size: 11px; }
.empty-hint { color: #64748b; font-size: 12px; margin: 0; }

@media (max-width: 1000px) {
  .hero-top-row {
    grid-template-columns: 1fr;
    max-height: none;
  }
  .hero-top-row:not(:has(.score-hero-banner)):has(.distribution-hero-card) { max-width: none; }
  .summary-filter-bar { grid-template-columns: 1fr; }
  .summary-filter-controls { grid-template-columns: 1fr 1fr; }
  .summary-card-grid.merged-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .error-frames-layout, .analytics-layout { grid-template-columns: 1fr; }
  .analytics-layout { --analytics-panel-height: auto; }
  .chart-nav {
    height: auto;
    min-height: auto;
    max-height: none;
  }
  .chart-panel { height: auto; }
  .chart-panel-fill { min-height: 360px; }
}
</style>
