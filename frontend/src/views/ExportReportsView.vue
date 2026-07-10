<template>
  <div class="report-page">
    <!-- Hero -->
    <header class="report-hero">
      <div class="hero-copy">
        <h1>来看看你最近练得怎么样 👋</h1>
        <p>我们帮你把训练情况整理好了，一眼就能看懂</p>
      </div>
      <img class="hero-thumb" src="/reports/hero-thumb.png" alt="鼓励插图" />
    </header>

    <!-- Toolbar -->
    <section class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">选择动作</span>
        <div class="toolbar-pills">
          <button
            v-for="item in exercisePills"
            :key="item.key"
            type="button"
            class="pill-btn"
            :class="{ active: exerciseFilter === item.key }"
            @click="exerciseFilter = item.key"
          >{{ item.label }}</button>
        </div>
        <span class="toolbar-label">选择时间</span>
        <div class="toolbar-ranges">
          <button
            v-for="item in ranges"
            :key="item.key"
            type="button"
            class="range-btn"
            :class="{ active: rangeKey === item.key }"
            @click="rangeKey = item.key"
          >{{ item.label }}</button>
        </div>
      </div>
    </section>

    <!-- Top Grid -->
    <section class="top-grid">
      <!-- Score Card (Big Purple) -->
      <article class="card score-card">
        <span class="card-kicker">这次整体表现</span>
        <div class="score-main">
          <div class="score-value">
            <strong>{{ avgScore }}</strong><small>分</small>
          </div>
          <span class="score-badge">还不错，继续加油</span>
          <p class="score-copy">{{ scoreEncouragement }}</p>
          <div class="score-progress"><i :style="{ width: `${Math.min(avgScore, 100)}%` }"></i></div>
          <p class="score-footnote">超过了 {{ outperformPct }}% 的同阶段用户 👍</p>
        </div>
      </article>

      <!-- Stats + Radar Column -->
      <div class="mid-col">
        <!-- Stats Row -->
        <div class="stats-row">
          <div class="stat-item violet">
            <div class="stat-icon"><Calendar :size="18" /></div>
            <div>
              <span>本月训练</span>
              <strong>{{ monthSessions }}<small>次</small></strong>
              <small>比上月 ↑ 12%</small>
            </div>
          </div>
          <div class="stat-item orange">
            <div class="stat-icon"><Flame :size="18" /></div>
            <div>
              <span>累计训练</span>
              <strong>{{ totalDays }}<small>天</small></strong>
              <small>坚持就是胜利！</small>
            </div>
          </div>
        </div>

        <!-- Radar Card -->
        <article class="card radar-card">
          <header class="section-head">
            <strong class="radar-title">
              你的动作表现
            </strong>
          </header>
          <div ref="radarRef" class="radar-chart"></div>
        </article>
      </div>

      <!-- Trend Card -->
      <article class="card trend-card">
        <header class="section-head">
          <strong>最近变化</strong>
          <div class="trend-dropdown">
            <span>得分</span>
            <ChevronDown :size="14" />
          </div>
        </header>
        <div class="trend-score-badge">{{ avgScore }}分</div>
        <div ref="trendRef" class="trend-chart"></div>
        <p class="trend-footnote">整体在稳步提升，继续保持！💪</p>
      </article>
    </section>

    <!-- Bottom Grid -->
    <section class="bottom-grid">
      <!-- Exercise Table -->
      <article class="card exercise-table-card">
        <header class="section-head">
          <strong>你练了哪些动作</strong>
          <div class="more-dropdown">
            <span>查看更多动作记录</span>
            <ChevronDown :size="14" />
          </div>
        </header>

        <div class="table-header">
          <span>动作</span>
          <span>练了多少次</span>
          <span>得分</span>
          <span>表现如何</span>
          <span>完成度</span>
          <span>平均时长</span>
          <span>消耗热量</span>
        </div>

        <ul class="exercise-list-new">
          <li v-for="item in exerciseAnalysis" :key="item.key">
            <div class="ex-thumb" :style="{ background: item.accent }">
              <img :src="`/exercises/${item.key}.png`" :alt="item.name" />
            </div>
            <div class="ex-info">
              <strong>{{ item.name }}</strong>
              <span>练了 {{ item.count }} 次</span>
            </div>
            <div class="ex-score">
              <b>{{ item.score }}</b><small>分</small>
            </div>
            <em :class="item.gradeClass">{{ item.grade }}</em>
            <div class="ex-completion">
              <div class="mini-bar"><i :style="{ width: `${item.completion}%` }"></i></div>
              <strong>{{ item.completion }}%</strong>
            </div>
            <span class="ex-duration">{{ formatTime(item.duration) }}</span>
            <span class="ex-calories">{{ item.calories }} 千卡</span>
            <button class="row-arrow" type="button" @click="router.push('/sessions')">
              <ChevronRight :size="18" />
            </button>
          </li>
        </ul>
      </article>

      <!-- Next Training Recommendations -->
      <aside class="next-col">
        <header class="next-head"><strong>接下来怎么练</strong></header>
        <ul class="next-list">
          <li v-for="(rec, idx) in nextTrainings" :key="idx">
            <div class="next-icon" :style="{ background: rec.bg, color: rec.color }">
              <component :is="rec.icon" :size="18" />
            </div>
            <div class="next-body">
              <strong>{{ rec.title }}</strong>
              <p>{{ rec.desc }}</p>
            </div>
            <ChevronRight :size="16" class="next-arrow" />
          </li>
        </ul>
      </aside>
    </section>

    <!-- Coach Banner -->
    <section class="coach-banner">
      <img class="coach-img" src="/reports/coach-fist.png" alt="鼓励插图" />
      <div class="coach-copy">
        <span>✨ 你已经很棒了！</span>
        <p>每一次训练，都是在成为更好的自己。坚持下去，你会看到更大的进步！</p>
      </div>
      <button class="continue-btn" type="button" @click="router.push('/sessions')">
        继续训练
        <ChevronRight :size="16" />
      </button>
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
  ChevronDown,
  ChevronRight,
  CircleCheckBig,
  Flame,
  Heart,
  Moon,
  ShieldCheck,
  Target,
  Timer,
  Zap,
} from "lucide-vue-next";
import { getDashboardStats } from "@/api/dashboard";
import { getSessions, type SessionRecord } from "@/api/sessions";
import { EXERCISE_META, getDateKey, getScoreLevel } from "@/data/trainingRecords";

