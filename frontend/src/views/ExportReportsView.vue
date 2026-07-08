<template>
  <div class="report-page">
    <header class="report-hero">
      <div class="hero-copy">
        <h1>我的报告</h1>
        <p>全面分析你的训练表现，帮助你更科学地进步</p>
      </div>

      <div class="hero-stats">
        <div class="hero-stat violet">
          <div class="hero-stat__icon"><Calendar :size="18" /></div>
          <div>
            <span>本月训练</span>
            <strong>{{ monthSessions }}<small>次</small></strong>
          </div>
        </div>
        <div class="hero-stat orange">
          <div class="hero-stat__icon"><Flame :size="18" /></div>
          <div>
            <span>累计训练</span>
            <strong>{{ totalDays }}<small>天</small></strong>
          </div>
        </div>
        <div class="hero-stat blue">
          <div class="hero-stat__icon"><Star :size="18" /></div>
          <div>
            <span>平均得分</span>
            <strong>{{ avgScore }}<small>分</small></strong>
          </div>
        </div>
      </div>
    </header>

    <section class="toolbar">
      <div class="toolbar-left">
        <select v-model="exerciseFilter" class="toolbar-select">
          <option value="">全部动作</option>
          <option v-for="(meta, key) in EXERCISE_META" :key="key" :value="key">
            {{ meta.name }}
          </option>
        </select>

        <div class="toolbar-ranges">
          <button
            v-for="item in ranges"
            :key="item.key"
            type="button"
            class="range-btn"
            :class="{ active: rangeKey === item.key }"
            @click="rangeKey = item.key"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <button class="export-btn" type="button" @click="exportReport">
        <Download :size="16" />
        <span>导出报告</span>
      </button>
    </section>

    <section class="summary-grid">
      <article class="card score-card">
        <span class="card-kicker">综合表现</span>
        <div class="score-main">
          <div>
            <div class="score-value">
              <strong>{{ avgScore }}</strong>
              <small>分</small>
            </div>
            <div class="score-badge">{{ scoreLevel.label }}</div>
            <p class="score-copy">超过了 {{ outperformPct }}% 的同阶段用户</p>
            <div class="score-progress">
              <i :style="{ width: `${Math.min(avgScore, 100)}%` }"></i>
            </div>
          </div>
          <div class="score-figure">
            <img src="/exercises/squat.png" alt="综合表现示意" />
          </div>
        </div>
        <p class="score-footnote">继续保持，你的进步很明显。</p>
      </article>

      <article class="card radar-card">
        <header class="section-head">
          <strong>能力雷达图</strong>
        </header>
        <div ref="radarRef" class="radar-chart"></div>
      </article>

      <article class="card metrics-card">
        <header class="section-head">
          <strong>关键数据</strong>
        </header>
        <ul class="metrics-list">
          <li v-for="metric in metrics" :key="metric.label">
            <div class="metrics-icon" :style="{ background: metric.bg, color: metric.color }">
              <component :is="metric.icon" :size="16" />
            </div>
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}<small v-if="metric.unit">{{ metric.unit }}</small></strong>
          </li>
        </ul>
      </article>
    </section>

    <section class="content-grid">
      <article class="card trend-card">
        <header class="section-head">
          <strong>表现趋势</strong>
        </header>
        <div ref="trendRef" class="trend-chart"></div>
      </article>

      <article class="card dist-card">
        <header class="section-head">
          <strong>动作训练分布</strong>
        </header>
        <div ref="distRef" class="dist-chart"></div>
        <ul class="dist-list">
          <li v-for="item in distributionItems" :key="item.name">
            <span class="dist-dot" :style="{ background: item.color }"></span>
            <span class="dist-name">{{ item.name }}</span>
            <span class="dist-pct">{{ item.pct }}%</span>
            <span class="dist-count">{{ item.count }}次</span>
          </li>
        </ul>
      </article>

      <article class="card analysis-card">
        <header class="section-head">
          <div>
            <strong>动作分析</strong>
            <span>最近{{ rangeDays }}天表现</span>
          </div>
        </header>

        <ul class="exercise-list">
          <li v-for="item in exerciseAnalysis" :key="item.key">
            <div class="exercise-cover" :style="{ background: item.accent }">
              <img :src="`/exercises/${item.key}.png`" :alt="item.name" />
            </div>

            <div class="exercise-meta">
              <div class="exercise-title">
                <strong>{{ item.name }}</strong>
                <span>训练 {{ item.count }} 次</span>
              </div>
              <div class="exercise-scoreline">
                <b>{{ item.score }}</b>
                <small>分</small>
                <em :class="item.gradeClass">{{ item.grade }}</em>
              </div>
            </div>

            <div class="exercise-stats">
              <div class="mini-stat">
                <span>动作完成率</span>
                <div class="mini-bar">
                  <i :style="{ width: `${item.completion}%` }"></i>
                </div>
                <strong>{{ item.completion }}%</strong>
              </div>
              <div class="mini-stat">
                <span>平均时长</span>
                <strong>{{ formatTime(item.duration) }}</strong>
              </div>
              <div class="mini-stat">
                <span>消耗热量</span>
                <strong>{{ item.calories }}<small> 千卡</small></strong>
              </div>
            </div>

            <button class="row-arrow" type="button" @click="router.push('/sessions')">
              <ChevronRight :size="18" />
            </button>
          </li>
        </ul>
      </article>

      <article class="card compare-card">
        <header class="section-head">
          <strong>深蹲动作对比</strong>
        </header>
        <div class="compare-legend">
          <span><i class="legend-dot purple"></i>你的动作</span>
          <span><i class="legend-dot green"></i>标准动作</span>
        </div>
        <div class="compare-stage">
          <img src="/exercises/squat.png" alt="深蹲对比示意" />
        </div>
        <div class="compare-score">
          <span>整体相似度</span>
          <strong>{{ similarityScore }}%</strong>
        </div>
        <ul class="compare-points">
          <li v-for="point in squatPoints" :key="point.title">
            <span class="point-mark" :class="point.status"></span>
            <span>{{ point.title }}：{{ point.text }}</span>
          </li>
        </ul>
        <button class="primary-side-btn" type="button" @click="router.push('/sessions')">
          查看详细对比
        </button>
      </article>

      <article class="card problems-card">
        <header class="section-head">
          <strong>常见问题</strong>
        </header>

        <ul class="problem-list">
          <li v-for="(problem, index) in commonProblems" :key="problem.title">
            <div class="problem-index">{{ index + 1 }}</div>
            <div class="problem-copy">
              <strong>{{ problem.title }}</strong>
              <p>{{ problem.desc }}</p>
            </div>
            <div class="problem-exercise">
              <span>建议动作</span>
              <strong>{{ problem.suggest }}</strong>
            </div>
            <button class="problem-btn" type="button" @click="router.push('/exercises')">
              去练习
            </button>
          </li>
        </ul>
      </article>

      <article class="card suggest-card">
        <header class="section-head">
          <strong>进步建议</strong>
        </header>

        <ul class="suggest-list">
          <li v-for="item in suggestions" :key="item.title">
            <div class="suggest-icon" :style="{ background: item.bg, color: item.fg }">
              <component :is="item.icon" :size="18" />
            </div>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </li>
        </ul>

        <div class="coach-banner">
          <div class="coach-copy">
            <span>你已经很棒了！</span>
            <p>继续保持，节奏稳住，好的变化会越来越明显。</p>
          </div>
          <img src="/exercises/high_knees.png" alt="训练鼓励插图" />
        </div>
      </article>

      <article class="card goal-card">
        <header class="section-head">
          <div>
            <strong>下一个目标</strong>
            <span>让我们一起设定新的目标，继续突破自己</span>
          </div>
        </header>

        <div class="goal-items">
          <div class="goal-item">
            <div class="goal-icon violet"><Calendar :size="18" /></div>
            <div>
              <span>训练目标</span>
              <strong>每周训练 4 次</strong>
            </div>
          </div>
          <div class="goal-item">
            <div class="goal-icon blue"><Target :size="18" /></div>
            <div>
              <span>得分目标</span>
              <strong>平均得分 85 分</strong>
            </div>
          </div>
          <div class="goal-item">
            <div class="goal-icon orange"><Timer :size="18" /></div>
            <div>
              <span>时长目标</span>
              <strong>每次 60 分钟</strong>
            </div>
          </div>
          <button class="goal-btn" type="button" @click="router.push('/profile')">
            设定新目标
          </button>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import {
  Activity,
  Calendar,
  ChevronRight,
  CircleCheckBig,
  Download,
  Flame,
  Heart,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  Timer,
} from "lucide-vue-next";
import { getDashboardStats } from "@/api/dashboard";
import { getSessions, type SessionRecord } from "@/api/sessions";
import { EXERCISE_META, getDateKey, getScoreLevel } from "@/data/trainingRecords";

