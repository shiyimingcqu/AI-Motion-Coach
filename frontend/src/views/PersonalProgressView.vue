<template>
  <StateDisplay v-if="loading" type="loading" skeleton="cards" :skeleton-rows="4" />
  <StateDisplay v-else-if="sessions.length === 0" type="empty" title="暂无训练数据" text="完成训练后，你的进步趋势将在此展示" />
  <div v-else class="progress-page">
    <header class="section-page-header">
      <div>
        <h1>Personal Progress / 个人进步趋势</h1>
        <p>Track your improvement journey over time</p>
      </div>
    </header>

    <section class="gradient-stat-grid">
      <article v-for="card in cards" :key="card.label" :class="['gradient-stat-card', card.tone]">
        <component :is="card.icon" :size="18" />
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </section>

    <section class="progress-card">
      <h2>6-Month Score Trend / 6个月分数趋势</h2>
      <div class="wide-line-chart">
        <svg viewBox="0 0 1000 210" preserveAspectRatio="none">
          <defs>
            <linearGradient id="progressArea" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#4f7df3" stop-opacity="0.18" />
              <stop offset="100%" stop-color="#4f7df3" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path :d="svgPoints.area" fill="url(#progressArea)" />
          <polyline :points="svgPoints.path.replace('M', '')" fill="none" stroke="#5d84ff" stroke-width="3" />
        </svg>
        <div class="chart-axis months"><span v-for="m in monthlyVolume" :key="m.month">{{ m.month }}月</span></div>
      </div>
    </section>

    <section class="progress-card">
      <h2>Exercise-Specific Progress / 各动作进步情况</h2>
      <div class="exercise-progress-list">
        <article v-for="exercise in exerciseAverages" :key="exercise.name">
          <header>
            <strong>{{ exercise.name }}</strong>
            <span>4-Week Improvement: <b>+{{ exercise.gain }}%</b></span>
          </header>
          <div class="week-grid">
            <div v-for="(score, index) in exercise.scores" :key="index" :class="{ current: index === 3 }">
              <small>Week {{ index + 1 }}</small>
              <strong>{{ score }}</strong>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="progress-card">
      <h2>Training Volume / 训练量</h2>
      <div class="volume-bars">
        <span v-for="bar in monthlyVolume" :key="bar.month" :style="{ height: `${bar.value * 4}px` }"><b>{{ bar.month }}</b></span>
      </div>
    </section>

    <section class="progress-card">
      <h2>Milestones & Achievements / 里程碑与成就</h2>
      <div class="milestone-list">
        <article v-for="item in milestones" :key="item.title">
          <span>{{ item.icon }}</span>
          <div><strong>{{ item.title }}</strong><small>{{ item.desc }}</small></div>
          <time>{{ item.date }}</time>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Award, CalendarDays, Target, TrendingUp } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getSessions, type SessionRecord } from "../api/sessions";

const sessions = ref<SessionRecord[]>([]);
const loading = ref(true);

const recentCount = computed(() => sessions.value.length);
const totalSessions = computed(() => sessions.value.length);

const avgScore = computed(() => {
  if (!sessions.value.length) return 0;
  const sum = sessions.value.reduce((s, x) => s + x.average_score, 0);
  return Math.round(sum / sessions.value.length);
});

const totalDuration = computed(() => {
  return sessions.value.reduce((s, x) => s + x.duration_seconds, 0);
});

const totalDays = computed(() => {
  const days = new Set(sessions.value.map(s => s.created_at?.slice(0, 10)));
  return days.size;
});

const trendPoints = computed(() => {
  const sorted = [...sessions.value].sort((a, b) => a.created_at.localeCompare(b.created_at));
  return sorted.slice(-30);
});

const exerciseAverages = computed(() => {
  const byExercise: Record<string, number[]> = {};
  for (const s of sessions.value) {
    if (!byExercise[s.exercise]) byExercise[s.exercise] = [];
    byExercise[s.exercise].push(s.average_score);
  }
  return Object.entries(byExercise).map(([key, scores]) => ({
    name: exerciseName(key),
    scores: scores.slice(-4),
    gain: scores.length >= 2 ? Math.round(scores[scores.length - 1] - scores[0]) : 0,
  }));
});

const monthlyVolume = computed(() => {
  const byMonth: Record<string, number> = {};
  for (const s of sessions.value) {
    const month = s.created_at?.slice(0, 7);
    if (month) byMonth[month] = (byMonth[month] || 0) + 1;
  }
  return Object.entries(byMonth).slice(-6).map(([month, value]) => ({
    month: month.slice(5), // MM
    value,
  }));
});

const cards = computed(() => [
  { label: "Overall Progress", value: totalSessions.value > 5 ? `+${Math.min(30, avgScore.value - 60)}%` : "New", hint: `based on ${totalSessions.value} sessions`, icon: TrendingUp, tone: "blue-gradient" },
  { label: "Achievements", value: String(Math.min(100, totalDays.value * 2)), hint: "milestones reached", icon: Award, tone: "green-gradient" },
  { label: "Current Score", value: String(avgScore.value), hint: "average rating", icon: Target, tone: "purple-gradient" },
  { label: "Training Days", value: String(totalDays.value), hint: "active days", icon: CalendarDays, tone: "orange-gradient" }
]);

const milestones = computed(() => {
  const items: { icon: string; title: string; desc: string; date: string }[] = [];
  const sorted = [...sessions.value].sort((a, b) => a.created_at.localeCompare(b.created_at));
  for (const s of sorted.slice(-4)) {
    items.push({
      icon: "🏆",
      title: `Session / 训练记录`,
      desc: `${exerciseName(s.exercise)} · Score: ${s.average_score}`,
      date: s.created_at?.slice(0, 10) || "",
    });
  }
  if (!items.length) {
    items.push({ icon: "🔥", title: "开始你的训练之旅", desc: "完成训练后将在此展示里程碑", date: "" });
  }
  return items;
});

// SVG chart points for trend line
const svgPoints = computed(() => {
  const pts = trendPoints.value;
  if (pts.length < 2) return { path: "M0,138 L1000,138", area: "M0,138 L1000,138 L1000,210 L0,210 Z" };
  const w = 1000;
  const h = 210;
  const maxScore = Math.max(...pts.map(p => p.average_score), 70);
  const minScore = Math.min(...pts.map(p => p.average_score), 60);
  const range = maxScore - minScore || 1;
  const points = pts.map((p, i) => {
    const x = (i / (pts.length - 1)) * w;
    const y = h - 30 - ((p.average_score - minScore) / range) * (h - 60);
    return `${x},${y}`;
  });
  const path = points.join(" L");
  const firstX = points[0].split(",")[0];
  const lastX = points[points.length - 1].split(",")[0];
  return {
    path: `M${path}`,
    area: `M${path} L${lastX},210 L${firstX},210 Z`,
  };
});

function exerciseName(key: string): string {
  const map: Record<string, string> = {
    squat: "深蹲", push_up: "俯卧撑", jumping_jack: "开合跳", plank: "平板支撑",
  };
  return map[key] ?? key;
}

onMounted(async () => {
  try {
    const data = await getSessions({ limit: 200 });
    sessions.value = data.items || [];
  } catch {
    sessions.value = [];
  } finally {
    loading.value = false;
  }
});
</script>
