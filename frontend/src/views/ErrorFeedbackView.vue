<template>
  <div class="feedback-page">
    <header class="section-page-header">
      <div>
        <h1>Error Feedback / 动作错误反馈</h1>
        <p>Real-time error detection and correction suggestions</p>
      </div>
    </header>

    <!-- 模式切换控件 -->
    <section class="feedback-mode-tabs">
      <button
        class="mode-tab"
        :class="{ active: mode === 'session' }"
        @click="switchMode('session')"
      >
        <span>本次训练</span>
        <small v-if="sessionId">查看本次训练的错误反馈</small>
      </button>
      <button
        class="mode-tab"
        :class="{ active: mode === 'history' }"
        @click="switchMode('history')"
      >
        <span>历史反馈</span>
        <small>查看全局历史聚合反馈</small>
      </button>
    </section>

    <section class="feedback-stats-grid">
      <article class="feedback-stat-card critical">
        <span><AlertTriangle :size="18" /></span>
        <div><p>Critical / 严重错误</p><strong>{{ stats.critical }}</strong></div>
      </article>
      <article class="feedback-stat-card warning">
        <span><Info :size="18" /></span>
        <div><p>Warning / 警告</p><strong>{{ stats.warning }}</strong></div>
      </article>
      <article class="feedback-stat-card minor">
        <span><CheckCircle2 :size="18" /></span>
        <div><p>Minor / 轻微错误</p><strong>{{ stats.minor }}</strong></div>
      </article>
      <article class="feedback-stat-card correct">
        <span><ShieldAlert :size="18" /></span>
        <div><p>Correct / 正确动作</p><strong>{{ stats.correct }}</strong></div>
      </article>
    </section>

    <StateDisplay v-if="loading && !detections.length" type="loading" size="sm" />
    <StateDisplay
      v-else-if="!loading && detections.length === 0"
      type="empty"
      :title="mode === 'session' ? '本次未检测到明显错误' : '暂无错误反馈'"
      :text="mode === 'session' ? '本次训练质量良好，继续保持！' : '训练中的错误识别将在此处展示'"
      size="sm"
    />

    <template v-if="detections.length > 0">
      <section class="feedback-card">
        <h2>
          {{ mode === 'session' ? 'Session Error Detections / 本次训练检测到的错误' : 'Recent Error Detections / 最近检测到的错误' }}
        </h2>
        <div class="error-detection-list">
          <article v-for="item in detections" :key="item.time" class="error-detection-row" :class="item.tone">
            <header>
              <div>
                <strong>{{ item.exercise }}</strong>
                <span>{{ item.type }}</span>
              </div>
              <time>{{ item.time }}</time>
            </header>
            <p>{{ item.problem }}</p>
            <div>
              <strong>Correction Suggestion / 纠正建议:</strong>
              <span>{{ item.suggestion }}</span>
            </div>
          </article>
        </div>
      </section>

      <section class="feedback-card">
        <h2>
          {{ mode === 'session' ? 'Session Analysis / 本次训练分析' : 'Common Mistakes Analysis / 常见错误分析' }}
        </h2>
        <div class="mistake-list">
          <article v-for="item in mistakeByExercise" :key="item.exercise" class="mistake-row">
            <header>
              <strong>{{ item.exercise }}</strong>
              <span>Frequency: <b>{{ item.errors }} errors</b></span>
            </header>
            <div class="mistake-tags">
              <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
            </div>
            <div class="mistake-bar">
              <i :style="{ width: `${item.percent}%` }" />
              <strong>{{ item.percent }}%</strong>
            </div>
          </article>
        </div>
      </section>
    </template>

    <!-- 承接动作按钮区（仅 session mode 显示） -->
    <section v-if="mode === 'session' && sessionId" class="feedback-actions">
      <button class="primary-button" type="button" @click="goToSessions">
        <span>查看训练记录</span>
      </button>
      <button class="secondary-button" type="button" @click="switchMode('history')">
        <span>继续查看历史反馈</span>
      </button>
    </section>

    <section class="ai-recommend-card">
      <span class="blue-solid"><Info :size="20" /></span>
      <div>
        <h2>AI Recommendations / AI 建议</h2>
        <p>• Focus on knee alignment during squats - 35% of errors detected in this area</p>
        <p>• Review push-up form video tutorial to reduce elbow flare incidents</p>
        <p>• Consider adding plank progression exercises to improve core stability</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { AlertTriangle, CheckCircle2, Info, ShieldAlert } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getFeedbacks } from "../api/feedback";
import { getSession, getSessions } from "../api/sessions";

type Mode = "session" | "history";

interface Detection {
  exercise: string;
  type: string;
  problem: string;
  suggestion: string;
  time: string;
  tone: string;
}

interface Mistake {
  exercise: string;
  tags: string[];
  errors: number;
  percent: number;
}

const route = useRoute();
const router = useRouter();

const detections = ref<Detection[]>([]);
const loading = ref(true);
const mode = ref<Mode>("history");
const sessionId = ref("");

const stats = ref({ critical: 0, warning: 0, minor: 0, correct: 0 });

// Exercise display names
const exerciseNames: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  plank: "平板支撑",
  jumping_jack: "开合跳",
};

// Tone mapping
const severityTone: Record<string, string> = {
  high: "critical",
  medium: "warning",
  low: "minor",
};