const router = useRouter();

const rangeKey = ref<"7" | "30" | "90">("30");
const exerciseFilter = ref("");
const monthSessions = ref(27);
const totalDays = ref(3);
const avgScore = ref(64);
const totalSessions = ref(27);
const totalHours = ref(10);
const completionRate = ref(86);
const totalCalories = ref(1620);
const sessions = ref<SessionRecord[]>([]);

const radarRef = ref<HTMLElement | null>(null);
const trendRef = ref<HTMLElement | null>(null);

let charts: echarts.ECharts[] = [];

const ranges = [
  { key: "7" as const, label: "近7天" },
  { key: "30" as const, label: "近30天" },
  { key: "90" as const, label: "近90天" },
];

const exercisePills = computed(() => [
  { key: "", label: "全部动作" },
  ...Object.entries(EXERCISE_META).slice(0, 4).map(([k, m]) => ({ key: k, label: m.name })),
]);

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

const scoreEncouragement = computed(() => {
  const s = avgScore.value;
  if (s >= 85) return "你的动作越来越稳定了，继续保持这个状态！";
  if (s >= 70) return "你的动作越来越稳定了，深蹲还可以再蹲深一点哦！";
  return "你的动作越来越稳定了，深蹲还可以再蹲深一点哦！";
});

const exerciseAnalysis = computed(() => {
  const map = new Map<string, {
    key: string; name: string; count: number;
    totalScore: number; totalDuration: number; totalCalories: number; accent: string;
  }>();

  for (const item of filteredSessions.value) {
    const meta = EXERCISE_META[item.exercise] ?? { name: item.exercise, accent: "#f5f7ff" };
    if (!map.has(item.exercise)) {
      map.set(item.exercise, {
        key: item.exercise, name: meta.name, count: 0,
        totalScore: 0, totalDuration: 0, totalCalories: 0, accent: meta.accent ?? "#f5f7ff",
      });
    }
    const cur = map.get(item.exercise)!;
    cur.count += 1;
    cur.totalScore += item.average_score;
    cur.totalDuration += item.duration_seconds;
    cur.totalCalories += Math.max(60, Math.round(item.duration_seconds / 3));
  }

  const fallback = [
    { key: "squat", name: "深蹲", count: 26, score: 63, completion: 75, duration: 1440, calories: 60, accent: "#e8f5e9" },
    { key: "jumping_jack", name: "开合跳", count: 1, score: 91, completion: 98, duration: 1380, calories: 60, accent: "#e3f2fd" },
  ];

  const derived = [...map.values()]
    .map((item) => {
      const score = Math.round(item.totalScore / item.count);
      const level = getScoreLevel(score);
      return {
        key: item.key, name: item.name, count: item.count, score,
        grade: level.label,
        gradeClass: level.key === "excellent" ? "grade-excellent" : level.key === "good" ? "grade-good" : level.key === "mid" ? "grade-mid" : "grade-low",
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
    return { ...item, grade: level.label, gradeClass: level.key === "good" ? "grade-good" : "grade-mid" };
  });
});

const nextTrainings = computed(() => [
  { title: "先把深蹲腾得更稳一些", desc: "注意膝盖方向，慢下蹲更稳更稳定", icon: Target, bg: "#ede9fe", color: "#7c3aed" },
  { title: "每次训练控制在 3-5 组", desc: "循序渐进，效果更好", icon: Zap, bg: "#fff7ed", color: "#ea580c" },
  { title: "练习时注意膝盖方向", desc: "膝盖不要内扣，保护关节", icon: ShieldCheck, bg: "#ecfdf5", color: "#16a34a" },
  { title: "休息好，动作会更稳定", desc: "保证睡眠，让身体更有力量", icon: Moon, bg: "#eff6ff", color: "#2563eb" },
]);

function formatTime(seconds: number) {
  if (seconds <= 0) return "0秒";
  const minutes = Math.floor(seconds / 60);
  const remain = Math.floor(seconds % 60);
  if (minutes > 0) return `${minutes}秒`;
  return `${remain}秒`;
}

function renderRadar() {
  if (!radarRef.value) return;
  const chart = echarts.init(radarRef.value);
  chart.setOption({
    radar: {
      radius: 72,
      indicator: [
        { name: "稳定性", max: 100 },
        { name: "协调性", max: 100 },
        { name: "力量", max: 100 },
        { name: "节奏", max: 100 },
        { name: "动作幅度", max: 100 },
      ],
      splitNumber: 4,
      splitArea: { areaStyle: { color: ["rgba(124,92,255,0.05)", "rgba(124,92,255,0.02)"] } },
      splitLine: { lineStyle: { color: "rgba(124,92,255,0.12)" } },
      axisLine: { lineStyle: { color: "rgba(124,92,255,0.14)" } },
      axisName: { color: "#5a6476", fontSize: 11, fontWeight: 600 },
    },
    series: [{
      type: "radar",
      symbol: "circle",
      symbolSize: 6,
      lineStyle: { color: "#6e54ff", width: 2 },
      areaStyle: { color: "rgba(110,84,255,0.2)" },
      itemStyle: { color: "#6e54ff" },
      data: [{ value: [72, 68, 65, 74, 60] }],
    }],
  });
  charts.push(chart);
}

function renderTrend() {
  if (!trendRef.value) return;
  const chart = echarts.init(trendRef.value);
  chart.setOption({
    grid: { top: 12, left: 30, right: 16, bottom: 26, containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: ["06/10", "06/17", "06/24", "07/01", "07/08"],
      axisLabel: { color: "#98a2b3", fontSize: 11 },
      axisLine: { lineStyle: { color: "#edf0f7" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: "#f2f4fa" } },
      axisLabel: { color: "#98a2b3", fontSize: 11 },
    },
    series: [{
      type: "line",
      smooth: true,
      data: [45, 52, 58, 61, 64],
      symbolSize: 6,
      lineStyle: { width: 3, color: "#6e54ff" },
      itemStyle: { color: "#6e54ff" },
      areaStyle: { color: "rgba(110,84,255,0.08)" },
    }],
  });
  charts.push(chart);
}

function renderCharts() {
  charts.forEach((chart) => chart.dispose());
  charts = [];
  renderRadar();
  renderTrend();
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
  padding: 0 0 28px;
}

/* ── Hero ── */
.report-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.hero-copy h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #131a2e;
}