const router = useRouter();

const rangeKey = ref<"7" | "30" | "90">("30");
const exerciseFilter = ref("");
const monthSessions = ref(12);
const totalDays = ref(36);
const avgScore = ref(78);
const totalSessions = ref(12);
const totalHours = ref(6.2);
const completionRate = ref(92);
const totalCalories = ref(3260);
const similarityScore = ref(82);
const sessions = ref<SessionRecord[]>([]);

const radarRef = ref<HTMLElement | null>(null);
const trendRef = ref<HTMLElement | null>(null);
const distRef = ref<HTMLElement | null>(null);

let charts: echarts.ECharts[] = [];

const ranges = [
  { key: "7" as const, label: "近7天" },
  { key: "30" as const, label: "近30天" },
  { key: "90" as const, label: "近90天" },
];

const rangeDays = computed(() => Number.parseInt(rangeKey.value, 10));

const filteredSessions = computed(() => {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - rangeDays.value);

  return sessions.value.filter((item) => {
    const inRange = new Date(item.created_at) >= cutoff;
    const matchedExercise = !exerciseFilter.value || item.exercise === exerciseFilter.value;
    return inRange && matchedExercise;
  });
});

const scoreLevel = computed(() => getScoreLevel(avgScore.value));
const outperformPct = computed(() => Math.max(55, Math.min(96, Math.round(avgScore.value * 0.87))));

