<template>
  <section class="report-charts">
    <article class="chart-card wide">
      <header>
        <h3>评分趋势 / Score Trend</h3>
        <span>近 7 日训练平均分变化</span>
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

    <article class="chart-card wide">
      <header>
        <h3>动作质量雷达 / Quality Radar</h3>
        <span>综合各维度动作质量评估</span>
      </header>
      <div ref="radarRef" class="chart-box radar-box" />
    </article>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import type { ChartData } from "@/api/reports";

const props = defineProps<{
  charts: ChartData;
  compact?: boolean;
}>();

const trendRef = ref<HTMLElement | null>(null);
const calorieRef = ref<HTMLElement | null>(null);
const pieRef = ref<HTMLElement | null>(null);
const radarRef = ref<HTMLElement | null>(null);

const instances: echarts.ECharts[] = [];

function initChart(el: HTMLElement | null, option: echarts.EChartsOption) {
  if (!el) return;
  const chart = echarts.init(el, undefined, { renderer: "canvas" });
  chart.setOption(option);
  instances.push(chart);
}

function buildOptions(data: ChartData) {
  const chartTheme = {
    backgroundColor: "transparent",
    textStyle: { color: "#94a3b8", fontFamily: "system-ui, sans-serif" },
  };

  const trendOption: echarts.EChartsOption = {
    ...chartTheme,
    animationDuration: 1200,
    animationEasing: "cubicOut",
    grid: { left: 48, right: 24, top: 36, bottom: 36 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.95)",
      borderColor: "rgba(59,130,246,0.3)",
      textStyle: { color: "#e2e8f0" },
    },
    xAxis: {
      type: "category",
      data: data.score_trend.map((item) => item.date.slice(5)),
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#94a3b8" },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.08)" } },
      axisLabel: { color: "#94a3b8" },
    },
    series: [{
      type: "line",
      smooth: true,
      symbol: "circle",
      symbolSize: 8,
      data: data.score_trend.map((item) => item.score),
      lineStyle: { color: "#60a5fa", width: 3, shadowColor: "rgba(96,165,250,0.4)", shadowBlur: 12 },
      itemStyle: { color: "#93c5fd", borderColor: "#1e3a8a", borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(96,165,250,0.45)" },
          { offset: 0.6, color: "rgba(59,130,246,0.12)" },
          { offset: 1, color: "rgba(59,130,246,0.01)" },
        ]),
      },
    }],
  };

  const calorieOption: echarts.EChartsOption = {
    ...chartTheme,
    animationDuration: 1000,
    grid: { left: 48, right: 24, top: 36, bottom: 56 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.95)",
      borderColor: "rgba(245,158,11,0.3)",
      formatter: (p: unknown) => {
        const items = Array.isArray(p) ? p : [p];
        const item = items[0] as { name: string; value: number };
        return `${item.name}<br/>消耗 <b>${item.value}</b> kcal`;
      },
    },
    xAxis: {
      type: "category",
      data: data.calorie_by_exercise.map((item) => item.name),
      axisLabel: { color: "#94a3b8", rotate: 20, fontSize: 11 },
      axisLine: { lineStyle: { color: "#334155" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#94a3b8", formatter: "{value} kcal" },
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.08)" } },
    },
    series: [{
      type: "bar",
      data: data.calorie_by_exercise.map((item) => item.value),
      itemStyle: {
        color: (params: { dataIndex: number }) => {
          const palette = ["#f59e0b", "#fb923c", "#f97316", "#ef4444", "#ec4899"];
          return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: palette[params.dataIndex % palette.length] },
            { offset: 1, color: "rgba(239,68,68,0.6)" },
          ]);
        },
        borderRadius: [8, 8, 0, 0],
        shadowColor: "rgba(245,158,11,0.3)",
        shadowBlur: 8,
      },
      barWidth: "48%",
    }],
  };

  const pieOption: echarts.EChartsOption = {
    ...chartTheme,
    animationDuration: 1000,
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.95)",
      formatter: "{b}<br/>{c} 次 · {d}%",
    },
    legend: {
      bottom: 0,
      textStyle: { color: "#94a3b8", fontSize: 11 },
    },
    series: [{
      type: "pie",
      radius: ["46%", "72%"],
      center: ["50%", "44%"],
      data: data.exercise_distribution,
      label: { color: "#e2e8f0", fontSize: 11, formatter: "{b}\n{d}%" },
      itemStyle: { borderRadius: 8, borderColor: "#0f172a", borderWidth: 3 },
      color: ["#3b82f6", "#8b5cf6", "#14b8a6", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"],
      emphasis: {
        scale: true,
        scaleSize: 8,
        itemStyle: { shadowBlur: 16, shadowColor: "rgba(59,130,246,0.4)" },
      },
    }],
  };

  const radarOption: echarts.EChartsOption = {
    ...chartTheme,
    animationDuration: 1200,
    tooltip: { backgroundColor: "rgba(15,23,42,0.95)" },
    radar: {
      indicator: data.quality_radar.dimensions.map((name) => ({ name, max: 100 })),
      shape: "polygon",
      splitNumber: 4,
      splitLine: { lineStyle: { color: "rgba(59,130,246,0.15)" } },
      splitArea: {
        areaStyle: {
          color: ["rgba(59,130,246,0.04)", "rgba(59,130,246,0.08)", "rgba(59,130,246,0.04)", "rgba(59,130,246,0.08)"],
        },
      },
      axisLine: { lineStyle: { color: "rgba(59,130,246,0.2)" } },
      axisName: { color: "#cbd5e1", fontSize: 12, fontWeight: 600 },
    },
    series: [{
      type: "radar",
      data: [{
        value: data.quality_radar.values,
        name: "动作质量",
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { offset: 0, color: "rgba(96,165,250,0.5)" },
            { offset: 1, color: "rgba(59,130,246,0.05)" },
          ]),
        },
        lineStyle: { color: "#60a5fa", width: 2.5 },
        itemStyle: { color: "#93c5fd", borderColor: "#1e40af", borderWidth: 2 },
      }],
    }],
  };

  return { trendOption, calorieOption, pieOption, radarOption };
}

function renderCharts() {
  instances.splice(0).forEach((chart) => chart.dispose());

  const hasData = props.charts.score_trend.length > 0
    || props.charts.calorie_by_exercise.length > 0;

  if (!hasData) return;

  const options = buildOptions(props.charts);
  initChart(trendRef.value, options.trendOption);
  initChart(calorieRef.value, options.calorieOption);
  initChart(pieRef.value, options.pieOption);
  initChart(radarRef.value, options.radarOption);
}

function handleResize() {
  instances.forEach((chart) => chart.resize());
}

watch(() => props.charts, renderCharts, { deep: true });

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
.report-charts {
  display: grid;
  gap: 16px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-card {
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  border: 1px solid rgba(59, 130, 246, 0.14);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  position: relative;
  overflow: hidden;
}

.chart-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.5), rgba(139,92,246,0.5), transparent);
}

.chart-card.wide {
  grid-column: 1 / -1;
}

.chart-card header {
  display: grid;
  gap: 4px;
  margin-bottom: 12px;
}

.chart-card h3 {
  margin: 0;
  color: #f8fafc;
  font-size: 15px;
}

.chart-card span {
  color: #64748b;
  font-size: 12px;
}

.chart-box {
  width: 100%;
  height: 240px;
}

.radar-box {
  height: 280px;
}

@media (max-width: 900px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}
</style>