.hero-copy p {
  margin: 6px 0 0;
  font-size: 14px;
  color: #6f7787;
}

.hero-thumb {
  width: 160px;
  height: auto;
  object-fit: contain;
}

/* ── Toolbar ── */
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

.toolbar-label {
  font-size: 13px;
  color: #7e8798;
  white-space: nowrap;
}

.toolbar-pills {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.pill-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid #ebeefa;
  background: #fff;
  color: #626d82;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s;
}

.pill-btn.active {
  color: #7256ff;
  border-color: rgba(114, 86, 255, 0.35);
  background: rgba(114, 86, 255, 0.06);
}

.toolbar-ranges {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.range-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid #ebeefa;
  background: #fff;
  color: #626d82;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s;
}

.range-btn.active {
  color: #7256ff;
  border-color: rgba(114, 86, 255, 0.35);
  background: rgba(114, 86, 255, 0.08);
  box-shadow: 0 4px 14px rgba(114, 86, 255, 0.15);
}

/* ── Cards base ── */
.card {
  background:
    radial-gradient(circle at top left, rgba(129, 109, 255, 0.05), transparent 34%),
    rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(236, 239, 248, 0.92);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(133, 141, 175, 0.08);
  padding: 20px 22px 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-head strong {
  font-size: 15px;
  font-weight: 800;
  color: #182033;
}

.section-head.center {
  justify-content: center;
}

.section-head span,
.trend-dropdown,
.more-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #818a9b;
  cursor: pointer;
}

