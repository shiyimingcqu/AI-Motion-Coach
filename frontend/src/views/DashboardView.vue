<template>
  <div class="dashboard-page">
    <section class="dashboard-metrics">
      <article
        v-for="metric in metrics"
        :key="metric.label"
        class="dashboard-metric-card"
      >
        <span class="metric-icon" :class="metric.tone">
          <component :is="metric.icon" :size="25" />
        </span>
        <div>
          <p>{{ metric.label }}</p>
          <strong>{{ metric.value }}</strong>
          <small>{{ metric.hint }}</small>
        </div>
      </article>
    </section>

    <section class="dashboard-chart-grid">
      <article class="dashboard-card">
        <header class="dashboard-card-header">
          <h2>Weekly Score Trend / 本周分数趋势</h2>
        </header>
        <div ref="scoreChartRef" class="echart-panel" />
      </article>

      <article class="dashboard-card">
        <header class="dashboard-card-header">
          <h2>Training Sessions / 训练次数</h2>
        </header>
        <div ref="sessionsChartRef" class="echart-panel" />
      </article>
    </section>

    <section class="dashboard-bottom-grid">
      <article class="dashboard-card dashboard-table-card">
        <header class="dashboard-card-header">
          <h2>Recent Evaluations / 最近评估</h2>
        </header>
        <table class="evaluation-table">
          <thead>
            <tr>
              <th>User / 用户</th>
              <th>Exercise / 动作</th>
              <th>Score / 分数</th>
              <th>Time / 时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recentEvaluations" :key="item.user">
              <td>{{ item.user }}</td>
              <td>{{ item.exercise }}</td>
              <td>
                <span class="score-badge" :class="scoreTone(item.score)">
                  {{ item.score }}
                </span>
              </td>
              <td>
                <span class="time-cell">
                  <Clock3 :size="14" />
                  {{ item.time }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="dashboard-card">
        <header class="dashboard-card-header">
          <h2>Exercise Distribution / 动作分布</h2>
        </header>
        <div ref="distributionChartRef" class="donut-panel" />
        <div class="distribution-legend">
          <div v-for="item in exerciseDistribution" :key="item.name">
            <span>
              <i :style="{ backgroundColor: item.color }" />
              {{ item.name }}
            </span>
            <strong>{{ item.value }}%</strong>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import {
  Activity,
  Clock3,
  Target,
  TrendingUp,
  UsersRound
} from "lucide-vue-next";

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer
]);

const scoreChartRef = ref<HTMLDivElement | null>(null);
const sessionsChartRef = ref<HTMLDivElement | null>(null);
const distributionChartRef = ref<HTMLDivElement | null>(null);
const chartInstances: echarts.ECharts[] = [];

const metrics = [
  {
    label: "Today's Training / 今日训练",
    value: "3",
    hint: "sessions",
    icon: Activity,
    tone: "tone-blue"
  },
  {
    label: "Active Users / 活跃用户",
    value: "127",
    hint: "users",
    icon: UsersRound,
    tone: "tone-green"
  },
  {
    label: "Avg. Score / 平均分数",
    value: "87.5",
    hint: "points",
    icon: Target,
    tone: "tone-purple"
  },
  {
    label: "Improvement / 进步率",
    value: "+12%",
    hint: "this week",
    icon: TrendingUp,
    tone: "tone-orange"
  }
];

const recentEvaluations = [
  { user: "Zhang Wei / 张伟", exercise: "Squat / 深蹲", score: 92, time: "14:30" },
  { user: "Li Na / 李娜", exercise: "Push-up / 俯卧撑", score: 85, time: "14:15" },
  { user: "Wang Ming / 王明", exercise: "Plank / 平板支撑", score: 78, time: "13:45" },
  { user: "Chen Jing / 陈静", exercise: "Lunge / 弓步蹲", score: 88, time: "13:20" }
];

const exerciseDistribution = [
  { name: "Squat / 深蹲", value: 35, color: "#4f7df3" },
  { name: "Push-up / 俯卧撑", value: 25, color: "#2eba83" },
  { name: "Plank / 平板支撑", value: 20, color: "#f2a21a" },
  { name: "Lunge / 弓步蹲", value: 15, color: "#8a55ed" },
  { name: "Others / 其他", value: 5, color: "#7d8491" }
];

function scoreTone(score: number) {
  if (score >= 90) return "score-good";
  if (score >= 85) return "score-blue";
  return "score-warn";
}

function createChart(element: HTMLDivElement, option: echarts.EChartsCoreOption) {
  const chart = echarts.init(element);
  chart.setOption(option);
  chartInstances.push(chart);
}

function resizeCharts() {
  chartInstances.forEach((chart) => chart.resize());
}

onMounted(() => {
  if (scoreChartRef.value) {
    createChart(scoreChartRef.value, {
      color: ["#4f7df3"],
      grid: { left: 58, right: 28, top: 24, bottom: 42 },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        axisLine: { lineStyle: { color: "#c9d1dc" } },
        axisTick: { show: false },
        axisLabel: { color: "#9aa3b2", fontSize: 14 }
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        interval: 25,
        splitLine: { lineStyle: { color: "#edf0f5", type: "dashed" } },
        axisLabel: { color: "#9aa3b2", fontSize: 14 }
      },
      series: [
        {
          type: "line",
          smooth: true,
          symbolSize: 11,
          lineStyle: { width: 3 },
          data: [74, 78, 82, 85, 87, 89, 91]
        }
      ]
    });
  }

  if (sessionsChartRef.value) {
    createChart(sessionsChartRef.value, {
      color: ["#2eba83"],
      grid: { left: 58, right: 28, top: 24, bottom: 42 },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        axisLine: { lineStyle: { color: "#c9d1dc" } },
        axisTick: { show: false },
        axisLabel: { color: "#9aa3b2", fontSize: 14 }
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 20,
        interval: 5,
        splitLine: { lineStyle: { color: "#edf0f5", type: "dashed" } },
        axisLabel: { color: "#9aa3b2", fontSize: 14 }
      },
      series: [
        {
          type: "bar",
          barWidth: 78,
          itemStyle: { borderRadius: [8, 8, 0, 0] },
          data: [12, 15, 18, 14, 16, 20, 17]
        }
      ]
    });
  }

  if (distributionChartRef.value) {
    createChart(distributionChartRef.value, {
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["52%", "78%"],
          avoidLabelOverlap: true,
          label: { show: false },
          labelLine: { show: false },
          itemStyle: {
            borderColor: "#ffffff",
            borderWidth: 5
          },
          data: exerciseDistribution.map((item) => ({
            value: item.value,
            name: item.name,
            itemStyle: { color: item.color }
          }))
        }
      ]
    });
  }

  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  chartInstances.forEach((chart) => chart.dispose());
});
</script>
