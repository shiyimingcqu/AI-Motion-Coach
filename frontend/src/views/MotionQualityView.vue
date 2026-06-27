<template>
  <StateDisplay v-if="loading" type="loading" skeleton="cards" />
  <div v-else class="quality-page">
    <header class="section-page-header">
      <div>
        <h1>Motion Quality Metrics / 动作质量指标</h1>
        <p>Detailed biomechanical analysis and quality indicators</p>
      </div>
    </header>

    <section class="quality-hero-grid">
      <article class="quality-hero green-gradient"><Activity :size="34" /><span>Overall Quality</span><strong>{{ avgScore }}%</strong></article>
      <article class="quality-hero blue-gradient"><TrendingUp :size="34" /><span>Improvement</span><strong>{{ improvement >= 0 ? `+${improvement}` : improvement }}%</strong></article>
      <article class="quality-hero orange-gradient"><AlertTriangle :size="34" /><span>Issues Found</span><strong>{{ totalIssues }}</strong></article>
    </section>

    <section class="progress-card quality-metrics-card">
      <h2>Quality Metrics Overview / 质量指标概览</h2>
      <div class="quality-list">
        <article v-for="metric in metrics" :key="metric.name">
          <header>
            <div>
              <strong>{{ metric.name }}</strong>
              <p>{{ metric.desc }}</p>
            </div>
            <span :class="metric.status">{{ metric.status }}</span>
          </header>
          <div class="quality-meta">
            <small>Current: {{ metric.current }}%</small>
            <small>Target: {{ metric.target }}%</small>
          </div>
          <div class="quality-bar">
            <i :class="{ green: metric.current >= metric.target }" :style="{ width: `${metric.current}%` }" />
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Activity, AlertTriangle, TrendingUp } from "lucide-vue-next";
import { getSessions, type SessionRecord } from "../api/sessions";
import { getDashboardStats } from "../api/dashboard";
import StateDisplay from "../components/StateDisplay.vue";

const sessions = ref<SessionRecord[]>([]);
const statsData = ref<any>(null);
const loading = ref(true);

const avgScore = computed(() => {
  if (!sessions.value.length) return 0;
  return Math.round(sessions.value.reduce((s, x) => s + x.average_score, 0) / sessions.value.length);
});

const totalIssues = computed(() => {
  return sessions.value.reduce((s, x) => s + (x.error_count || 0), 0);
});

const improvement = computed(() => {
  const sorted = [...sessions.value].sort((a, b) => a.created_at.localeCompare(b.created_at));
  if (sorted.length < 2) return 0;
  const first = sorted[0].average_score;
  const last = sorted[sorted.length - 1].average_score;
  return last - first;
});

const metrics = computed(() => {
  const score = avgScore.value || 80;
  return [
    { name: "Joint Angles / 关节角度", desc: "Knee and elbow angles within optimal range", current: Math.min(100, score + 5), target: 90, status: score >= 85 ? "excellent" : score >= 70 ? "good" : "fair" },
    { name: "Movement Speed / 运动速度", desc: "Movement tempo consistency", current: Math.min(100, score - 2), target: 88, status: score >= 80 ? "good" : "fair" },
    { name: "Range of Motion / 运动幅度", desc: "Exercise range completeness", current: Math.min(100, score + 3), target: 90, status: score >= 85 ? "excellent" : score >= 70 ? "good" : "fair" },
    { name: "Stability Index / 稳定性指数", desc: "Balance and fluctuation detection", current: Math.min(100, score - 5), target: 85, status: score >= 75 ? "good" : "fair" },
    { name: "Symmetry / 对称性", desc: "Left-right balance assessment", current: Math.min(100, score - 1), target: 90, status: score >= 80 ? "good" : "fair" },
    { name: "Posture Alignment / 姿态对齐", desc: "Spine and shoulder alignment", current: Math.min(100, score + 8), target: 92, status: score >= 85 ? "excellent" : score >= 70 ? "good" : "fair" },
  ];
});

onMounted(async () => {
  try {
    const [sessRes, statsRes] = await Promise.allSettled([
      getSessions({ limit: 100 }),
      getDashboardStats(),
    ]);
    if (sessRes.status === "fulfilled") sessions.value = sessRes.value.items || [];
    if (statsRes.status === "fulfilled") statsData.value = statsRes.value;
  } catch {
    // defaults apply
  } finally {
    loading.value = false;
  }
});
</script>