const metrics = computed(() => [
  { label: "总训练次数", value: totalSessions.value, unit: "次", icon: Calendar, bg: "#f1ebff", color: "#7c5cff" },
  { label: "总训练时长", value: totalHours.value, unit: "小时", icon: Timer, bg: "#e9fbef", color: "#22a75a" },
  { label: "平均得分", value: avgScore.value, unit: "分", icon: Star, bg: "#ebf2ff", color: "#467cf4" },
  { label: "动作完成率", value: completionRate.value, unit: "%", icon: Target, bg: "#fff4e8", color: "#ff9a2e" },
  { label: "消耗热量", value: totalCalories.value, unit: "千卡", icon: Flame, bg: "#ffeded", color: "#ff6b4d" },
]);

const exerciseAnalysis = computed(() => {
  const map = new Map<string, {
    key: string;
    name: string;
    count: number;
    totalScore: number;
    totalDuration: number;
    totalCalories: number;
    accent: string;
  }>();

  for (const item of filteredSessions.value) {
    const meta = EXERCISE_META[item.exercise] ?? { name: item.exercise, accent: "#f5f7ff" };
    if (!map.has(item.exercise)) {
      map.set(item.exercise, {
        key: item.exercise,
        name: meta.name,
        count: 0,
        totalScore: 0,
        totalDuration: 0,
        totalCalories: 0,
        accent: meta.accent ?? "#f5f7ff",
      });
    }

    const current = map.get(item.exercise)!;
    current.count += 1;
    current.totalScore += item.average_score;
    current.totalDuration += item.duration_seconds;
    current.totalCalories += Math.max(60, Math.round(item.duration_seconds / 3));
  }

  const fallback = [
    { key: "squat", name: "深蹲", count: 3, score: 82, completion: 95, duration: 80, calories: 320, accent: "#efe9ff" },
    { key: "push_up", name: "俯卧撑", count: 3, score: 76, completion: 90, duration: 65, calories: 280, accent: "#ecfbff" },
    { key: "plank", name: "平板支撑", count: 2, score: 79, completion: 92, duration: 75, calories: 260, accent: "#eef7ff" },
    { key: "jumping_jack", name: "开合跳", count: 2, score: 72, completion: 85, duration: 70, calories: 240, accent: "#fff3e8" },
  ];

  const derived = [...map.values()]
    .map((item) => {
      const score = Math.round(item.totalScore / item.count);
      const level = getScoreLevel(score);
      return {
        key: item.key,
        name: item.name,
        count: item.count,
        score,
        grade: level.label,
        gradeClass:
          level.key === "excellent"
            ? "grade-excellent"
            : level.key === "good"
              ? "grade-good"
              : level.key === "mid"
                ? "grade-mid"
                : "grade-low",
        completion: Math.max(72, Math.min(98, Math.round(score + 12))),
        duration: Math.round(item.totalDuration / item.count),
        calories: Math.round(item.totalCalories / item.count),
        accent: item.accent,
      };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 4);

  return derived.length > 0 ? derived : fallback.map((item) => {
    const level = getScoreLevel(item.score);
    return {
      ...item,
      grade: level.label,
      gradeClass:
        level.key === "excellent"
          ? "grade-excellent"
          : level.key === "good"
            ? "grade-good"
            : level.key === "mid"
              ? "grade-mid"
              : "grade-low",
    };
  });
});

const distributionItems = computed(() => {
  const counts = new Map<string, number>();
  for (const item of filteredSessions.value) {
    counts.set(item.exercise, (counts.get(item.exercise) ?? 0) + 1);
  }

  const source = [...counts.entries()]
    .map(([key, count]) => ({
      key,
      name: EXERCISE_META[key]?.name ?? key,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  const palette = ["#7c5cff", "#4f8cff", "#43c59e", "#ffad42", "#c9ced9"];
  const base = source.length > 0 ? source.slice(0, 5) : [
    { key: "squat", name: "深蹲", count: 3 },
    { key: "push_up", name: "俯卧撑", count: 3 },
    { key: "plank", name: "平板支撑", count: 2 },
    { key: "jumping_jack", name: "开合跳", count: 2 },
    { key: "other", name: "其他", count: 2 },
  ];

  const total = base.reduce((sum, item) => sum + item.count, 0) || 1;

  return base.map((item, index) => ({
    name: item.name,
    count: item.count,
    pct: Math.round((item.count / total) * 100),
    color: palette[index % palette.length],
  }));
});

const squatPoints = [
  { title: "膝盖内扣", status: "mid", text: "轻微" },
  { title: "下蹲深度", status: "good", text: "良好" },
  { title: "核心稳定", status: "good", text: "良好" },
];

const commonProblems = [
  { title: "下蹲深度不足", desc: "你的下蹲深度偏浅，建议继续加强髋关节活动与下肢控制。", suggest: "深蹲拉伸" },
  { title: "膝盖内扣", desc: "下蹲时膝盖向内扣，可能增加受伤风险，需要注意膝尖方向。", suggest: "蛙式深蹲" },
  { title: "核心收紧不足", desc: "核心肌群激活不够，会导致动作过程中的身体稳定性下降。", suggest: "平板支撑" },
  { title: "手臂发力不均衡", desc: "上肢训练中左右侧输出不稳定，建议做更慢一点的控制练习。", suggest: "跪姿俯卧撑" },
];

const suggestions = [
  { title: "保持训练频率", desc: "建议每周进行 3-4 次训练，让动作记忆更稳定。", icon: Activity, bg: "#edf2ff", fg: "#5576ff" },
  { title: "注意动作质量", desc: "宁可少做一点，也要保证每次动作轨迹清晰标准。", icon: CircleCheckBig, bg: "#ebfbef", fg: "#24a860" },
  { title: "加强核心训练", desc: "稳定的核心是你所有动作控制和发力质量的基础。", icon: ShieldCheck, bg: "#fff6df", fg: "#d99214" },
  { title: "合理安排休息", desc: "让身体有足够恢复时间，表现才会继续往上走。", icon: Heart, bg: "#ffedf1", fg: "#ef5a7d" },
];

function formatTime(seconds: number) {
  if (seconds <= 0) return "0秒";
  const minutes = Math.floor(seconds / 60);
  const remain = Math.floor(seconds % 60);
  if (minutes > 0) return `${minutes}分${remain.toString().padStart(2, "0")}秒`;
  return `${remain}秒`;
}

function renderRadar() {
  if (!radarRef.value) return;
  const chart = echarts.init(radarRef.value);
  chart.setOption({
    radar: {
      radius: 88,
      indicator: [
        { name: "核心稳定", max: 100 },
        { name: "下肢力量", max: 100 },
        { name: "动作控制", max: 100 },
        { name: "身体协调", max: 100 },
        { name: "柔韧性", max: 100 },
      ],
      splitNumber: 4,
      splitArea: { areaStyle: { color: ["rgba(124,92,255,0.06)", "rgba(124,92,255,0.02)"] } },
      splitLine: { lineStyle: { color: "rgba(124,92,255,0.14)" } },
      axisLine: { lineStyle: { color: "rgba(124,92,255,0.16)" } },
      axisName: { color: "#5a6476", fontSize: 12, fontWeight: 600 },
    },
    series: [{
      type: "radar",
      symbol: "circle",
      symbolSize: 7,
      lineStyle: { color: "#6e54ff", width: 2.5 },
      areaStyle: { color: "rgba(110,84,255,0.2)" },
      itemStyle: { color: "#6e54ff" },
      data: [{ value: [82, 76, 80, 75, 68] }],
    }],
  });
  charts.push(chart);
}

function renderTrend() {
  if (!trendRef.value) return;
  const chart = echarts.init(trendRef.value);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: {
      top: 0,
      left: 0,
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: "#6f7787", fontSize: 12 },
      data: ["平均得分", "动作完成率", "训练时长(分钟)"],
    },
    grid: { top: 52, left: 26, right: 26, bottom: 22, containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: ["06/10", "06/15", "06/20", "06/25", "06/30", "07/05", "07/08"],
      axisLabel: { color: "#98a2b3", fontSize: 11 },
      axisLine: { lineStyle: { color: "#edf0f7" } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: "value",
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: "#f2f4fa" } },
        axisLabel: { color: "#98a2b3", fontSize: 11 },
      },
      {
        type: "value",
        min: 0,
        max: 100,
        splitLine: { show: false },
        axisLabel: { color: "#98a2b3", fontSize: 11 },
      },
    ],
    series: [
      {
        name: "平均得分",
        type: "line",
        smooth: true,
        data: [62, 75, 83, 74, 71, 79, 78],
        symbolSize: 6,
        lineStyle: { width: 3, color: "#6e54ff" },
        itemStyle: { color: "#6e54ff" },
      },
      {
        name: "动作完成率",
        type: "line",
        smooth: true,
        yAxisIndex: 1,
        data: [28, 52, 54, 79, 68, 86, 92],
        symbolSize: 6,
        lineStyle: { width: 3, color: "#48c488" },
        itemStyle: { color: "#48c488" },
      },
      {
        name: "训练时长(分钟)",
        type: "line",
        smooth: true,
        yAxisIndex: 1,
        data: [36, 25, 44, 35, 49, 60, 53],
        symbolSize: 6,
        lineStyle: { width: 3, color: "#ffac3d" },
        itemStyle: { color: "#ffac3d" },
      },
    ],
  });
  charts.push(chart);
}