/* ── Top Grid ── */
.top-grid {
  display: grid;
  grid-template-columns: 420px 320px 1fr;
  gap: 20px;
}

/* Score card — big purple */
.score-card {
  background:
    radial-gradient(circle at 86% 14%, rgba(255, 255, 255, 0.22), transparent 30%),
    linear-gradient(135deg, #7b58ff 0%, #8f77ff 35%, #a78bff 100%);
  color: #fff;
  overflow: hidden;
  padding: 26px 28px 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-kicker {
  font-size: 14px;
  font-weight: 800;
  opacity: 0.9;
}

.score-main {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.score-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.score-value strong {
  font-size: 76px;
  line-height: 1;
  font-weight: 900;
}

.score-value small {
  font-size: 28px;
  font-weight: 700;
  opacity: 0.85;
}

.score-badge {
  display: block;
  align-self: flex-start;
  height: 28px;
  line-height: 28px;
  padding: 0 14px;
  margin-top: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.score-copy {
  margin: 12px 0 0;
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.5;
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

.score-footnote {
  margin: 12px 0 0;
  font-size: 13px;
  opacity: 0.85;
}

/* Mid column (stats + radar) */
.mid-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(236, 239, 248, 0.9);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(130, 139, 171, 0.06);
}

.stat-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  flex-shrink: 0;
}

.violet .stat-icon { color: #7c5cff; background: #f1ebff; }
.orange .stat-icon { color: #ff7c47; background: #fff0e9; }

.stat-item > div span {
  display: block;
  font-size: 12px;
  color: #7e8798;
}

.stat-item > div strong {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 4px;
  font-size: 19px;
  font-weight: 800;
  color: #1c2235;
}

.stat-item > div strong small {
  font-size: 12px;
  color: #8b95a8;
}

.stat-item > div small {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: #a0a8ba;
}

.radar-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.radar-card .section-head {
  flex-shrink: 0;
}

.radar-title {
  font-size: 16px;
  position: relative;
  padding-left: 10px;
}
.radar-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 2px;
  bottom: 2px;
  width: 3px;
  border-radius: 3px;
  background: #7b58ff;
}

.radar-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
}

/* Trend card */
.trend-card {
  position: relative;
  display: flex;
  flex-direction: column;
}

.trend-score-badge {
  position: absolute;
  top: 50px;
  right: 22px;
  padding: 4px 12px;
  border-radius: 10px;
  background: #7b58ff;
  color: #fff;
  font-size: 14px;
  font-weight: 800;
}

.trend-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
  margin-top: 8px;
}

.trend-footnote {
  margin: 8px 0 0;
  font-size: 12px;
  color: #818a9b;
  text-align: center;
}

/* ── Bottom Grid ── */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: start;
}

/* Exercise table */
.exercise-table-card {
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 100px 90px 70px 120px 80px 80px 90px 28px;
  gap: 8px;
  padding: 10px 4px 8px;
  border-bottom: 1px solid #f0f2f8;
  font-size: 12px;
  color: #8b94a6;
  font-weight: 700;
}

.exercise-list-new {
  margin: 0;
  padding: 0;
  list-style: none;
}

.exercise-list-new li {
  display: grid;
  grid-template-columns: 100px 90px 70px 120px 80px 80px 90px 28px;
  gap: 8px;
  align-items: center;
  padding: 14px 4px;
  border-bottom: 1px solid #f5f7fa;
}

.exercise-list-new li:last-child {
  border-bottom: none;
}

.ex-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 42px;
  border-radius: 12px;
  overflow: hidden;
}

