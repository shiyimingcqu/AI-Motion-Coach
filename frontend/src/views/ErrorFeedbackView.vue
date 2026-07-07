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
        <small>查看本次训练的错误反馈</small>
      </button>
      <button
        class="mode-tab"
        :class="{ active: mode === 'history' }"
        @click="switchMode('history')"
      >
        <span>历史反馈</span>
        <small>按每次训练查看记录与建议</small>
      </button>
    </section>

    <!-- 历史训练列表 -->
    <section
      v-if="mode === 'history' && !activeSessionId"
      class="feedback-card history-session-list"
    >
      <h2>训练记录</h2>
      <p class="history-list-hint">选择一次训练，查看该次的错误反馈与 AI 建议。</p>

      <StateDisplay v-if="historyLoading" type="loading" size="sm" />
      <StateDisplay
        v-else-if="historySessions.length === 0"
        type="empty"
        title="暂无训练记录"
        text="完成实时检测或视频分析后，记录会显示在这里。"
        size="sm"
      />

      <div v-else class="history-session-cards">
        <button
          v-for="session in historySessions"
          :key="session.session_id"
          type="button"
          class="history-session-card"
          @click="openHistorySession(session.session_id)"
        >
          <header>
            <div>
              <strong>{{ formatExerciseName(session.exercise) }}</strong>
              <span>{{ formatSessionDate(session.created_at) }}</span>
            </div>
            <ChevronRight :size="18" />
          </header>
          <div class="history-session-metrics">
            <span>评分 {{ session.average_score }}</span>
            <span class="history-score-hint">{{ getScoreFeedback(session.average_score).emoji }} {{ getScoreFeedback(session.average_score).title }}</span>
          </div>
        </button>
      </div>
    </section>

    <button
      v-if="mode === 'history' && activeSessionId"
      type="button"
      class="history-back-btn"
      @click="backToHistoryList"
    >
      <ArrowLeft :size="16" />
      返回训练列表
    </button>

    <section
      v-if="activeSessionId && currentSessionMeta"
      class="score-hero-banner"
      :class="scoreFeedback.tone"
    >
      <div class="score-hero-main">
        <span class="score-hero-emoji">{{ scoreFeedback.emoji }}</span>
        <div>
          <p class="score-hero-label">本次训练平均分</p>
          <strong class="score-hero-value">{{ currentSessionMeta.average_score }}</strong>
          <span class="score-hero-unit">分</span>
        </div>
      </div>
      <div class="score-hero-message">
        <strong>{{ scoreFeedback.title }}</strong>
        <p>{{ scoreFeedback.message }}</p>
        <div class="score-hero-meta">
          <span>{{ formatExerciseName(currentSessionMeta.exercise) }}</span>
          <span>{{ formatSessionDate(currentSessionMeta.created_at) }}</span>
          <span>时长 {{ formatDuration(currentSessionMeta.duration_seconds) }}</span>
        </div>
      </div>
    </section>

    <StateDisplay
      v-else-if="activeSessionId && sessionMetaLoading"
      type="loading"
      size="sm"
      text="加载训练评分..."
    />

    <StateDisplay
      v-if="mode === 'session' && !activeSessionId"
      type="empty"
      title="暂无本次训练记录"
      text="完成一次实时检测或视频分析后，可从训练结束页进入本次反馈。"
      size="sm"
    />

    <section v-if="activeSessionId" class="feedback-stats-grid">
      <button
        v-for="card in statCards"
        :key="card.key"
        type="button"
        class="feedback-stat-card stat-card-btn"
        :class="[card.key, { active: activeFilter === card.key }]"
        @click="setStatFilter(card.key)"
      >
        <span><component :is="card.icon" :size="18" /></span>
        <div>
          <p>{{ card.label }}</p>
          <strong>{{ cardCount(card.key) }}</strong>
        </div>
      </button>
    </section>

    <section v-if="activeSessionId && activeFilter !== 'all'" class="feedback-card stat-detail-panel">
      <header class="stat-detail-header">
        <div>
          <h2>{{ activeStatMeta.title }}</h2>
          <p>{{ activeStatMeta.subtitle }}</p>
        </div>
      </header>

      <div v-if="displayDetections.length" class="error-detection-list compact">
        <article
          v-for="item in displayDetections"
          :key="`${item.time}-${item.type}`"
          class="error-detection-row"
          :class="item.tone"
        >
          <header>
            <div>
              <strong>{{ item.exercise }}</strong>
              <span>{{ item.type }}</span>
            </div>
            <time>{{ item.time }}</time>
          </header>
          <p>{{ item.problem }}</p>
          <div v-if="item.suggestion">
            <strong>{{ item.kind === 'positive' ? 'Keep It Up / 保持建议:' : '纠正建议:' }}</strong>
            <span>{{ item.suggestion }}</span>
          </div>
        </article>
      </div>

      <StateDisplay
        v-else
        type="empty"
        title="暂无该类反馈"
        text="切换到「所有反馈」可查看完整训练反馈。"
        size="sm"
      />
    </section>

    <StateDisplay
      v-if="activeSessionId && loading && !allDetections.length"
      type="loading"
      size="sm"
    />
    <StateDisplay
      v-else-if="activeSessionId && !loading && activeFilter === 'all' && allDetections.length === 0 && positiveNotes.length === 0"
      type="empty"
      title="本次未检测到明显错误"
      text="本次训练质量良好，继续保持！"
      size="sm"
    />

    <template v-if="activeSessionId && activeFilter === 'all' && allFeedbackItems.length > 0">
      <section class="feedback-card">
        <h2>Session Feedback / 训练反馈</h2>
        <div class="error-detection-list">
          <article
            v-for="(item, index) in allFeedbackItems"
            :key="`${item.kind}-${item.type}-${index}`"
            class="error-detection-row"
            :class="item.tone"
          >
            <header>
              <div>
                <strong>{{ item.exercise }}</strong>
                <span>{{ item.type }}</span>
              </div>
              <time>{{ item.time }}</time>
            </header>
            <p>{{ item.problem }}</p>
            <div v-if="item.suggestion">
              <strong>{{ item.kind === 'positive' ? 'Keep It Up / 保持建议:' : 'Correction Suggestion / 纠正建议:' }}</strong>
              <span>{{ item.suggestion }}</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="allDetections.length" class="feedback-card">
        <h2>Session Analysis / 错误分析</h2>
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

    <!-- AI 建议面板 -->
    <section v-if="activeSessionId" class="feedback-card ai-advice-card">
      <header class="ai-advice-card-header">
        <div class="ai-advice-card-icon">
          <Sparkles :size="20" />
        </div>
        <div class="ai-advice-card-heading">
          <h2>AI 智能建议</h2>
          <p>基于该次训练数据自动生成的个性化指导</p>
        </div>
        <label class="voice-toggle-pill" :class="{ active: voiceEnabled }">
          <Volume2 :size="14" />
          <input v-model="voiceEnabled" type="checkbox" class="sr-only" />
          <span>语音播报</span>
        </label>
      </header>

      <div v-if="aiAdvicePending || aiLoading" class="ai-advice-loading">
        <div class="ai-advice-spinner" aria-hidden="true"></div>
        <span>{{ aiAdvicePending ? "AI 建议正在生成中，请稍候..." : "正在加载已保存的 AI 建议..." }}</span>
      </div>

      <div class="ai-advice-body" :class="{ 'is-loading': aiLoading, 'is-lost': aiAdviceLost }">
        <AiAdviceContent
          theme="dark"
          :content="aiAdvice"
          :placeholder="aiAdviceLost ? '' : '暂无 AI 建议'"
        />
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "ErrorFeedbackView" });
import { computed, onActivated, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { AlertTriangle, ArrowLeft, CheckCircle2, ChevronRight, Info, Layers, Sparkles, ThumbsUp, Volume2 } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import AiAdviceContent from "../components/AiAdviceContent.vue";
import { getFeedbacks } from "../api/feedback";
import { getSession, getSessions, readLastSessionCache, type SessionRecord } from "../api/sessions";
import { useAiAdvice } from "../composables/useAiAdvice";
import { getScoreFeedback } from "../utils/scoreFeedback";

type Mode = "session" | "history";
type StatFilter = "all" | "critical" | "warning" | "minor" | "positive";
type DetectionTone = "critical" | "warning" | "minor" | "positive";

interface Detection {
  exercise: string;
  type: string;
  problem: string;
  suggestion: string;
  time: string;
  tone: DetectionTone;
  kind: "error" | "positive";
}

const POSITIVE_FEEDBACK_TYPE = "做得不错";
const POSITIVE_SUGGESTION = "继续保持当前节奏，稳定发挥这一优势";

interface StatCard {
  key: StatFilter;
  label: string;
  icon: typeof AlertTriangle;
}

const statCards: StatCard[] = [
  { key: "all", label: "所有反馈 / All", icon: Layers },
  { key: "critical", label: "Critical / 严重错误", icon: AlertTriangle },
  { key: "warning", label: "Warning / 警告", icon: Info },
  { key: "minor", label: "Minor / 轻微错误", icon: CheckCircle2 },
  { key: "positive", label: "Well Done / 做得不错", icon: ThumbsUp },
];

const ISSUE_ASPECT_MAP: Record<string, string> = {
  "下降深度不稳定": "depth",
  "下降幅度整体偏浅": "depth",
  "部分动作下降过深": "depth",
  "下降幅度不足": "depth",
  "底部身体未保持直线": "body_line",
  "身体直线控制不足": "body_line",
  "左右发力明显不均": "symmetry",
  "左右略有不对称": "symmetry",
  "下降速度偏快": "tempo",
  "整体节奏略快": "tempo",
  "下蹲深度不稳定": "depth",
  "下蹲深度整体偏浅": "depth",
  "下蹲深度整体偏深": "depth",
  "部分动作深度偏浅": "depth",
  "部分动作深度偏深": "depth",
  "底部躯干前倾明显": "trunk",
  "底部躯干前倾偏大": "trunk",
  "左右膝关节明显不对称": "symmetry",
  "左右膝关节略不对称": "symmetry",
  "下蹲速度偏快": "tempo",
  "双脚打开幅度不足": "spread",
  "手臂上举幅度不足": "arms",
  "手脚配合不同步": "sync",
  "塌腰或撅臀明显，身体未保持直线": "body_line",
  "身体直线略有偏差": "body_line",
  "髋部不稳定，核心控制不足": "core",
  "支撑过程中晃动过大": "stability",
};

const EXERCISE_ASPECTS: Record<string, Record<string, string>> = {
  push_up: {
    depth: "下降深度控制较稳定，能完成完整动作循环",
    body_line: "身体直线保持较好，核心有参与",
    symmetry: "左右发力较为均衡",
    tempo: "动作节奏整体平稳",
  },
  squat: {
    depth: "下蹲深度整体可控，完成度不错",
    trunk: "躯干稳定性良好，背部控制到位",
    symmetry: "左右膝盖对称性较好",
    tempo: "下蹲节奏比较均匀",
  },
  jumping_jack: {
    spread: "开合步幅基本到位",
    arms: "手臂上举动作较完整",
    sync: "手脚配合有一定协调性",
    symmetry: "左右动作对称性尚可",
  },
  plank: {
    body_line: "身体直线维持能力不错",
    core: "核心参与感较好",
    stability: "支撑稳定性在可控范围内",
  },
  lunge: {
    depth: "弓步下蹲深度整体可控",
    trunk: "躯干稳定性良好",
    symmetry: "左右腿对称性较好",
  },
  glute_bridge: {
    extension: "髋部伸展幅度较好",
    stability: "顶峰收缩控制稳定",
  },
  high_knees: {
    height: "抬膝高度基本到位",
    tempo: "节奏较为均匀",
  },
  burpee: {
    depth: "下蹲与平板阶段完成度不错",
    control: "身体控制较稳定",
  },
  mountain_climber: {
    body_line: "平板姿势维持较好",
    knee_drive: "提膝动作较完整",
  },
  pull_up: {
    depth: "上拉幅度整体可控",
    control: "身体摆动控制尚可",
  },
  dumbbell_curl: {
    depth: "弯举幅度较完整",
    stability: "上臂稳定性较好",
  },
  dumbbell_press: {
    extension: "推举伸展较充分",
    symmetry: "左右对称性尚可",
  },
  russian_twist: {
    rotation: "转体幅度基本到位",
    core: "核心参与感较好",
  },
};

const route = useRoute();
const router = useRouter();
const { aiAdvice, aiLoading, voiceEnabled, clearAdvice } = useAiAdvice();

const AI_ADVICE_LOST_MESSAGE = "该次训练的 AI 建议未保存，信息已丢失。";
const aiAdviceLost = ref(false);
const aiAdvicePending = ref(false);

const AI_ADVICE_POLL_INTERVAL_MS = 2000;
const AI_ADVICE_POLL_TIMEOUT_MS = 90000;
let aiAdvicePollTimer: ReturnType<typeof setInterval> | null = null;

function clearAiAdvicePoll() {
  if (aiAdvicePollTimer) {
    clearInterval(aiAdvicePollTimer);
    aiAdvicePollTimer = null;
  }
}

function hasStructuredFeedback(summary: Record<string, unknown>) {
  const items = summary.items;
  const issues = summary.issues;
  const suggestions = summary.suggestions;
  return Boolean(
    (Array.isArray(items) && items.length > 0)
    || (Array.isArray(issues) && issues.length > 0)
    || (Array.isArray(suggestions) && suggestions.length > 0),
  );
}

function startAiAdvicePoll(sessionId: string) {
  clearAiAdvicePoll();
  const startedAt = Date.now();

  aiAdvicePollTimer = setInterval(async () => {
    if (Date.now() - startedAt > AI_ADVICE_POLL_TIMEOUT_MS) {
      clearAiAdvicePoll();
      aiAdvicePending.value = false;
      aiAdvice.value = "AI 建议生成超时，请稍后刷新页面重试。";
      aiAdviceLost.value = true;
      return;
    }

    try {
      const session = await getSession(sessionId);
      const raw = session.feedback_summary;
      if (!raw) return;

      const summary = JSON.parse(raw) as {
        ai_advice?: string;
        ai_advice_pending?: boolean;
        ai_advice_status?: string;
      };
      const text = typeof summary.ai_advice === "string" ? summary.ai_advice.trim() : "";

      if (text) {
        clearAiAdvicePoll();
        aiAdvicePending.value = false;
        aiAdvice.value = text;
        return;
      }

      if (summary.ai_advice_status === "failed") {
        clearAiAdvicePoll();
        aiAdvicePending.value = false;
        aiAdvice.value = "AI 建议生成失败，请稍后刷新页面重试。";
        aiAdviceLost.value = true;
      }
    } catch {
      // ignore transient poll errors
    }
  }, AI_ADVICE_POLL_INTERVAL_MS);
}

const allDetections = ref<Detection[]>([]);
const positiveNotes = ref<string[]>([]);
const loading = ref(false);
const sessionMetaLoading = ref(false);
let lastLoadedSessionId = "";
const historyLoading = ref(false);
const mode = ref<Mode>("history");
const activeSessionId = ref("");
const sessionExercise = ref("squat");
const feedbackTime = ref("--:--");
const activeFilter = ref<StatFilter>("all");
const historySessions = ref<SessionRecord[]>([]);
const currentSessionMeta = ref<SessionRecord | null>(null);

const scoreFeedback = computed(() =>
  getScoreFeedback(Number(currentSessionMeta.value?.average_score ?? 0)),
);

const stats = ref({ critical: 0, warning: 0, minor: 0 });

const allFeedbackCount = computed(
  () => allDetections.value.length + positiveNotes.value.length,
);

function cardCount(key: StatFilter) {
  if (key === "all") return allFeedbackCount.value;
  if (key === "positive") return positiveNotes.value.length;
  return stats.value[key];
}

function isErrorFeedback(item: { issue?: string; severity?: string }) {
  return Boolean(item.issue) && item.severity !== "info";
}

function applyFeedbackStats(fbItems: Array<{ severity?: string }>) {
  const errorItems = fbItems.filter(isErrorFeedback);
  stats.value.critical = errorItems.filter((f) => f.severity === "high" || f.severity === "error").length;
  stats.value.warning = errorItems.filter((f) => f.severity === "medium" || f.severity === "warning").length;
  stats.value.minor = errorItems.filter((f) => f.severity === "low").length;
}

// Tone mapping
const severityTone: Record<string, string> = {
  high: "critical",
  medium: "warning",
  low: "minor",
  error: "critical",
  warning: "warning",
  info: "correct",
};

function setStatFilter(filter: StatFilter) {
  activeFilter.value = filter;
}

function buildStrengthMessages(exercise: string, issues: string[]): string[] {
  const aspects = EXERCISE_ASPECTS[exercise] || EXERCISE_ASPECTS.squat;
  const flagged = new Set(
    issues.map((issue) => ISSUE_ASPECT_MAP[issue]).filter(Boolean),
  );
  const messages = Object.entries(aspects)
    .filter(([key]) => !flagged.has(key))
    .map(([, message]) => message);

  if (messages.length === 0) {
    return ["训练态度积极，愿意反复尝试并调整动作"];
  }
  return messages;
}

function rebuildPositiveNotes(exercise: string, issues: string[], apiPositives: string[]) {
  const strengths = buildStrengthMessages(exercise, issues);
  const merged = [...new Set([...apiPositives, ...strengths])];
  positiveNotes.value = merged.slice(0, 5);
}

const positiveDetections = computed<Detection[]>(() => {
  const exerciseLabel = exerciseNames[sessionExercise.value] || sessionExercise.value;
  return positiveNotes.value.map((note) => ({
    exercise: exerciseLabel,
    type: POSITIVE_FEEDBACK_TYPE,
    problem: note,
    suggestion: POSITIVE_SUGGESTION,
    time: feedbackTime.value,
    tone: "positive",
    kind: "positive",
  }));
});

const allFeedbackItems = computed(() => [
  ...positiveDetections.value,
  ...allDetections.value,
]);

const displayDetections = computed(() => {
  if (activeFilter.value === "all") {
    return [];
  }
  if (activeFilter.value === "positive") {
    return positiveDetections.value;
  }
  return allDetections.value.filter((item) => item.tone === activeFilter.value);
});

const activeStatMeta = computed(() => {
  const filter = activeFilter.value;

  if (filter === "positive") {
    return {
      title: "做得不错",
      subtitle: "这些方面表现稳定，建议继续保持并强化",
    };
  }

  if (filter === "critical") {
    return {
      title: "严重错误详情",
      subtitle: "需要优先纠正的问题，可能影响训练安全或效果",
    };
  }

  if (filter === "warning") {
    return {
      title: "警告详情",
      subtitle: "建议尽快改善的问题，避免形成错误习惯",
    };
  }

  if (filter === "minor") {
    return {
      title: "轻微错误详情",
      subtitle: "细节层面的改进空间，优化后动作会更标准",
    };
  }

  return { title: "", subtitle: "" };
});

// Grouped mistakes — only count real errors, not positive/info feedback
const mistakeByExercise = computed(() => {
  const map: Record<string, { exercise: string; tags: string[]; errors: number }> = {};
  for (const d of allDetections.value) {
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

// Exercise display names
const exerciseNames: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  plank: "平板支撑",
  jumping_jack: "开合跳",
  lunge: "弓步蹲",
  glute_bridge: "臀桥",
  high_knees: "高抬腿",
  burpee: "波比跳",
  mountain_climber: "登山跑",
  pull_up: "引体向上",
  dumbbell_curl: "哑铃弯举",
  dumbbell_press: "哑铃推举",
  russian_twist: "俄罗斯转体",
};

function loadSavedAiAdvice(session: SessionRecord) {
  clearAiAdvicePoll();
  aiAdviceLost.value = false;
  aiAdvicePending.value = false;
  const raw = session.feedback_summary;
  if (!raw) {
    aiAdvice.value = AI_ADVICE_LOST_MESSAGE;
    aiAdviceLost.value = true;
    return;
  }

  try {
    const summary = JSON.parse(raw) as {
      ai_advice?: string;
      ai_advice_pending?: boolean;
      ai_advice_status?: string;
      items?: unknown[];
      issues?: unknown[];
      suggestions?: unknown[];
    };
    const text = typeof summary.ai_advice === "string" ? summary.ai_advice.trim() : "";
    if (text) {
      aiAdvice.value = text;
      return;
    }

    if (summary.ai_advice_pending || hasStructuredFeedback(summary)) {
      aiAdvicePending.value = true;
      aiAdvice.value = "";
      startAiAdvicePoll(session.session_id);
      return;
    }

    if (summary.ai_advice_status === "failed") {
      aiAdvice.value = "AI 建议生成失败，请稍后刷新页面重试。";
      aiAdviceLost.value = true;
      return;
    }
  } catch {
    // fall through to lost message
  }

  aiAdvice.value = AI_ADVICE_LOST_MESSAGE;
  aiAdviceLost.value = true;
}

async function loadSessionFeedbacks(sid: string) {
  if (!sid) return;
  lastLoadedSessionId = sid;
  activeSessionId.value = sid;
  loading.value = true;
  sessionMetaLoading.value = !currentSessionMeta.value || currentSessionMeta.value.session_id !== sid;
  clearAdvice();
  clearAiAdvicePoll();
  aiAdviceLost.value = false;
  aiAdvicePending.value = false;
  activeFilter.value = "all";

  try {
    const session = await getSession(sid);
    currentSessionMeta.value = session;
    sessionExercise.value = session.exercise || "squat";
    feedbackTime.value = session.created_at?.slice(11, 19) || "--:--";
    loadSavedAiAdvice(session);
  } catch (error) {
    console.error("加载训练记录失败:", error);
    currentSessionMeta.value = null;
    aiAdvice.value = AI_ADVICE_LOST_MESSAGE;
    aiAdviceLost.value = true;
  } finally {
    sessionMetaLoading.value = false;
  }

  try {
    const fbRes = await getFeedbacks({ session_id: sid, limit: 50 });
    const fbItems = fbRes.items || [];
    const errorItems = fbItems.filter(isErrorFeedback);
    const infoItems = fbItems.filter((f: any) => f.severity === "info" || !f.issue);
    const apiPositives = infoItems
      .map((f: any) => f.suggestion)
      .filter(Boolean);

    if (errorItems.length > 0) {
      allDetections.value = errorItems.map((f: any) => ({
        exercise: exerciseNames[f.exercise] || f.exercise,
        type: f.issue,
        problem: f.issue,
        suggestion: f.suggestion || "请根据纠正建议调整动作",
        time: f.created_at?.slice(11, 19) || "--:--",
        tone: (severityTone[f.severity] || "minor") as DetectionTone,
        kind: "error",
      }));
      applyFeedbackStats(fbItems);
    } else {
      allDetections.value = [];
      stats.value = { critical: 0, warning: 0, minor: 0 };
    }

    rebuildPositiveNotes(
      sessionExercise.value,
      allDetections.value.map((item) => item.problem),
      apiPositives,
    );
  } catch (error) {
    console.error("加载反馈失败:", error);
    if (!allDetections.value.length) {
      allDetections.value = [];
      stats.value = { critical: 0, warning: 0, minor: 0 };
    }
  } finally {
    loading.value = false;
  }
}

async function loadHistorySessions() {
  historyLoading.value = true;
  try {
    const response = await getSessions({ limit: 50 });
    historySessions.value = response.items || [];
  } catch (error) {
    console.error("加载训练记录失败:", error);
    historySessions.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function formatExerciseName(exercise: string) {
  return exerciseNames[exercise] || exercise;
}

function formatSessionDate(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 16).replace("T", " ");
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(seconds: number) {
  if (!seconds || seconds <= 0) return "--";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
}

function resetSessionDetailState() {
  clearAdvice();
  clearAiAdvicePoll();
  aiAdviceLost.value = false;
  aiAdvicePending.value = false;
  allDetections.value = [];
  positiveNotes.value = [];
  stats.value = { critical: 0, warning: 0, minor: 0 };
  currentSessionMeta.value = null;
  activeFilter.value = "all";
}

async function openHistorySession(sid: string) {
  activeSessionId.value = sid;
  mode.value = "history";
  await router.push({ path: "/feedback", query: { session: sid } });
  await loadSessionFeedbacks(sid);
}

async function backToHistoryList() {
  activeSessionId.value = "";
  resetSessionDetailState();
  mode.value = "history";
  await router.replace({ path: "/feedback" });
  await loadHistorySessions();
}

function switchMode(newMode: Mode) {
  if (newMode === mode.value) return;
  mode.value = newMode;

  if (newMode === "history") {
    activeSessionId.value = "";
    resetSessionDetailState();
    void router.replace({ path: "/feedback" });
    void loadHistorySessions();
    return;
  }

  const querySession = route.query.session as string | undefined;
  if (querySession) {
    activeSessionId.value = querySession;
    void loadSessionFeedbacks(querySession);
    return;
  }

  activeSessionId.value = "";
  resetSessionDetailState();
}

function hydrateSessionFromCache(sid: string): boolean {
  const cached = readLastSessionCache(sid);
  if (!cached) return false;
  currentSessionMeta.value = cached;
  sessionExercise.value = cached.exercise || "squat";
  feedbackTime.value = cached.created_at?.slice(11, 19) || "--:--";
  return true;
}

async function initFromRoute() {
  const querySession = route.query.session as string | undefined;
  const fromTraining = route.query.from === "realtime" || route.query.from === "upload";

  if (querySession) {
    mode.value = fromTraining ? "session" : "history";
    if (querySession !== lastLoadedSessionId) {
      resetSessionDetailState();
      if (fromTraining) {
        hydrateSessionFromCache(querySession);
      }
      await loadSessionFeedbacks(querySession);
    }
    return;
  }

  activeSessionId.value = "";
  lastLoadedSessionId = "";
  resetSessionDetailState();
  mode.value = "history";
  await loadHistorySessions();
}

onMounted(() => {
  void initFromRoute();
});

onActivated(() => {
  void initFromRoute();
});

watch(
  () => route.query.session,
  (sid) => {
    if (typeof sid === "string" && sid && sid !== lastLoadedSessionId) {
      void loadSessionFeedbacks(sid);
    }
  },
);

onUnmounted(() => {
  clearAiAdvicePoll();
});
</script>

<style scoped>
.feedback-stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
  perspective: 1200px;
}

.stat-card-btn {
  position: relative;
  width: 100%;
  min-height: 88px;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 16px;
  padding: 18px;
  isolation: isolate;
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.22s ease,
    filter 0.22s ease;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -2px 0 rgba(0, 0, 0, 0.2),
    0 6px 14px rgba(0, 0, 0, 0.2),
    0 3px 8px rgba(0, 0, 0, 0.16);
}

.stat-card-btn::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.02) 42%, transparent 100%);
  pointer-events: none;
  z-index: 0;
}

.stat-card-btn::after {
  content: "";
  position: absolute;
  inset: auto -20% -55% -20%;
  height: 70%;
  background: transparent;
  pointer-events: none;
  z-index: 0;
}

.stat-card-btn > span,
.stat-card-btn > div {
  position: relative;
  z-index: 1;
}

.stat-card-btn > span {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 4px 10px rgba(0, 0, 0, 0.2);
}

.stat-card-btn p {
  color: rgba(226, 232, 240, 0.82);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.stat-card-btn strong {
  display: block;
  margin-top: 6px;
  font-size: 28px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.03em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.28);
}

.stat-card-btn:hover {
  transform: translateY(-3px);
  filter: brightness(1.05);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 -3px 0 rgba(0, 0, 0, 0.16),
    0 14px 28px rgba(0, 0, 0, 0.3),
    0 6px 14px rgba(0, 0, 0, 0.2);
}

.stat-card-btn.active {
  transform: translateY(1px);
  filter: brightness(1.06);
  box-shadow:
    inset 0 4px 14px rgba(0, 0, 0, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    0 6px 16px rgba(0, 0, 0, 0.26);
}

/* 所有反馈 — 亮靛 */
.stat-card-btn.all {
  background: linear-gradient(145deg, #5b6cf2 0%, #3f4bd0 48%, #242a73 100%);
  border-color: rgba(163, 179, 255, 0.38);
}

.stat-card-btn.all > span {
  background: linear-gradient(145deg, rgba(173, 186, 255, 0.48), rgba(99, 115, 236, 0.3));
  color: #eff1ff;
}

.stat-card-btn.all strong {
  color: #f3f4ff;
}

.stat-card-btn.all.active {
  border-color: rgba(183, 198, 255, 0.55);
  box-shadow:
    inset 0 4px 14px rgba(32, 35, 88, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(144, 160, 255, 0.45),
    0 8px 22px rgba(72, 86, 200, 0.28);
}

/* 严重错误 — 亮玫瑰 */
.stat-card-btn.critical {
  background: linear-gradient(145deg, #f0627a 0%, #d43b59 48%, #5a1a2a 100%);
  border-color: rgba(255, 173, 186, 0.38);
}

.stat-card-btn.critical > span {
  background: linear-gradient(145deg, rgba(255, 173, 186, 0.48), rgba(220, 90, 114, 0.3));
  color: #ffe8ee;
}

.stat-card-btn.critical strong {
  color: #ffeef2;
}

.stat-card-btn.critical.active {
  border-color: rgba(255, 192, 202, 0.55);
  box-shadow:
    inset 0 4px 14px rgba(90, 26, 42, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(246, 120, 146, 0.42),
    0 8px 22px rgba(212, 59, 89, 0.26);
}

/* 警告 — 柔暖琥珀 */
.stat-card-btn.warning {
  background: linear-gradient(145deg, #f1a24a 0%, #d6782c 48%, #583317 100%);
  border-color: rgba(255, 200, 140, 0.38);
}

.stat-card-btn.warning > span {
  background: linear-gradient(145deg, rgba(255, 200, 140, 0.45), rgba(224, 128, 64, 0.3));
  color: #fff1e1;
}

.stat-card-btn.warning strong {
  color: #fff6e8;
}

.stat-card-btn.warning.active {
  border-color: rgba(255, 210, 160, 0.55);
  box-shadow:
    inset 0 4px 14px rgba(88, 51, 23, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(239, 150, 78, 0.42),
    0 8px 22px rgba(214, 120, 44, 0.26);
}

/* 轻微错误 — 亮蓝 */
.stat-card-btn.minor {
  background: linear-gradient(145deg, #4b8ef1 0%, #2f69d8 48%, #1a2c63 100%);
  border-color: rgba(164, 201, 255, 0.38);
}

.stat-card-btn.minor > span {
  background: linear-gradient(145deg, rgba(164, 201, 255, 0.45), rgba(76, 130, 238, 0.3));
  color: #eaf2ff;
}

.stat-card-btn.minor strong {
  color: #eef4ff;
}

.stat-card-btn.minor.active {
  border-color: rgba(186, 214, 255, 0.55);
  box-shadow:
    inset 0 4px 14px rgba(26, 44, 99, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(96, 155, 245, 0.42),
    0 8px 22px rgba(47, 105, 216, 0.26);
}

/* 做得不错 — 明亮青绿 */
.stat-card-btn.positive {
  background: linear-gradient(145deg, #39b98d 0%, #1f916f 48%, #0f4a3b 100%);
  border-color: rgba(153, 226, 200, 0.38);
}

.stat-card-btn.positive > span {
  background: linear-gradient(145deg, rgba(153, 226, 200, 0.45), rgba(57, 185, 141, 0.3));
  color: #e6fff5;
}

.stat-card-btn.positive strong {
  color: #effdf7;
}

.stat-card-btn.positive.active {
  border-color: rgba(176, 234, 212, 0.55);
  box-shadow:
    inset 0 4px 14px rgba(15, 74, 59, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(83, 206, 167, 0.42),
    0 8px 22px rgba(31, 145, 111, 0.26);
}

.stat-detail-panel {
  margin-bottom: 18px;
}

.stat-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-detail-header h2 {
  margin: 0;
  font-size: 20px;
  color: #f8fafc;
}

.stat-detail-header p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 14px;
}

.stat-clear-btn {
  flex-shrink: 0;
  padding: 8px 14px;
  border: 1px solid #334155;
  border-radius: 999px;
  background: transparent;
  color: #86efac;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.positive-feedback-box {
  margin-bottom: 16px;
  padding: 16px 18px;
  border-radius: 12px;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.28);
}

.positive-feedback-box h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #86efac;
}

.positive-feedback-box ul {
  margin: 0;
  padding-left: 18px;
  color: #bbf7d0;
  line-height: 1.7;
}

.error-detection-list.compact {
  gap: 12px;
}

.feedback-mode-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.history-list-hint {
  margin: 0 0 16px;
  color: #94a3b8;
  font-size: 14px;
}

.history-session-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-session-card {
  width: 100%;
  text-align: left;
  padding: 16px 18px;
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.72);
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.history-session-card:hover {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.08);
  transform: translateY(-1px);
}

.history-session-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.history-session-card strong {
  display: block;
  font-size: 16px;
  color: #f8fafc;
}

.history-session-card header span {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: #94a3b8;
}

.history-session-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  font-size: 13px;
  color: #cbd5e1;
}

.history-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 14px;
  border: 1px solid #334155;
  border-radius: 999px;
  background: transparent;
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.history-back-btn:hover {
  border-color: #22c55e;
  color: #86efac;
}

.score-hero-banner {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: center;
  padding: 20px 24px;
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
}
.score-hero-banner.excellent {
  border-color: rgba(250, 204, 21, 0.35);
  background: linear-gradient(135deg, rgba(30, 27, 10, 0.95), rgba(15, 23, 42, 0.98));
  box-shadow: 0 0 32px rgba(250, 204, 21, 0.08);
}
.score-hero-banner.good { border-color: rgba(34, 197, 94, 0.3); }
.score-hero-banner.encourage { border-color: rgba(59, 130, 246, 0.3); }
.score-hero-banner.improve { border-color: rgba(239, 68, 68, 0.25); }
.score-hero-main {
  display: flex;
  align-items: center;
  gap: 16px;
}
.score-hero-emoji { font-size: 42px; line-height: 1; }
.score-hero-label { margin: 0 0 4px; color: #94a3b8; font-size: 12px; }
.score-hero-value {
  font-size: 48px;
  font-weight: 800;
  color: #f8fafc;
  line-height: 1;
}
.score-hero-unit { margin-left: 4px; color: #94a3b8; font-size: 16px; font-weight: 600; }
.score-hero-message strong { display: block; color: #f8fafc; font-size: 18px; margin-bottom: 6px; }
.score-hero-message p { margin: 0 0 10px; color: #cbd5e1; font-size: 14px; line-height: 1.5; }
.score-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  font-size: 12px;
  color: #64748b;
}
.history-score-hint { color: #fde047; font-size: 12px; }
.highlight-captures-card {
  border-color: rgba(250, 204, 21, 0.25) !important;
}
.highlight-captures-header h2 { margin: 0 0 4px; color: #fde047; }
.highlight-captures-header p { margin: 0; color: #94a3b8; font-size: 13px; }
.highlight-captures-layout {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 16px;
  margin-top: 14px;
}
.highlight-thumb-list { display: grid; gap: 8px; }
.highlight-thumb-btn {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(250, 204, 21, 0.2);
  background: rgba(8, 13, 26, 0.5);
  color: #fde047;
  text-align: left;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}
.highlight-thumb-btn small { color: #94a3b8; font-size: 11px; font-weight: 400; }
.highlight-thumb-btn.active {
  border-color: rgba(250, 204, 21, 0.5);
  background: rgba(250, 204, 21, 0.1);
}

.session-meta-card h2 {
  margin: 0 0 12px;
}

.session-meta-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  font-size: 14px;
  color: #cbd5e1;
}

.mode-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 24px;
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.72);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-tab:hover {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.08);
}

.mode-tab.active {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.14);
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.2);
}

.mode-tab span {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
}

.mode-tab small {
  font-size: 12px;
  color: #94a3b8;
}

.mode-tab.active span {
  color: #86efac;
}

.ai-advice-card {
  margin-top: 8px;
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.96), rgba(15, 23, 42, 0.94));
  border-color: rgba(96, 165, 250, 0.28);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
}

.ai-advice-card-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.ai-advice-card-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.28);
}

.ai-advice-card-heading {
  flex: 1;
  min-width: 0;
}

.ai-advice-card-heading h2 {
  margin: 0;
  font-size: 22px;
  letter-spacing: -0.035em;
  color: #f8fafc;
}

.ai-advice-card-heading p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.5;
}

.voice-toggle-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 14px;
  border: 1px solid #334155;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.voice-toggle-pill:hover {
  border-color: #475569;
  color: #cbd5e1;
}

.voice-toggle-pill.active {
  border-color: #6366f1;
  background: rgba(79, 70, 229, 0.22);
  color: #c7d2fe;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.ai-advice-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: #cbd5e1;
  font-size: 13px;
}

.ai-advice-spinner {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  border: 2px solid rgba(148, 163, 184, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: ai-advice-spin 0.8s linear infinite;
}

.ai-advice-body {
  padding: 20px 22px;
  border-radius: 12px;
  background: rgba(2, 6, 23, 0.42);
  border: 1px solid #253047;
}

.ai-advice-body.is-loading {
  opacity: 0.55;
}

.ai-advice-body.is-lost {
  color: #94a3b8;
  font-style: italic;
}

@keyframes ai-advice-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1280px) {
  .feedback-stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .feedback-stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stat-card-btn {
    min-height: 78px;
    padding: 14px;
  }

  .stat-card-btn strong {
    font-size: 24px;
  }

  .stat-card-btn > span {
    width: 36px;
    height: 36px;
  }

  .ai-advice-card-header {
    flex-wrap: wrap;
  }

  .voice-toggle-pill {
    margin-left: 60px;
  }
}
</style>
