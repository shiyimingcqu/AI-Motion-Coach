<template>
  <StateDisplay v-if="loading" type="loading" skeleton="chart" />
  <div v-else class="score-trends-page">
    <header class="section-page-header">
      <div>
        <h1>Score Trends / 分数趋势</h1>
        <p>Analyze performance trends and patterns over time</p>
      </div>
    </header>

    <section class="summary-card-grid">
      <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="progress-card">
      <header class="chart-card-header">
        <h2>7-Day Score Trend / 7天分数趋势</h2>
        <select><option>Last 7 Days</option></select>
      </header>
      <div class="wide-line-chart score-line-chart">
        <svg v-if="trendPoints.length" viewBox="0 0 1000 240" preserveAspectRatio="none">
          <polyline :points="trendPolyline" fill="none" stroke="#4f7df3" stroke-width="3" />
          <g fill="#4f7df3">
            <circle v-for="(p, i) in trendPoints" :key="i" :cx="p.x" :cy="p.y" r="6" />
          </g>
        </svg>
        <div v-if="trendLabels.length" class="chart-axis">
          <span v-for="(label, i) in trendLabels" :key="i">{{ label }}</span>
        </div>
        <StateDisplay v-if="!trendPoints.length" type="empty" title="暂无趋势数据" text="完成训练后趋势图表将自动生成" />
      </div>
    </section>

    <section class="score-two-grid">
      <article class="progress-card">
        <h2>Exercise Comparison / 动作对比</h2>
        <div class="comparison-bars">
          <span v-for="item in comparisons" :key="item.name" :style="{ height: `${item.score * 2.4}px` }"><b>{{ item.name }}</b></span>
        </div>
      </article>
      <article class="progress-card">
        <h2>Performance Categories / 表现类别</h2>
        <div class="radar-visual">
          <div class="radar-polygon" />
          <span class="r-top">Form / 动作形态</span>
          <span class="r-right">Balance / 平衡性</span>
          <span class="r-bottom-right">Range / 幅度</span>
          <span class="r-bottom">Speed / 速度</span>
          <span class="r-left">Stability / 稳定性</span>
          <span class="r-top-left">Alignment / 对齐</span>
        </div>
      </article>
    </section>

    <section class="progress-card">
      <h2>Detailed Score Breakdown / 详细分数分析</h2>
      <div class="score-breakdown-list">
        <article v-for="item in breakdown" :key="item.name">
          <header><strong>{{ item.name }}</strong><span>Current <b>{{ item.current }}</b> Change <b>+{{ item.change }}</b></span></header>
          <div class="detail-score-bar"><i :style="{ width: `${item.current}%` }" /></div>
          <footer><small>Previous: {{ item.previous }}</small><small>Average: {{ item.average }}</small></footer>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getSessions, type SessionRecord } from "../api/sessions";
import { getPersonalReport } from "../api/reports";
import StateDisplay from "../components/StateDisplay.vue";

const sessions = ref<SessionRecord[]>([]);
const personalReport = ref<Awaited<ReturnType<typeof getPersonalReport>> | null>(null);
const loading = ref(true);

const trendData = computed(() => personalReport.value?.charts?.score_trend || personalReport.value?.trend || []);

const trendPoints = computed(() => {
  const data = trendData.value;
  if (!data || data.length < 2) return [];
  const width = 1000;
  const height = 240;
  const padding = 30;
  const scores = data.map((d: any) => d.score);
  const minScore = Math.max(0, Math.min(...scores) - 10);
  const maxScore = Math.min(100, Math.max(...scores) + 10);
  const range = maxScore - minScore || 1;

  return data.map((d: any, i: number) => ({
    x: Math.round(padding + (i / (data.length - 1)) * (width - 2 * padding)),
    y: Math.round(height - padding - ((d.score - minScore) / range) * (height - 2 * padding)),
    label: d.date?.slice(5) || "",
    score: d.score,
  }));
});

