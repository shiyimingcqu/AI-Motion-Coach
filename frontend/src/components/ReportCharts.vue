<template>
  <section class="report-charts">
    <article v-if="showTrend" class="chart-card wide">
      <header>
        <h3>7日评分趋势 / 7-Day Score Trend</h3>
        <span>{{ trendSubtitle }}</span>
      </header>
      <div ref="trendRef" class="chart-box" />
    </article>

    <div class="chart-row">
      <article class="chart-card">
        <header>
          <h3>卡路里消耗 / Calories</h3>
          <span>按动作类型统计</span>
        </header>
        <div ref="calorieRef" class="chart-box" />
      </article>

      <article class="chart-card">
        <header>
          <h3>训练分布 / Distribution</h3>
          <span>各动作训练次数占比</span>
        </header>
        <div ref="pieRef" class="chart-box" />
      </article>
    </div>

    <div class="chart-row">
      <article class="chart-card">
        <header>
          <h3>动作质量雷达 / Quality Radar</h3>
          <span>{{ radarSubtitle }}</span>
        </header>
        <div ref="radarRef" class="chart-box radar-box" />
      </article>

      <article class="chart-card">
        <header>
          <h3>错误统计 / Errors</h3>
          <span>各动作需改进次数</span>
        </header>
        <div ref="errorRef" class="chart-box" />
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import type { ChartData } from "@/api/reports";

export interface TrendSeriesItem {
  name: string;
  trend: { date: string; score: number }[];
}

const props = withDefaults(
  defineProps<{
    charts: ChartData;
    showTrend?: boolean;
    trendSeries?: TrendSeriesItem[];
    radarSubtitle?: string;
    trendSubtitle?: string;
  }>(),
  {
    showTrend: true,
    trendSeries: () => [],
    radarSubtitle: "综合各维度动作质量评估",
    trendSubtitle: "近 7 日训练平均分变化（可按动作区分）",
  },
);

const trendRef = ref<HTMLElement | null>(null);
const calorieRef = ref<HTMLElement | null>(null);
const pieRef = ref<HTMLElement | null>(null);
const radarRef = ref<HTMLElement | null>(null);
const errorRef = ref<HTMLElement | null>(null);

const instances: echarts.ECharts[] = [];
const lineColors = ["#60a5fa", "#34d399", "#f59e0b", "#a78bfa", "#f87171", "#22d3ee"];

const chartTheme = {
  backgroundColor: "transparent",
  textStyle: { color: "#94a3b8", fontFamily: "system-ui, sans-serif" },
};

function initChart(el: HTMLElement | null, option: echarts.EChartsOption) {
  if (!el) return;
  const chart = echarts.init(el, undefined, { renderer: "canvas" });
  chart.setOption(option);
  instances.push(chart);
}

function buildTrendOption() {
  const seriesList = props.trendSeries?.length
    ? props.trendSeries
    : [{ name: "综合", trend: props.charts.score_trend }];

  const allDates = [
    ...new Set(seriesList.flatMap((s) => s.trend.map((p) => p.date))),
  ].sort();

  const series = seriesList
    .filter((s) => s.trend.length > 0)
    .map((item, index) => ({
      name: item.name,
      type: "line" as const,
      smooth: true,
      symbol: "circle",
      symbolSize: 7,
      data: allDates.map((date) => {
        const point = item.trend.find((p) => p.date === date);
        return point ? point.score : null;
      }),
      lineStyle: { color: lineColors[index % lineColors.length], width: 2.5 },
      itemStyle: { color: lineColors[index % lineColors.length] },
      connectNulls: true,
    }));

  return {
    ...chartTheme,
    animationDuration: 1200,
    legend: series.length > 1 ? { top: 0, textStyle: { color: "#94a3b8" } } : undefined,
    grid: { left: 48, right: 24, top: series.length > 1 ? 40 : 36, bottom: 36 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.95)",
      borderColor: "rgba(59,130,246,0.3)",
    },
    xAxis: {
      type: "category" as const,
      data: allDates.map((d) => d.slice(5)),
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#94a3b8" },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.08)" } },
      axisLabel: { color: "#94a3b8" },
    },
    series,
  };
}

