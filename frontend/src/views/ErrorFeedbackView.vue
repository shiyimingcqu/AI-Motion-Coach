<template>
  <div class="feedback-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("errorFeedback.title") }}</h1>
        <p>Real-time error detection and correction suggestions</p>
      </div>
    </header>

    <section class="feedback-mode-tabs">
      <button class="mode-tab" :class="{ active: mode === 'session' }" @click="switchMode('session')">
        <span>{{ $t("errorFeedback.currentSession") }}</span>
        <small v-if="sessionId">{{ sessionExerciseName }} · {{ sessionDate }}</small>
        <small v-else>{{ $t("errorFeedback.noSessionRecord") }}</small>
      </button>
      <button class="mode-tab" :class="{ active: mode === 'history' }" @click="switchMode('history')">
        <span>{{ $t("errorFeedback.historyFeedback") }}</span>
        <small>{{ $t("errorFeedback.historyFeedbackDesc") }}</small>
      </button>
    </section>

    <section class="feedback-stats-grid">
      <article class="feedback-stat-card critical">
        <span><AlertTriangle :size="18" /></span>
        <div><p>{{ $t("errorFeedback.critical") }}</p><strong>{{ stats.critical }}</strong></div>
      </article>
      <article class="feedback-stat-card warning">
        <span><Info :size="18" /></span>
        <div><p>{{ $t("errorFeedback.warning") }}</p><strong>{{ stats.warning }}</strong></div>
      </article>
      <article class="feedback-stat-card minor">
        <span><CheckCircle2 :size="18" /></span>
        <div><p>{{ $t("errorFeedback.minor") }}</p><strong>{{ stats.minor }}</strong></div>
      </article>
      <article class="feedback-stat-card correct">
        <span><ShieldAlert :size="18" /></span>
        <div><p>{{ $t("errorFeedback.correct") }}</p><strong>{{ stats.correct }}</strong></div>
      </article>
    </section>

    <section v-if="mode === 'session' && sessionId" class="ai-advice-section">
      <div class="ai-advice-panel">
        <div class="ai-advice-header">
          <div class="ai-advice-title">
            <Info :size="18" />
            <strong>{{ $t("errorFeedback.aiSuggestion") }}</strong>
          </div>
          <div class="ai-advice-actions">
            <label class="voice-toggle">
              <Volume2 :size="14" />
              <input type="checkbox" v-model="voiceEnabled" />
              {{ $t("errorFeedback.voiceBroadcast") }}
            </label>
            <button class="ai-advice-button" type="button" :disabled="aiLoading || detections.length === 0" @click="generateAiAdvice">
              {{ aiLoading ? $t("errorFeedback.generating") : $t("errorFeedback.generateAi") }}
            </button>
          </div>
        </div>
        <AiAdviceContent class="ai-advice-text" :content="aiAdvice" :placeholder="$t('errorFeedback.aiPlaceholder')" />
      </div>
    </section>

    <section v-if="mode === 'session' && sessionId" class="feedback-actions">
      <button class="primary-button" type="button" @click="goToSessions">
        <span>{{ $t("errorFeedback.viewSessionLog") }}</span>
      </button>
      <button class="secondary-button" type="button" @click="switchMode('history')">
        <span>{{ $t("errorFeedback.continueHistory") }}</span>
      </button>
    </section>

    <StateDisplay v-if="loading" type="loading" size="sm" />
    <StateDisplay v-else-if="mode === 'session' && detections.length === 0" type="empty" :title="$t('errorFeedback.noErrors')" :text="$t('errorFeedback.noErrorsText')" size="sm" />
    <StateDisplay v-else-if="mode === 'history' && historyGroups.length === 0" type="empty" :title="$t('errorFeedback.noHistory')" :text="$t('errorFeedback.noHistoryText')" size="sm" />

    <template v-if="mode === 'session' && detections.length > 0">
      <section class="feedback-card">
        <h2>{{ $t("errorFeedback.sessionErrors") }}</h2>
        <div class="error-detection-list">
          <article v-for="(item, idx) in detections" :key="idx" class="error-detection-row" :class="item.tone">
            <header>
              <div>
                <strong>{{ item.exercise }}</strong>
                <span>{{ item.type }}</span>
              </div>
              <time>{{ item.time }}</time>
            </header>
            <p>{{ item.problem }}</p>
            <div>
              <strong>{{ $t("errorFeedback.correctionSuggestion") }}:</strong>
              <span>{{ item.suggestion }}</span>
            </div>
          </article>
        </div>
      </section>

      <section class="feedback-card">
        <h2>{{ $t("errorFeedback.sessionAnalysis") }}</h2>
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

    <template v-if="mode === 'history' && historyGroups.length > 0">
      <section v-for="group in historyGroups" :key="group.sessionId" class="history-group">
        <div class="history-group-header">
          <div>
            <strong>{{ group.exerciseName }}</strong>
            <span class="history-date">{{ group.date }} · {{ $t("errorFeedback.errors", { count: group.feedbacks.length }) }}</span>
          </div>
          <span class="history-score" :class="scoreClass(group)">
            {{ $t("errorFeedback.correctRate", { valid: group.validCount, total: group.totalCount }) }}
          </span>
        </div>
        <div class="error-detection-list">
          <article v-for="(item, idx) in group.feedbacks" :key="idx" class="error-detection-row" :class="item.tone">
            <header>
              <div>
                <strong>{{ item.exercise }}</strong>
                <span>{{ item.type }}</span>
              </div>
              <time>{{ item.time }}</time>
            </header>
            <p>{{ item.problem }}</p>
            <div>
              <strong>{{ $t("errorFeedback.correctionSuggestion") }}:</strong>
              <span>{{ item.suggestion }}</span>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { AlertTriangle, CheckCircle2, Info, ShieldAlert, Volume2 } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import AiAdviceContent from "../components/AiAdviceContent.vue";
