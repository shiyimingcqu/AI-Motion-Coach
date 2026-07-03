<template>
  <StateDisplay v-if="loading" type="loading" skeleton="chart" />
  <div v-else class="score-trends-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("scoreTrends.title") }}</h1>
        <p>{{ $t("scoreTrends.subtitle") }}</p>
      </div>
    </header>

    <section class="filter-card trend-filter-card">
      <label>
        <span>{{ $t("scoreTrends.exerciseFilter") }}</span>
        <select v-model="exerciseFilter" @change="loadData">
          <option value="">{{ $t("scoreTrends.allExercises") }}</option>
          <option v-for="ex in EXERCISE_OPTIONS" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
        </select>
      </label>
      <label>
        <span>{{ $t("scoreTrends.timeRange") }}</span>
        <select v-model="rangePreset" @change="applyRange">
          <option value="7d">{{ $t("scoreTrends.last7Days") }}</option>
          <option value="all">{{ $t("scoreTrends.allTime") }}</option>
        </select>
      </label>
    </section>

    <p v-if="loadError" class="trend-load-error">{{ loadError }}</p>

    <section class="summary-card-grid">
      <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <ReportCharts
      v-if="hasChartData"
      :charts="displayCharts"
      :trend-series="trendSeries"
      :radar-subtitle="radarSubtitle"
      :trend-subtitle="trendSubtitle"
    />

    <section class="progress-card comparison-card">
      <h2>{{ $t("scoreTrends.comparisonTitle") }}</h2>
      <div v-if="comparisonRows.length" class="comparison-table-wrap">
        <table class="comparison-table">
          <thead>
            <tr>
              <th>{{ $t("scoreTrends.tableHead_exercise") }}</th>
              <th>{{ $t("scoreTrends.tableHead_sessions") }}</th>
              <th>{{ $t("scoreTrends.tableHead_avgScore") }}</th>
              <th>{{ $t("scoreTrends.tableHead_latestScore") }}</th>
              <th>{{ $t("scoreTrends.tableHead_bestScore") }}</th>
              <th>{{ $t("scoreTrends.tableHead_validRate") }}</th>
              <th>{{ $t("scoreTrends.tableHead_errors") }}</th>
              <th>{{ $t("scoreTrends.tableHead_calories") }}</th>
              <th>{{ $t("scoreTrends.tableHead_duration") }}</th>
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
              <td>{{ row.duration_minutes }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <StateDisplay v-else type="empty" :title="$t('scoreTrends.noComparisonData')" :text="$t('scoreTrends.noComparisonText')" />
      <div ref="comparisonChartRef" class="comparison-chart" />
    </section>

    <section class="progress-card">
      <h2>{{ $t("scoreTrends.perExerciseTitle") }}</h2>
      <div class="exercise-trend-grid">
        <article v-for="item in exerciseTrendCards" :key="item.exercise" class="trend-mini-card">
          <header>
            <strong>{{ item.name }}</strong>
            <span>{{ $t("scoreTrends.daysRecorded", { count: item.trend.length }) }}</span>
          </header>
          <ul>
            <li v-for="point in item.trend" :key="point.date">
              <span>{{ point.date.slice(5) }}</span>
              <b>{{ point.score }}</b>
            </li>
          </ul>
          <p v-if="!item.trend.length" class="empty-hint">{{ $t("scoreTrends.noTrend") }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import * as echarts from "echarts";
import { getPersonalReport, type PersonalReport } from "../api/reports";
import ReportCharts, { type TrendSeriesItem } from "../components/ReportCharts.vue";
import StateDisplay from "../components/StateDisplay.vue";

const { t } = useI18n();

const EXERCISE_OPTIONS = [
  { key: "squat", name: t("exercises.squat") },
  { key: "push_up", name: t("exercises.push_up") },
  { key: "jumping_jack", name: t("exercises.jumping_jack") },
  { key: "plank", name: t("exercises.plank") },
];

const personalReport = ref<PersonalReport | null>(null);
const loading = ref(true);
const loadError = ref("");
const exerciseFilter = ref("");
const rangePreset = ref("7d");
const dateFrom = ref("");
const dateTo = ref("");
const comparisonChartRef = ref<HTMLElement | null>(null);
let comparisonChart: echarts.ECharts | null = null;

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
  return {
    ...charts,
    quality_radar: perRadar?.dimensions?.length
      ? perRadar
      : charts.quality_radar,
    calorie_by_exercise: charts.calorie_by_exercise.filter(
      (c) => c.name === exerciseName(exerciseFilter.value),
    ),
    exercise_distribution: charts.exercise_distribution.filter(
      (c) => c.name === exerciseName(exerciseFilter.value),
    ),
    error_by_exercise: charts.error_by_exercise.filter(
      (c) => c.name === exerciseName(exerciseFilter.value),
    ),
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
    ? `${exerciseName(exerciseFilter.value)} · ${t("scoreTrends.recent7DayScoreTrend")}`
    : t("scoreTrends.allExercisesScoreTrend"),
);

const radarSubtitle = computed(() =>
  exerciseFilter.value
    ? `${exerciseName(exerciseFilter.value)} ${t("scoreTrends.qualityDimension")}`
    : t("scoreTrends.qualityAssessment"),
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

const exerciseTrendCards = computed(() => {
  const trends = personalReport.value?.exercise_trends
    || personalReport.value?.charts?.score_trend_by_exercise
    || [];
  if (exerciseFilter.value) {
    return trends.filter((t) => t.exercise === exerciseFilter.value);
  }
  return trends.length ? trends : EXERCISE_OPTIONS.map((ex) => ({
    exercise: ex.key,
    name: ex.name,
    trend: [] as { date: string; score: number }[],
  }));
});

const stats = computed(() => {
  const report = personalReport.value;
  const trend = report?.trend || [];
  const trendScores = trend.map((d) => d.score);
  const scoreDelta = trendScores.length >= 2
    ? Math.round((trendScores[trendScores.length - 1] - trendScores[0]) * 10) / 10
    : 0;
  return [
    {
      label: t("scoreTrends.currentAvgScore"),
      value: report?.average_score ?? "--",
      hint: exerciseFilter.value ? exerciseName(exerciseFilter.value) : t("scoreTrends.allExercises"),
      tone: "",
    },
    {
      label: t("scoreTrends.trendChange"),
      value: trendScores.length >= 2 ? `${scoreDelta >= 0 ? "+" : ""}${scoreDelta}` : "--",
      hint: t("scoreTrends.weekComparison"),
      tone: scoreDelta >= 0 ? "tone-text-green" : "",
    },
    {
      label: t("scoreTrends.totalCalories"),
      value: `${report?.total_calories ?? 0} kcal`,
      hint: t("scoreTrends.estimatedCalories"),
      tone: "tone-text-orange",
    },
    {
      label: t("scoreTrends.totalSessions"),
      value: report?.total_sessions ?? 0,
      hint: rangePreset.value === "7d" ? t("scoreTrends.last7Days") : t("scoreTrends.allTime"),
      tone: "",
    },
  ];
});

function exerciseName(key: string): string {
  const exerciseNames: Record<string, string> = {
    squat: t("exercises.squat"),
    push_up: t("exercises.push_up"),
    jumping_jack: t("exercises.jumping_jack"),
    plank: t("exercises.plank"),
  };
  return exerciseNames[key] ?? key;
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
    legend: { data: [t("scoreTrends.tableHead_avgScore"), t("scoreTrends.tableHead_latestScore"), t("scoreTrends.tableHead_bestScore")], textStyle: { color: "#94a3b8" } },
    grid: { left: 40, right: 20, top: 40, bottom: 50 },
    xAxis: {
      type: "category",
      data: rows.map((r) => r.name),
      axisLabel: { color: "#94a3b8" },
    },
    yAxis: { type: "value", max: 100, axisLabel: { color: "#94a3b8" } },
    series: [
      { name: t("scoreTrends.tableHead_avgScore"), type: "bar", data: rows.map((r) => r.avg_score), itemStyle: { color: "#60a5fa" } },
      { name: t("scoreTrends.tableHead_latestScore"), type: "bar", data: rows.map((r) => r.latest_score ?? r.avg_score), itemStyle: { color: "#34d399" } },
      { name: t("scoreTrends.tableHead_bestScore"), type: "bar", data: rows.map((r) => r.best_score ?? r.avg_score), itemStyle: { color: "#f59e0b" } },
    ],
  });
}

async function loadData() {
  loading.value = true;
  loadError.value = "";
  try {
    personalReport.value = await getPersonalReport({
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      exercise: exerciseFilter.value || undefined,
    });
  } catch (err: unknown) {
    loadError.value = err instanceof Error ? err.message : t("scoreTrends.loadFailed");
  } finally {
    loading.value = false;
    await nextTick();
    renderComparisonChart();
  }
}

watch(comparisonRows, () => nextTick().then(renderComparisonChart));

onMounted(() => {
  applyRange();
});
onActivated(loadData);
onBeforeUnmount(() => {
  comparisonChart?.dispose();
});
</script>

<style scoped>
.score-trends-page { display: grid; gap: 24px; }
.trend-filter-card { display: flex; gap: 16px; flex-wrap: wrap; padding: 16px 20px; border-radius: 12px; background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); }
.trend-filter-card label { display: grid; gap: 6px; color: #94a3b8; font-size: 12px; }
.trend-filter-card select { padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(59,130,246,0.15); background: rgba(8,13,26,0.8); color: #f8fafc; }
.trend-load-error { color: #f87171; font-size: 13px; margin: 0; }
.comparison-card { display: grid; gap: 16px; }
.comparison-table-wrap { overflow-x: auto; }
.comparison-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.comparison-table th, .comparison-table td { padding: 10px 12px; border-bottom: 1px solid rgba(59,130,246,0.08); color: #cbd5e1; text-align: left; }
.comparison-table th { color: #64748b; font-size: 11px; }
.comparison-chart { width: 100%; height: 280px; }
.exercise-trend-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.trend-mini-card { padding: 14px; border-radius: 10px; background: rgba(8,13,26,0.5); border: 1px solid rgba(59,130,246,0.08); }
.trend-mini-card header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.trend-mini-card header strong { color: #f8fafc; }
.trend-mini-card header span { color: #64748b; font-size: 11px; }
.trend-mini-card ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
.trend-mini-card li { display: flex; justify-content: space-between; color: #94a3b8; font-size: 12px; }
.trend-mini-card b { color: #60a5fa; }
.empty-hint { color: #64748b; font-size: 12px; margin: 0; }
</style>