// Grouped mistakes
const mistakeByExercise = computed(() => {
  const map: Record<string, { exercise: string; tags: string[]; errors: number }> = {};
  for (const d of detections.value) {
    const key = d.exercise;
    if (!map[key]) {
      map[key] = { exercise: exerciseNames[key] || key, tags: [], errors: 0 };
    }
    map[key].errors += 1;
    if (!map[key].tags.includes(d.type)) {
      map[key].tags.push(d.type);
    }
  }
  const values = Object.values(map);
  const maxErrors = Math.max(...values.map(v => v.errors), 1);
  return values.map(v => ({
    ...v,
    percent: Math.round((v.errors / maxErrors) * 100),
  }));
});

async function loadSessionFeedbacks(sid: string) {
  loading.value = true;
  try {
    const [fbRes, sessionRes] = await Promise.allSettled([
      getFeedbacks({ session_id: sid, limit: 50 }),
      getSession(sid),
    ]);

    const fbItems = fbRes.status === "fulfilled" ? fbRes.value.items : [];

    if (fbItems.length > 0) {
      detections.value = fbItems.map((f: any) => ({
        exercise: exerciseNames[f.exercise] || f.exercise,
        type: f.issue,
        problem: f.issue,
        suggestion: f.suggestion || "请根据纠正建议调整动作",
        time: f.created_at?.slice(11, 19) || "--:--",
        tone: severityTone[f.severity] || "minor",
      }));
      stats.value.critical = fbItems.filter((f: any) => f.severity === "high").length;
      stats.value.warning = fbItems.filter((f: any) => f.severity === "medium").length;
      stats.value.minor = fbItems.filter((f: any) => f.severity === "low").length;
    } else {
      detections.value = [];
      stats.value = { critical: 0, warning: 0, minor: 0, correct: 0 };
    }

    // Count correct from this session's valid_count
    if (sessionRes.status === "fulfilled" && sessionRes.value) {
      stats.value.correct = sessionRes.value.valid_count ?? 0;
    }
  } finally {
    loading.value = false;
  }
}

async function loadHistoryFeedbacks() {
  loading.value = true;
  try {
    const [fbRes, sessionRes] = await Promise.allSettled([
      getFeedbacks({ limit: 50 }),
      getSessions({ limit: 20 }),
    ]);

    // Process feedbacks from API
    const fbItems = fbRes.status === "fulfilled" ? fbRes.value.items : [];

    if (fbItems.length > 0) {
      detections.value = fbItems.map((f: any) => ({
        exercise: exerciseNames[f.exercise] || f.exercise,
        type: f.issue,
        problem: f.issue,
        suggestion: f.suggestion || "请根据纠正建议调整动作",
        time: f.created_at?.slice(11, 19) || "--:--",
        tone: severityTone[f.severity] || "minor",
      }));
      stats.value.critical = fbItems.filter((f: any) => f.severity === "high").length;
      stats.value.warning = fbItems.filter((f: any) => f.severity === "medium").length;
      stats.value.minor = fbItems.filter((f: any) => f.severity === "low").length;
    } else {
      detections.value = [];
      stats.value = { critical: 0, warning: 0, minor: 0, correct: 0 };
    }

    // Count correct from valid sessions
    if (sessionRes.status === "fulfilled") {
      const sessions = sessionRes.value.items || [];
      stats.value.correct = sessions.reduce((s: number, x: any) => s + x.valid_count, 0);
    }
  } finally {
    loading.value = false;
  }
}

function switchMode(newMode: Mode) {
  if (newMode === mode.value) return;
  mode.value = newMode;

  if (newMode === "session" && sessionId.value) {
    loadSessionFeedbacks(sessionId.value);
  } else if (newMode === "history") {
    loadHistoryFeedbacks();
  }
}

function goToSessions() {
  if (sessionId.value) {
    router.push({ path: "/sessions", query: { highlight: sessionId.value } });
  }
}

onMounted(async () => {
  // Determine initial mode from URL query
  const querySession = route.query.session as string | undefined;
  if (querySession) {
    sessionId.value = querySession;
    mode.value = "session";
    await loadSessionFeedbacks(querySession);
  } else {
    mode.value = "history";
    await loadHistoryFeedbacks();
  }
});
</script>

<style scoped>
.feedback-mode-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.mode-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 24px;
  border: 1px solid var(--line, #d5ded2);
  border-radius: 12px;
  background: var(--panel, #ffffff);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-tab:hover {
  border-color: var(--green, #1b7a57);
  background: rgba(27, 122, 87, 0.03);
}

.mode-tab.active {
  border-color: var(--green, #1b7a57);
  background: rgba(27, 122, 87, 0.08);
  box-shadow: 0 0 0 1px rgba(27, 122, 87, 0.15);
}

.mode-tab span {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink, #16211b);
}

.mode-tab small {
  font-size: 12px;
  color: var(--muted, #69756e);
}

.mode-tab.active span {
  color: var(--green, #1b7a57);
}

.feedback-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  margin-bottom: 24px;
}

.feedback-actions .primary-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.feedback-actions .secondary-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 1px solid var(--line, #d5ded2);
  border-radius: 9px;
  background: var(--panel, #ffffff);
  color: var(--ink, #16211b);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.feedback-actions .secondary-button:hover {
  background: rgba(27, 122, 87, 0.05);
  border-color: var(--green, #1b7a57);
}
</style>