const trendPolyline = computed(() =>
  trendPoints.value.map(p => `${p.x},${p.y}`).join(" ")
);

const trendLabels = computed(() =>
  trendPoints.value.map(p => p.label)
);

const stats = computed(() => {
  const avg = personalReport.value?.average_score || 0;
  const trend = trendData.value;
  const trendScores = trend.map((d: { score: number }) => d.score);
  const peak = trendScores.length ? Math.max(...trendScores) : 0;
  const peakDate = trendScores.length ? trend[trendScores.indexOf(peak)]?.date || "" : "";
  const weekAgo = trendScores.length >= 2 ? trendScores[trendScores.length - 1] - trendScores[0] : 0;
  const avgSessionScore = sessions.value.length
    ? Math.round(sessions.value.reduce((s, x) => s + x.average_score, 0) / sessions.value.length)
    : 0;
  return [
    { label: "Current Avg / 当前平均分", value: avgSessionScore || avg, hint: weekAgo >= 0 ? `+${weekAgo} vs last week` : `${weekAgo} vs last week`, tone: weekAgo >= 0 ? "tone-text-green" : "" },
    { label: "Peak Score / 最高分", value: peak, hint: peakDate || "-", tone: "" },
    { label: "Total Calories / 总卡路里", value: `${personalReport.value?.total_calories ?? 0} kcal`, hint: "Estimated burn", tone: "tone-text-orange" },
    { label: "Total Sessions / 总次数", value: sessions.value.length, hint: "Total training sessions", tone: "" },
  ];
});

const comparisons = computed(() => {
  const breakdown = personalReport.value?.exercise_breakdown;
  if (breakdown && breakdown.length > 0) {
    return breakdown.map((item) => ({ name: item.name, score: Math.round(item.avg_score) }));
  }
  const byEx: Record<string, number[]> = {};
  for (const s of sessions.value) {
    if (!byEx[s.exercise]) byEx[s.exercise] = [];
    byEx[s.exercise].push(s.average_score);
  }
  const result = Object.entries(byEx).map(([key, scores]) => ({
    name: exerciseName(key),
    score: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
  }));
  return result.length ? result : [{ name: "No data", score: 0 }];
});

const breakdown = computed(() => {
  const byEx: Record<string, { current: number; previous: number; count: number; scores: number[] }> = {};
  for (const s of sessions.value) {
    if (!byEx[s.exercise]) byEx[s.exercise] = { current: 0, previous: 0, count: 0, scores: [] };
    byEx[s.exercise].scores.push(s.average_score);
    byEx[s.exercise].current = s.average_score;
    byEx[s.exercise].count += 1;
  }
  return Object.entries(byEx).map(([key, vals]) => {
    const prev = vals.scores.length >= 2 ? vals.scores[vals.scores.length - 2] : vals.current;
    const avg = vals.scores.length
      ? Math.round(vals.scores.reduce((a, b) => a + b, 0) / vals.scores.length)
      : vals.current;
    return {
      name: exerciseName(key),
      current: vals.current,
      change: vals.scores.length >= 2 ? vals.current - prev : 0,
      previous: prev,
      average: avg,
    };
  }).slice(0, 5);
});

function exerciseName(key: string): string {
  const map: Record<string, string> = {
    squat: "深蹲", push_up: "俯卧撑", jumping_jack: "开合跳", plank: "平板支撑",
  };
  return map[key] ?? key;
}

onMounted(async () => {
  try {
    const [sessRes, reportRes] = await Promise.allSettled([
      getSessions({ limit: 200 }),
      getPersonalReport(),
    ]);
    if (sessRes.status === "fulfilled") {
      sessions.value = sessRes.value.items || [];
    }
    if (reportRes.status === "fulfilled") {
      personalReport.value = reportRes.value;
    }
  } catch {
    // defaults apply
  } finally {
    loading.value = false;
  }
});
</script>