import { getFeedbacks } from "../api/feedback";
import { getSession, getSessions } from "../api/sessions";
import { useAiAdvice } from "../composables/useAiAdvice";

const { t } = useI18n();
type Mode = "session" | "history";

interface Detection {
  exercise: string;
  type: string;
  problem: string;
  suggestion: string;
  time: string;
  tone: string;
}

interface HistoryGroup {
  sessionId: string;
  date: string;
  exerciseName: string;
  validCount: number;
  totalCount: number;
  feedbacks: Detection[];
}

const route = useRoute();
const router = useRouter();
const { aiAdvice, aiLoading, voiceEnabled, requestAiAdvice, clearAdvice } = useAiAdvice();

const detections = ref<Detection[]>([]);
const historyGroups = ref<HistoryGroup[]>([]);
const loading = ref(true);
const mode = ref<Mode>("session");
const sessionId = ref("");
const sessionExercise = ref("squat");
const sessionDate = ref("");

const stats = ref({ critical: 0, warning: 0, minor: 0, correct: 0 });

const exerciseNames: Record<string, string> = {
  squat: t("exercises.squat"),
  push_up: t("exercises.push_up"),
  plank: t("exercises.plank"),
  jumping_jack: t("exercises.jumping_jack"),
};

const sessionExerciseName = computed(() => {
  return exerciseNames[sessionExercise.value] || sessionExercise.value;
});

const severityTone: Record<string, string> = {
  high: "critical",
  medium: "warning",
  low: "minor",
};

function scoreClass(group: HistoryGroup) {
  const ratio = group.totalCount > 0 ? group.validCount / group.totalCount : 0;
  if (ratio >= 0.8) return "score-good";
  if (ratio >= 0.5) return "score-warn";
  return "score-bad";
}

const mistakeByExercise = computed(() => {
  const map: Record<string, { exercise: string; tags: string[]; errors: number }> = {};
  for (const d of detections.value) {
    const key = d.exercise;
    if (!map[key]) map[key] = { exercise: key, tags: [], errors: 0 };
    map[key].errors += 1;
    if (!map[key].tags.includes(d.type)) map[key].tags.push(d.type);
  }
  const values = Object.values(map);
  const maxErrors = Math.max(...values.map(v => v.errors), 1);
  return values.map(v => ({
    ...v,
    percent: Math.round((v.errors / maxErrors) * 100),
  }));
});

