<template>
  <StateDisplay v-if="loading" type="loading" skeleton="cards" />
  <div v-else class="quality-page">
    <header class="section-page-header">
      <div>
        <h1>Motion Quality Metrics / 动作质量指标</h1>
        <p>按动作查看真实训练评估维度与质量指标</p>
      </div>
    </header>

    <section class="filter-card quality-filter-card">
      <label>
        <span>选择动作 / Exercise</span>
        <select v-model="exerciseFilter" @change="loadData">
          <option value="">全部动作（综合）</option>
          <option v-for="ex in EXERCISE_OPTIONS" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
        </select>
      </label>
    </section>

    <section class="quality-hero-grid">
      <article class="quality-hero green-gradient">
        <Activity :size="34" />
        <span>Overall Quality</span>
        <strong>{{ avgScore }} 分</strong>
      </article>
      <article class="quality-hero blue-gradient">
        <TrendingUp :size="34" />
        <span>Valid Rate</span>
        <strong>{{ validRate }}%</strong>
      </article>
      <article class="quality-hero orange-gradient">
        <AlertTriangle :size="34" />
        <span>Issues Found</span>
        <strong>{{ totalIssues }}</strong>
      </article>
    </section>

    <section class="progress-card quality-metrics-card">
      <h2>{{ exerciseFilter ? exerciseName(exerciseFilter) + ' · ' : '' }}质量指标概览</h2>
      <div v-if="metrics.length" class="quality-list">
        <article v-for="metric in metrics" :key="metric.name">
          <header>
            <div>
              <strong>{{ metric.name }}</strong>
              <p>{{ metric.desc }}</p>
            </div>
            <span :class="metric.status">{{ statusLabel(metric.status) }}</span>
          </header>
          <div class="quality-meta">
            <small>当前: {{ metric.current }}%</small>
            <small>目标: {{ metric.target }}%</small>
          </div>
          <div class="quality-bar">
            <i :class="{ green: metric.current >= metric.target }" :style="{ width: `${metric.current}%` }" />
          </div>
        </article>
      </div>
      <StateDisplay v-else type="empty" title="暂无质量数据" text="完成该动作的训练后将显示真实维度评分" />
    </section>

    <section v-if="feedbackItems.length" class="progress-card feedback-card">
      <h2>纠错建议摘要 / Correction Tips</h2>
      <ul>
        <li v-for="(tip, i) in feedbackItems" :key="i">{{ tip }}</li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref } from "vue";
import { Activity, AlertTriangle, TrendingUp } from "lucide-vue-next";
import { getSessions, type SessionRecord } from "../api/sessions";
import { getPersonalReport } from "../api/reports";
import StateDisplay from "../components/StateDisplay.vue";

const EXERCISE_OPTIONS = [
  { key: "squat", name: "深蹲" },
  { key: "push_up", name: "俯卧撑" },
  { key: "jumping_jack", name: "开合跳" },
  { key: "plank", name: "平板支撑" },
];

const EXERCISE_METRIC_DESC: Record<string, Record<string, string>> = {
  squat: {
    "膝角": "下蹲时膝关节屈曲角度是否达标",
    "髋角": "髋关节活动度与下蹲深度",
    "躯干倾斜角": "上身是否保持中立稳定",
    "左右膝差": "双膝对称性与平衡控制",
  },
  push_up: {
    "肘角": "推起/下降时肘关节屈伸幅度",
    "肩角": "肩关节稳定性与控制",
    "身体直线角": "肩-髋-踝是否保持一条直线",
    "左右膝差": "左右发力对称性",
  },
  jumping_jack: {
    "肩外展角": "手臂侧举幅度是否充分",
    "双腿夹角": "双脚打开宽度与节奏",
    "手腕高度": "手臂上举高度是否达标",
    "脚踝距离": "下肢展开幅度",
  },
  plank: {
    "肩髋踝直线角": "平板支撑身体直线保持",
    "髋部角": "核心与臀部是否下沉",
    "颈部角": "头颈位置是否中立",
  },
};

const sessions = ref<SessionRecord[]>([]);
const personalReport = ref<Awaited<ReturnType<typeof getPersonalReport>> | null>(null);
const loading = ref(true);
const exerciseFilter = ref("");

const filteredSessions = computed(() => {
  if (!exerciseFilter.value) return sessions.value;
  return sessions.value.filter((s) => s.exercise === exerciseFilter.value);
});

const avgScore = computed(() => {
  const list = filteredSessions.value;
  if (!list.length) return 0;
  return Math.round(list.reduce((s, x) => s + x.average_score, 0) / list.length);
});

const validRate = computed(() => {
  const list = filteredSessions.value;
  const total = list.reduce((s, x) => s + x.total_count, 0);
  const valid = list.reduce((s, x) => s + x.valid_count, 0);
  if (total === 0) return personalReport.value?.valid_count && personalReport.value?.total_count
    ? Math.round((personalReport.value.valid_count / personalReport.value.total_count) * 100)
    : 0;
  return Math.round((valid / total) * 100);
});

const totalIssues = computed(() =>
  filteredSessions.value.reduce((s, x) => s + (x.error_count || 0), 0),
);

const metrics = computed(() => {
  const radar = exerciseFilter.value
    ? personalReport.value?.charts?.per_exercise_radar?.[exerciseFilter.value]
    : personalReport.value?.charts?.quality_radar;

  if (radar && radar.dimensions.length > 0) {
    const descMap = exerciseFilter.value
      ? EXERCISE_METRIC_DESC[exerciseFilter.value] || {}
      : {};
    return radar.dimensions.map((name, index) => {
      const current = Math.round(radar.values[index] ?? 0);
      const target = 85;
      return {
        name,
        desc: descMap[name] || "基于 AI 姿态分析的真实训练维度评分",
        current,
        target,
        status: current >= 90 ? "excellent" : current >= 75 ? "good" : current >= 60 ? "fair" : "poor",
      };
    });
  }
  return [];
});

const feedbackItems = computed(() => {
  const fb = personalReport.value?.feedback_summary;
  if (!fb) return [];
  return [...(fb.weaknesses || []).slice(0, 4), ...(fb.recommendations || []).slice(0, 4)];
});

function exerciseName(key: string) {
  return EXERCISE_OPTIONS.find((e) => e.key === key)?.name ?? key;
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    excellent: "优秀", good: "良好", fair: "一般", poor: "待改进",
  };
  return map[status] || status;
}

async function loadData() {
  loading.value = true;
  try {
    const [sessRes, reportRes] = await Promise.allSettled([
      getSessions({ limit: 200, exercise: exerciseFilter.value || undefined }),
      getPersonalReport({ exercise: exerciseFilter.value || undefined }),
    ]);
    if (sessRes.status === "fulfilled") sessions.value = sessRes.value.items || [];
    if (reportRes.status === "fulfilled") personalReport.value = reportRes.value;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
onActivated(loadData);
</script>

<style scoped>
.quality-page { display: grid; gap: 24px; }
.quality-filter-card { padding: 16px 20px; border-radius: 12px; background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); }
.quality-filter-card label { display: grid; gap: 6px; color: #94a3b8; font-size: 12px; }
.quality-filter-card select { max-width: 280px; padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(59,130,246,0.15); background: rgba(8,13,26,0.8); color: #f8fafc; }
.feedback-card ul { margin: 0; padding-left: 18px; color: #94a3b8; line-height: 1.7; font-size: 13px; }
</style>