.ex-thumb img {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.ex-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ex-info strong {
  font-size: 15px;
  font-weight: 700;
  color: #1a2033;
}

.ex-info span {
  font-size: 12px;
  color: #8a92a4;
}

.ex-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.ex-score b {
  font-size: 22px;
  font-weight: 800;
  color: #11182d;
}

.ex-score small {
  font-size: 13px;
  color: #8a92a4;
}

.exercise-list-new em {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-style: normal;
  font-size: 12px;
  font-weight: 700;
}

.grade-excellent, .grade-good { color: #1b9e58; background: #e9faef; }
.grade-mid { color: #de8b16; background: #fff4e2; }
.grade-low { color: #eb5d63; background: #ffe9ec; }

.ex-completion {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-bar {
  height: 6px;
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

.ex-completion strong {
  font-size: 14px;
  font-weight: 800;
  color: #1a2033;
}

.ex-duration, .ex-calories {
  font-size: 14px;
  color: #596376;
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
  cursor: pointer;
}

/* Next training recommendations */
.next-head {
  margin-bottom: 12px;
}

.next-head strong {
  font-size: 15px;
  font-weight: 800;
  color: #182033;
}

.next-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.next-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fbfcff;
  border: 1px solid #eef1f7;
  border-radius: 16px;
  cursor: pointer;
  transition: box-shadow 0.18s;
}

.next-list li:hover {
  box-shadow: 0 6px 20px rgba(130, 139, 171, 0.08);
}

.next-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  flex-shrink: 0;
}

.next-body {
  flex: 1;
  min-width: 0;
}

.next-body strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #1b2134;
}

.next-body p {
  margin: 3px 0 0;
  font-size: 12px;
  color: #818a9b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.next-arrow {
  flex-shrink: 0;
  color: #c0c7d4;
}

/* ── Coach Banner ── */
.coach-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 22px 28px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f5efff 0%, #ede9fe 50%, #eef2ff 100%);
  border: 1px solid #ebe4ff;
}

.coach-img {
  width: 110px;
  height: auto;
  flex-shrink: 0;
}

.coach-copy {
  flex: 1;
}

.coach-copy span {
  display: block;
  font-size: 20px;
  font-weight: 900;
  color: #6f54ff;
}

.coach-copy p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7588;
  line-height: 1.6;
}

.continue-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 42px;
  padding: 0 22px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #7b58ff, #8f77ff);
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 10px 28px rgba(114, 86, 255, 0.26);
  flex-shrink: 0;
  transition: transform 0.18s, box-shadow 0.18s;
}

.continue-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 34px rgba(114, 86, 255, 0.34);
}

/* ── Responsive ── */
@media (max-width: 1400px) {
  .top-grid {
    grid-template-columns: 1fr 1fr;
  }
  .score-card { grid-column: 1 / -1; }
  .mid-col { grid-column: 1 / -1; flex-direction: row; }
  .mid-col .stats-row { flex: 1; }
  .radar-card { flex: 2; }
  .trend-card { grid-column: 1 / -1; }
}

@media (max-width: 1200px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .report-hero { flex-direction: column; align-items: stretch; }
  .hero-thumb { align-self: center; max-width: 120px; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-left { flex-wrap: wrap; }
  .top-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: 1fr; }
  .exercise-list-new li,
  .table-header {
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 6px;
  }
  .ex-thumb, .row-arrow { display: none; }
}
</style>