function buildOptions(data: ChartData) {
  const calorieOption: echarts.EChartsOption = {
    ...chartTheme,
    grid: { left: 48, right: 24, top: 36, bottom: 56 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category" as const,
      data: data.calorie_by_exercise.map((item) => item.name),
      axisLabel: { color: "#94a3b8", rotate: 15, fontSize: 11 },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#94a3b8", formatter: "{value} kcal" },
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.08)" } },
    },
    series: [{
      type: "bar",
      data: data.calorie_by_exercise.map((item) => item.value),
      itemStyle: { borderRadius: [8, 8, 0, 0], color: "#f59e0b" },
      barWidth: "48%",
    }],
  };

  const pieOption: echarts.EChartsOption = {
    ...chartTheme,
    tooltip: { trigger: "item", formatter: "{b}<br/>{c} 次 · {d}%" },
    legend: { bottom: 0, textStyle: { color: "#94a3b8", fontSize: 11 } },
    series: [{
      type: "pie",
      radius: ["46%", "72%"],
      center: ["50%", "44%"],
      data: data.exercise_distribution,
      label: { color: "#e2e8f0", fontSize: 11 },
      color: ["#3b82f6", "#8b5cf6", "#14b8a6", "#f59e0b"],
    }],
  };

  const radarOption: echarts.EChartsOption = {
    ...chartTheme,
    radar: {
      indicator: data.quality_radar.dimensions.map((name) => ({ name, max: 100 })),
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.15)" } },
      axisName: { color: "#cbd5e1", fontSize: 11 },
    },
    series: [{
      type: "radar",
      data: [{
        value: data.quality_radar.values,
        areaStyle: { color: "rgba(96,165,250,0.25)" },
        lineStyle: { color: "#60a5fa" },
      }],
    }],
  };

  const errorOption: echarts.EChartsOption = {
    ...chartTheme,
    grid: { left: 48, right: 24, top: 36, bottom: 56 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category" as const,
      data: (data.error_by_exercise || []).map((item) => item.name),
      axisLabel: { color: "#94a3b8", rotate: 15 },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#94a3b8" },
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.08)" } },
    },
    series: [{
      type: "bar",
      data: (data.error_by_exercise || []).map((item) => item.value),
      itemStyle: { color: "#ef4444", borderRadius: [6, 6, 0, 0] },
      barWidth: "45%",
    }],
  };

  return { calorieOption, pieOption, radarOption, errorOption };
}

function renderCharts() {
  instances.splice(0).forEach((chart) => chart.dispose());

  const hasData =
    props.charts.score_trend.length > 0
    || props.trendSeries.some((s) => s.trend.length > 0)
    || props.charts.calorie_by_exercise.length > 0;

  if (!hasData) return;

  if (props.showTrend) {
    initChart(trendRef.value, buildTrendOption());
  }
  const options = buildOptions(props.charts);
  initChart(calorieRef.value, options.calorieOption);
  initChart(pieRef.value, options.pieOption);
  initChart(radarRef.value, options.radarOption);
  initChart(errorRef.value, options.errorOption);
}

function handleResize() {
  instances.forEach((chart) => chart.resize());
}

watch(() => [props.charts, props.trendSeries, props.showTrend], renderCharts, { deep: true });

onMounted(() => {
  renderCharts();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  instances.forEach((chart) => chart.dispose());
});
</script>

<style scoped>
.report-charts { display: grid; gap: 16px; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-card {
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  border: 1px solid rgba(59, 130, 246, 0.14);
}
.chart-card.wide { grid-column: 1 / -1; }
.chart-card header { display: grid; gap: 4px; margin-bottom: 12px; }
.chart-card h3 { margin: 0; color: #f8fafc; font-size: 15px; }
.chart-card span { color: #64748b; font-size: 12px; }
.chart-box { width: 100%; height: 260px; }
.radar-box { height: 280px; }
@media (max-width: 900px) { .chart-row { grid-template-columns: 1fr; } }
</style>