function mapFeedbacks(fbItems: any[]): Detection[] {
  return fbItems.map((f: any) => ({
    exercise: exerciseNames[f.exercise] || f.exercise,
    type: f.issue,
    problem: f.issue,
    suggestion: f.suggestion || t("errorFeedback.tryAdjustPosture"),
    time: f.created_at?.slice(11, 19) || "--:--",
    tone: severityTone[f.severity] || "minor",
  }));
}

function calcStats(fbItems: any[]) {
  stats.value.critical = fbItems.filter((f: any) => f.severity === "high").length;
  stats.value.warning = fbItems.filter((f: any) => f.severity === "medium").length;
  stats.value.minor = fbItems.filter((f: any) => f.severity === "low").length;
}

async function loadSessionFeedbacks(sid: string) {
  loading.value = true;
  try {
    const [fbRes, sessionRes] = await Promise.allSettled([
      getFeedbacks({ session_id: sid, limit: 50 }),
      getSession(sid),
    ]);
    const fbItems = fbRes.status === "fulfilled" ? fbRes.value.items : [];
    if (fbItems.length > 0) {
      detections.value = mapFeedbacks(fbItems);
      calcStats(fbItems);
    } else {
      detections.value = [];
      stats.value = { critical: 0, warning: 0, minor: 0, correct: 0 };
    }
    if (sessionRes.status === "fulfilled" && sessionRes.value) {
      stats.value.correct = sessionRes.value.valid_count ?? 0;
      sessionExercise.value = sessionRes.value.exercise || "squat";
      sessionDate.value = sessionRes.value.created_at?.slice(0, 10) || "";
    }
  } finally {
    loading.value = false;
  }
}

async function loadHistoryFeedbacks() {
  loading.value = true;
  try {
    const [fbRes, sessionsRes] = await Promise.allSettled([
      getFeedbacks({ limit: 200 }),
      getSessions({ limit: 50 }),
    ]);
    const fbItems: any[] = fbRes.status === "fulfilled" ? fbRes.value.items : [];
    const sessions: any[] = sessionsRes.status === "fulfilled" ? (sessionsRes.value.items || []) : [];
    const sessionMap: Record<string, any> = {};
    for (const s of sessions) {
      sessionMap[s.session_id] = {
        date: s.created_at?.slice(0, 10) || "",
        exercise: exerciseNames[s.exercise] || s.exercise,
        validCount: s.valid_count ?? 0,
        totalCount: s.total_count ?? 0,
      };
    }
    const groupsMap: Record<string, any[]> = {};
    for (const f of fbItems) {
      const sid = f.session_id || "unknown";
      if (!groupsMap[sid]) groupsMap[sid] = [];
      groupsMap[sid].push(f);
    }
    historyGroups.value = Object.entries(groupsMap)
      .map(([sid, items]) => {
        const meta = sessionMap[sid] || { date: "", exercise: t("exercises.squat"), validCount: 0, totalCount: 0 };
        items.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        return { sessionId: sid, date: meta.date, exerciseName: meta.exercise, validCount: meta.validCount, totalCount: meta.totalCount, feedbacks: mapFeedbacks(items) };
      })
      .sort((a, b) => b.date.localeCompare(a.date));
    calcStats(fbItems);
    stats.value.correct = sessions.reduce((s: number, x: any) => s + (x.valid_count || 0), 0);
    detections.value = [];
  } finally {
    loading.value = false;
  }
}

async function generateAiAdvice() {
  if (detections.value.length === 0) {
    aiAdvice.value = t("errorFeedback.noEnoughData");
    return;
  }
  const errors = detections.value.map((d) => d.problem).filter(Boolean);
  const feedbacks = detections.value.map((d) => d.suggestion).filter(Boolean);
  await requestAiAdvice({
    exercise: sessionExercise.value,
    stage: "completed",
    errors: [...new Set(errors)],
    feedbacks: [...new Set(feedbacks)],
    metrics: {
      total_errors: errors.length,
      critical_count: stats.value.critical,
      warning_count: stats.value.warning,
      valid_count: stats.value.correct,
    },
  });
}