function renderDist() {
  if (!distRef.value) return;
  const chart = echarts.init(distRef.value);
  chart.setOption({
    series: [{
      type: "pie",
      radius: ["62%", "82%"],
      center: ["50%", "50%"],
      label: { show: false },
      labelLine: { show: false },
      data: distributionItems.value.map((item) => ({
        value: item.count,
        name: item.name,
        itemStyle: { color: item.color },
      })),
    }],
    graphic: [
      {
        type: "text",
        left: "center",
        top: "41%",
        style: {
          text: String(totalSessions.value),
          fill: "#1a2033",
          fontWeight: 800,
          fontSize: 34,
          textAlign: "center",
        },
      },
      {
        type: "text",
        left: "center",
        top: "56%",
        style: {
          text: "总训练",
          fill: "#8c95a5",
          fontSize: 13,
          textAlign: "center",
        },
      },
    ],
  });
  charts.push(chart);
}

function renderCharts() {
  charts.forEach((chart) => chart.dispose());
  charts = [];
  renderRadar();
  renderTrend();
  renderDist();
}

function exportReport() {
  if (sessions.value.length === 0) {
    window.alert("暂无数据可导出");
    return;
  }

  const header = ["动作", "得分", "时长(秒)", "完成率", "日期"];
  const rows = sessions.value.map((item) => {
    const completion = item.total_count > 0 ? Math.round((item.valid_count / item.total_count) * 100) : 0;
    return [
      EXERCISE_META[item.exercise]?.name ?? item.exercise,
      item.average_score,
      item.duration_seconds,
      `${completion}%`,
      getDateKey(item.created_at),
    ];
  });

  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, "\"\"")}"`).join(","))
    .join("\n");

  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `report-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function loadData() {
  try {
    const [dashboardRes, sessionsRes] = await Promise.allSettled([
      getDashboardStats(),
      getSessions({ limit: 120 }),
    ]);

    if (dashboardRes.status === "fulfilled") {
      const dashboard = dashboardRes.value;
      totalSessions.value = dashboard.total_sessions || totalSessions.value;
      avgScore.value = Math.round(dashboard.average_score || avgScore.value);
      totalHours.value = Number((dashboard.total_duration_minutes / 60).toFixed(1)) || totalHours.value;
      totalCalories.value = Math.round(dashboard.total_duration_minutes * 5.8) || totalCalories.value;
    }

    if (sessionsRes.status === "fulfilled") {
      sessions.value = sessionsRes.value.items || [];
    }

    const daysSet = new Set(sessions.value.map((item) => getDateKey(item.created_at)));
    if (daysSet.size > 0) totalDays.value = daysSet.size;

    const now = new Date();
    monthSessions.value = sessions.value.filter((item) => {
      const date = new Date(item.created_at);
      return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
    }).length || monthSessions.value;

    const totalCount = sessions.value.reduce((sum, item) => sum + item.total_count, 0);
    const validCount = sessions.value.reduce((sum, item) => sum + item.valid_count, 0);
    completionRate.value = totalCount > 0 ? Math.round((validCount / totalCount) * 100) : completionRate.value;

    if (filteredSessions.value.length > 0) {
      const filteredAvg = filteredSessions.value.reduce((sum, item) => sum + item.average_score, 0) / filteredSessions.value.length;
      avgScore.value = Math.round(filteredAvg);
      totalSessions.value = filteredSessions.value.length;
      totalHours.value = Number((filteredSessions.value.reduce((sum, item) => sum + item.duration_seconds, 0) / 3600).toFixed(1));
      totalCalories.value = filteredSessions.value.reduce((sum, item) => sum + Math.max(60, Math.round(item.duration_seconds / 3)), 0);
    }
  } catch (error) {
    console.warn("[reports] load failed", error);
  }

  await nextTick();
  renderCharts();
}

function handleResize() {
  charts.forEach((chart) => chart.resize());
}

watch([rangeKey, exerciseFilter, sessions], async () => {
  await nextTick();
  renderCharts();
}, { deep: true });

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  charts.forEach((chart) => chart.dispose());
  charts = [];
});
</script>

<style scoped>
.report-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
  padding: 4px 0 28px;
}

.report-hero,
.toolbar,
.summary-grid,
.content-grid {
  width: 100%;
}

.report-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.hero-copy h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 900;
  color: #131a2e;
}

.hero-copy p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #6f7787;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.hero-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 150px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(236, 239, 248, 0.95);
  border-radius: 18px;
  box-shadow: 0 14px 34px rgba(130, 139, 171, 0.12);
}

.hero-stat__icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
}

.hero-stat span {
  display: block;
  font-size: 12px;
  color: #7e8798;
}

.hero-stat strong {
  display: flex;
  align-items: baseline;
  gap: 3px;
  margin-top: 4px;
  font-size: 16px;
  font-weight: 800;
  color: #1c2235;
}

.hero-stat strong small {
  font-size: 12px;
  color: #8b95a8;
}

.violet .hero-stat__icon {
  color: #7c5cff;
  background: #f1ebff;
}

.orange .hero-stat__icon {
  color: #ff7c47;
  background: #fff0e9;
}

.blue .hero-stat__icon {
  color: #467cf4;
  background: #edf4ff;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.toolbar-select {
  min-width: 150px;
  height: 42px;
  padding: 0 40px 0 14px;
  border: 1px solid #e8ebf4;
  border-radius: 14px;
  background: #fff;
  font-size: 14px;
  color: #20263a;
  box-shadow: 0 10px 24px rgba(130, 139, 171, 0.08);
}

.toolbar-ranges {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.range-btn,
.export-btn,
.goal-btn,
.primary-side-btn,
.problem-btn {
  border: none;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.range-btn {
  height: 42px;
  padding: 0 22px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #ebeefa;
  color: #626d82;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 10px 24px rgba(130, 139, 171, 0.06);
}

.range-btn.active {
  color: #7256ff;
  border-color: rgba(114, 86, 255, 0.35);
  background: rgba(114, 86, 255, 0.06);
  box-shadow: 0 14px 28px rgba(114, 86, 255, 0.16);
}

.export-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 18px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #ebeefa;
  color: #6f54ff;
  font-size: 14px;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(130, 139, 171, 0.08);
}

.export-btn:hover,
.goal-btn:hover,
.primary-side-btn:hover,
.problem-btn:hover,
.range-btn:hover {
  transform: translateY(-1px);
}

.card {
  background:
    radial-gradient(circle at top left, rgba(129, 109, 255, 0.06), transparent 34%),
    rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(236, 239, 248, 0.92);
  border-radius: 22px;
  box-shadow: 0 16px 40px rgba(133, 141, 175, 0.12);
}

.summary-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr 0.92fr;
  gap: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-head strong {
  font-size: 15px;
  font-weight: 800;
  color: #182033;
}

.section-head span {
  font-size: 12px;
  color: #818a9b;
}

.score-card,
.radar-card,
.metrics-card,
.trend-card,
.analysis-card,
.problems-card,
.goal-card,
.dist-card,
.compare-card,
.suggest-card {
  padding: 18px 18px 20px;
}

.card-kicker {
  font-size: 13px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.88);
}

.score-card {
  background:
    radial-gradient(circle at 86% 16%, rgba(255, 255, 255, 0.28), transparent 28%),
    linear-gradient(135deg, #7b58ff 0%, #8f77ff 35%, #b79cff 100%);
  color: #fff;
  overflow: hidden;
}

.score-main {
  display: grid;
  grid-template-columns: 1fr 160px;
  align-items: end;
  gap: 10px;
  min-height: 222px;
}

.score-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 18px;
}

.score-value strong {
  font-size: 70px;
  line-height: 1;
  font-weight: 900;
}

.score-value small {
  font-size: 28px;
  font-weight: 700;
  opacity: 0.88;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 12px;
  margin-top: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 13px;
  font-weight: 800;
}

.score-copy,
.score-footnote {
  margin: 12px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.88);
}

.score-progress {
  width: 100%;
  height: 8px;
  margin-top: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 999px;
}

.score-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #fff;
}

.score-figure {
  align-self: end;
  height: 178px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.score-figure img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  mix-blend-mode: screen;
  filter: drop-shadow(0 10px 24px rgba(53, 36, 132, 0.16));
}

.radar-chart,
.dist-chart,
.trend-chart {
  width: 100%;
}

.radar-chart {
  height: 270px;
}

.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.metrics-list li {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f3f8;
}

.metrics-list li:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.metrics-icon,
.goal-icon,
.suggest-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
}

.metrics-list span {
  font-size: 14px;
  color: #596376;
}

.metrics-list strong {
  font-size: 19px;
  font-weight: 800;
  color: #182033;
}

.metrics-list small {
  margin-left: 3px;
  font-size: 12px;
  color: #8a93a6;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.9fr) minmax(280px, 0.9fr);
  gap: 18px;
  align-items: start;
}

.content-main,
.content-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.trend-chart {
  height: 260px;
}

.analysis-card .section-head strong,
.problems-card .section-head strong {
  font-size: 26px;
  line-height: 1.1;
}

.analysis-card .section-head span {
  font-size: 13px;
}

.exercise-list,
.problem-list,
.dist-list,
.suggest-list,
.compare-points {
  margin: 0;
  padding: 0;
  list-style: none;
}

.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.exercise-list li {
  display: grid;
  grid-template-columns: 84px minmax(0, 1.2fr) minmax(220px, 1fr) 24px;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f8;
}

.exercise-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.exercise-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 62px;
  overflow: hidden;
  border-radius: 16px;
}

.exercise-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.exercise-title strong {
  display: block;
  font-size: 18px;
  color: #1a2033;
}

.exercise-title span {
  display: block;
  margin-top: 5px;
  font-size: 13px;
  color: #8a92a4;
}

.exercise-scoreline {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.exercise-scoreline b {
  font-size: 32px;
  line-height: 1;
  color: #11182d;
}

.exercise-scoreline small {
  font-size: 14px;
  color: #8a92a4;
}

.exercise-scoreline em {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 26px;
  padding: 0 10px;
  margin-left: 6px;
  border-radius: 999px;
  font-style: normal;
  font-size: 12px;
  font-weight: 800;
}

.grade-excellent,
.grade-good {
  color: #1b9e58;
  background: #e9faef;
}

.grade-mid {
  color: #de8b16;
  background: #fff4e2;
}

.grade-low {
  color: #eb5d63;
  background: #ffe9ec;
}

.exercise-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.mini-stat span {
  display: block;
  font-size: 12px;
  color: #8b94a6;
}

.mini-stat strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
  color: #1a2033;
}

.mini-stat small {
  font-size: 12px;
  color: #8b94a6;
}

.mini-bar {
  height: 7px;
  margin-top: 10px;
  overflow: hidden;
  background: #eef1f7;
  border-radius: 999px;
}

.mini-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6e54ff, #57d2a3);
}

.row-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #a0a8ba;
  background: transparent;
  border: none;
}

.problem-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.problem-list li {
  display: grid;
  grid-template-columns: 40px minmax(0, 1.4fr) minmax(120px, 0.7fr) auto;
  align-items: center;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f2f8;
}

.problem-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.problem-index {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #fff4e7;
  color: #ff992e;
  font-size: 14px;
  font-weight: 800;
}

.problem-copy strong,
.problem-exercise strong {
  font-size: 18px;
  color: #1a2033;
}

.problem-copy p,
.problem-exercise span,
.coach-copy p,
.suggest-list p {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #818a9b;
}

.problem-btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  background: rgba(114, 86, 255, 0.1);
  color: #6e54ff;
  font-size: 13px;
  font-weight: 800;
}

.goal-items {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  gap: 14px;
  align-items: center;
}

.goal-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #fbfcff;
  border: 1px solid #eef1f7;
}

.goal-item span {
  display: block;
  font-size: 13px;
  color: #7c8597;
}

.goal-item strong {
  display: block;
  margin-top: 5px;
  font-size: 16px;
  color: #192033;
}

.goal-btn,
.primary-side-btn {
  height: 50px;
  padding: 0 22px;
  border-radius: 16px;
  background: linear-gradient(135deg, #735bff, #886bff);
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  box-shadow: 0 16px 28px rgba(114, 86, 255, 0.26);
}

.dist-chart {
  height: 250px;
}

.dist-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dist-list li {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #667085;
}

.dist-dot,
.legend-dot,
.point-mark {
  display: inline-block;
  border-radius: 50%;
}

.dist-dot {
  width: 10px;
  height: 10px;
}

.dist-name {
  color: #475062;
}

.dist-pct,
.dist-count {
  color: #8b94a6;
}

.compare-legend {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 13px;
  color: #677084;
}

.legend-dot {
  width: 10px;
  height: 10px;
  margin-right: 6px;
}

.legend-dot.purple {
  background: #7c5cff;
}

.legend-dot.green {
  background: #48c488;
}

.compare-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 14px;
  padding: 18px;
  border-radius: 18px;
  background:
    radial-gradient(circle at center, rgba(124, 92, 255, 0.12), transparent 54%),
    linear-gradient(180deg, #fafbff 0%, #f3f6fd 100%);
}

.compare-stage img {
  width: 100%;
  max-width: 240px;
  height: auto;
  object-fit: contain;
  mix-blend-mode: multiply;
}

.compare-score {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 16px;
}

.compare-score span {
  font-size: 13px;
  color: #7f8798;
}

.compare-score strong {
  font-size: 34px;
  color: #171f34;
}

.compare-points {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.compare-points li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #5f687a;
}

.point-mark {
  width: 10px;
  height: 10px;
}

.point-mark.good {
  background: #3ec77c;
}

.point-mark.mid {
  background: #ff9e2e;
}

.primary-side-btn {
  width: 100%;
  margin-top: 16px;
}

.suggest-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggest-list li {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.suggest-list strong {
  display: block;
  font-size: 16px;
  color: #1b2134;
}

.coach-banner {
  display: grid;
  grid-template-columns: 1fr 110px;
  align-items: end;
  gap: 10px;
  margin-top: 20px;
  padding: 18px 18px 0;
  overflow: hidden;
  border-radius: 18px;
  background: linear-gradient(180deg, #f5efff 0%, #eef2ff 100%);
}

.coach-copy span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 24px;
  font-weight: 900;
  color: #6f54ff;
}

.coach-banner img {
  width: 100%;
  height: auto;
  object-fit: contain;
}

.goal-icon.violet {
  color: #765bff;
  background: #f0ebff;
}

.goal-icon.blue {
  color: #4784ff;
  background: #ebf3ff;
}

.goal-icon.orange {
  color: #f39c33;
  background: #fff1df;
}

@media (max-width: 1400px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metrics-card {
    grid-column: 1 / -1;
  }
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .goal-items {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .goal-btn {
    grid-column: 1 / -1;
  }
}

@media (max-width: 960px) {
  .report-hero,
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-stats {
    justify-content: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .score-main {
    grid-template-columns: 1fr;
  }

  .exercise-list li,
  .problem-list li {
    grid-template-columns: 1fr;
  }

  .exercise-stats {
    grid-template-columns: 1fr;
  }

  .row-arrow {
    display: none;
  }

  .goal-items {
    grid-template-columns: 1fr;
  }
}
</style>