function switchMode(newMode: Mode) {
  if (newMode === mode.value) return;
  clearAdvice();
  mode.value = newMode;
  if (newMode === "session") { if (sessionId.value) loadSessionFeedbacks(sessionId.value); }
  else { loadHistoryFeedbacks(); }
}

function goToSessions() {
  if (sessionId.value) router.push({ path: "/sessions", query: { highlight: sessionId.value } });
}

onMounted(async () => {
  const querySession = route.query.session as string | undefined;
  if (querySession) {
    sessionId.value = querySession;
    mode.value = "session";
    await loadSessionFeedbacks(querySession);
  } else {
    mode.value = "session";
    try {
      const sessionsRes = await getSessions({ limit: 1 });
      const sessions = sessionsRes.items || [];
      if (sessions.length > 0) {
        const latest = sessions[0];
        sessionId.value = latest.session_id;
        await loadSessionFeedbacks(latest.session_id);
      } else {
        loading.value = false;
        detections.value = [];
        stats.value = { critical: 0, warning: 0, minor: 0, correct: 0 };
      }
    } catch { loading.value = false; }
  }
});
</script>

<style scoped>
/* All styles preserved from original */
.feedback-mode-tabs { display: flex; gap: 12px; margin-bottom: 24px; }
.mode-tab { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 16px 24px; border: 1px solid var(--line, #d5ded2); border-radius: 12px; background: var(--panel, #ffffff); cursor: pointer; transition: all 0.2s ease; }
.mode-tab:hover { border-color: var(--green, #1b7a57); background: rgba(27, 122, 87, 0.03); }
.mode-tab.active { border-color: var(--green, #1b7a57); background: rgba(27, 122, 87, 0.08); box-shadow: 0 0 0 1px rgba(27, 122, 87, 0.15); }
.mode-tab span { font-size: 15px; font-weight: 700; color: var(--ink, #16211b); }
.mode-tab small { font-size: 12px; color: var(--muted, #69756e); }
.mode-tab.active span { color: var(--green, #1b7a57); }
.ai-advice-section { margin-bottom: 24px; }
.ai-advice-panel { padding: 16px; border-radius: 12px; background: #f8fbff; border: 1px solid #e2e8f0; }
.ai-advice-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 12px; }
.ai-advice-title { display: flex; align-items: center; gap: 8px; color: #0f172a; font-size: 14px; }
.ai-advice-title strong { font-weight: 600; }
.ai-advice-actions { display: inline-flex; align-items: center; gap: 12px; }
.voice-toggle { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #94a3b8; cursor: pointer; }
.voice-toggle input { margin: 0; }
.ai-advice-button { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; border-radius: 8px; background: linear-gradient(135deg, #5b8cff, #4f46e5); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s ease; }
.ai-advice-button:hover:not(:disabled) { opacity: 0.9; }
.ai-advice-button:disabled { opacity: 0.6; cursor: not-allowed; }
.ai-advice-text { margin-top: 8px; }
.feedback-actions { display: flex; gap: 12px; margin-bottom: 24px; }
.feedback-actions .primary-button { display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; border: none; border-radius: 9px; background: linear-gradient(135deg, #5b8cff, #4f46e5); color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.feedback-actions .secondary-button { display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; border: 1px solid var(--line, #d5ded2); border-radius: 9px; background: var(--panel, #ffffff); color: var(--ink, #16211b); font-size: 14px; font-weight: 600; cursor: pointer; }
.feedback-actions .secondary-button:hover { background: rgba(27, 122, 87, 0.05); border-color: var(--green, #1b7a57); }
.history-group { margin-bottom: 28px; padding: 16px; border: 1px solid var(--line, #d5ded2); border-radius: 12px; background: var(--panel, #ffffff); }
.history-group-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed var(--line, #d5ded2); }
.history-group-header strong { font-size: 15px; color: var(--ink, #16211b); display: block; }
.history-date { font-size: 12px; color: var(--muted, #69756e); margin-top: 2px; display: block; }
.history-score { font-size: 13px; font-weight: 600; padding: 4px 10px; border-radius: 6px; white-space: nowrap; }
.score-good { color: #16a34a; background: #dcfce7; }
.score-warn { color: #ca8a04; background: #fef9c3; }
.score-bad { color: #dc2626; background: #fee2e2; }
</style>
