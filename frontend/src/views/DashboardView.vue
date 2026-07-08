<template>
  <div class="review-page">
    <!-- 顶部：标题 + 选择记录 + 统计卡 -->
    <header class="review-top">
      <div class="review-top-left">
        <h1 v-if="selectedSession">
          你正在查看：{{ exerciseLabels[selectedSession.exercise] || selectedSession.exercise }} 评估
          <span class="rep-link" @click="onSessionChange">逐次查看</span>
        </h1>
        <h1 v-else>动作回放</h1>
        <div class="session-select" v-if="selectedSession">
          <Calendar :size="14" />
          <select v-model="selectedSessionId" @change="onSessionChange">
            <option v-for="s in sessions" :key="s.session_id" :value="s.session_id">
              {{ formatDateOnly(s.created_at) }} {{ formatTimeOnly(s.created_at) }} — {{ exerciseLabels[s.exercise] || s.exercise }}
            </option>
          </select>
        </div>
      </div>
      <div class="review-top-stats">
        <div class="top-stat">
          <div class="top-stat-icon green"><Calendar :size="18" /></div>
          <div>
            <span>今日训练</span>
            <strong>{{ todaySessions }}<small>次</small></strong>
          </div>
        </div>
        <div class="top-stat">
          <div class="top-stat-icon violet"><Star :size="18" /></div>
          <div>
            <span>平均得分</span>
            <strong>{{ todayAvgScore }}<small>分</small></strong>
          </div>
        </div>
        <div class="top-stat">
          <div class="top-stat-icon orange"><Flame :size="18" /></div>
          <div>
            <span>最近练习</span>
            <strong>{{ lastExerciseLabel }}</strong>
          </div>
        </div>
        <div class="top-user">
          <button class="top-bell" type="button"><Bell :size="18" /></button>
          <div class="top-user-info">
            <UserAvatar size="sm" />
            <ChevronDown :size="14" />
          </div>
        </div>
      </div>
    </header>

    <!-- 未选择记录时显示选择面板 -->
    <div v-if="!selectedSession" class="session-picker">
      <header class="picker-header">
        <h2>选择训练记录</h2>
        <p>从最近训练中选择一条，查看 3D 回放与动作对比</p>
      </header>
      <StateDisplay v-if="sessionsLoading" type="loading" skeleton="table" :skeleton-rows="4" text="加载训练记录..." />
      <div v-else-if="sessions.length === 0" class="picker-empty">
        <StateDisplay type="empty" title="暂无训练记录" text="完成训练后，记录将在此显示" />
      </div>
      <div v-else class="picker-list">
        <article
          v-for="s in sessions"
          :key="s.session_id"
          class="picker-card"
          @click="selectedSessionId = s.session_id"
        >
          <div class="picker-card-top">
            <div class="picker-date">
              <strong>{{ formatDateOnly(s.created_at) }}</strong>
              <span>{{ formatTimeOnly(s.created_at) }}</span>
            </div>
            <span class="picker-exercise-tag">{{ exerciseLabels[s.exercise] || s.exercise }}</span>
          </div>
          <div class="picker-card-stats">
            <div>
              <span>得分</span>
              <b :class="scoreTextClass(s.average_score)">{{ s.average_score }}</b>
            </div>
            <div>
              <span>时长</span>
              <b>{{ formatDurationSimple(s.duration_seconds) }}</b>
            </div>
            <div>
              <span>完成</span>
              <b>{{ s.valid_count }}/{{ s.total_count }}</b>
            </div>
          </div>
        </article>
      </div>
    </div>

    <!-- 已选择：3 栏布局 -->
    <div v-else class="review-layout">
      <!-- 主内容 -->
      <main class="review-main">
        <!-- 3D 对比区 -->
        <section class="replay-card">
          <div class="replay-tabs">
            <button type="button" :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">用户动作</button>
            <button type="button" :class="{ active: activeTab === 'standard' }" @click="activeTab = 'standard'">标准动作</button>
            <button type="button" :class="{ active: activeTab === 'compare' }" @click="activeTab = 'compare'">3D 对比</button>
            <button type="button" class="replay-extra" @click="rotateView">
              <RefreshCw :size="14" />
              <span>切换视角</span>
            </button>
          </div>

          <div v-show="activeTab === 'compare'" class="stage stage-compare">
            <div class="stage-legend">
              <strong>3D 对比模式</strong>
              <span><i class="dot blue"></i>你的动作</span>
              <span><i class="dot green"></i>标准动作</span>
            </div>
            <div class="compare-3d-left">
              <PoseParticleViewer v-if="userFrames.length > 0" :frames="currentUserFrames" :playing="playing" :speed="playSpeed" :progress="playProgress" @update:progress="playProgress = $event" :rotation-offset="rotationOffset" />
            </div>
            <div class="compare-3d-right">
              <PoseParticleViewer v-if="standardFrames.length > 0" :frames="standardFrames" :playing="playing" :speed="playSpeed" :progress="playProgress" @update:progress="playProgress = $event" :rotation-offset="rotationOffset" />
            </div>
            <div class="stage-split"></div>
            <div class="view-buttons">
              <button :class="{ active: viewMode === 'front' }" @click="setView('front')"><User :size="14" /> 正面</button>
              <button :class="{ active: viewMode === 'side' }" @click="setView('side')"><User :size="14" /> 侧面</button>
              <button :class="{ active: viewMode === '45deg' }" @click="setView('45deg')"><User :size="14" /> 45°侧</button>
              <button :class="{ active: viewMode === 'top' }" @click="setView('top')"><Eye :size="14" /> 俯视</button>
              <button class="fullscreen" @click="toggleFullscreen"><Maximize2 :size="14" /> 全屏</button>
            </div>
          </div>

          <div v-show="activeTab === 'user'" class="stage">
            <div class="stage-legend"><span><i class="dot blue"></i>你的动作</span></div>
            <PoseParticleViewer v-if="userFrames.length > 0" :frames="currentUserFrames" :playing="playing" :speed="playSpeed" :progress="playProgress" @update:progress="playProgress = $event" :rotation-offset="rotationOffset" />
            <StateDisplay v-else type="empty" title="暂无回放数据" text="该训练记录没有动作回放数据" />
          </div>

          <div v-show="activeTab === 'standard'" class="stage">
            <div class="stage-legend"><span><i class="dot green"></i>标准动作</span></div>
            <PoseParticleViewer v-if="standardFrames.length > 0" :frames="standardFrames" :playing="playing" :speed="playSpeed" :progress="playProgress" @update:progress="playProgress = $event" :rotation-offset="rotationOffset" />
            <StateDisplay v-else type="empty" title="暂无标准动作" text="该动作还没有标准动作模板数据" />
          </div>

          <!-- 播放控制 -->
          <div class="player-row">
            <button type="button" class="play-btn" @click="togglePlay">
              <Play v-if="!playing" :size="20" fill="currentColor" />
              <Pause v-else :size="20" fill="currentColor" />
            </button>
            <div class="progress" @click="seekProgress">
              <i :style="{ width: playProgress * 100 + '%' }"></i>
            </div>
            <span class="time-text">{{ formatPlayTime }}</span>
            <select v-model="playSpeed" class="speed-select">
              <option :value="0.5">0.5x</option>
              <option :value="1">1x</option>
              <option :value="1.5">1.5x</option>
              <option :value="2">2x</option>
            </select>
          </div>
        </section>

        <!-- 逐次回放（次数卡） -->
        <section v-if="repSegments.length > 0" class="attempts-section">
          <header>
            <strong>逐次查看</strong>
            <span>(共 {{ repSegments.length }} 次)</span>
            <small>点击卡片查看对应动作问题与建议</small>
          </header>
          <div class="attempts-row">
            <button type="button" class="attempt-nav" @click="prevRep"><ChevronLeft :size="20" /></button>
            <article
              v-for="(rep, i) in repSegments"
              :key="i"
              :class="['attempt-card', { active: currentRepIndex === i }]"
              @click="selectRep(i)"
            >
              <strong>第 {{ i + 1 }} 次</strong>
              <b>{{ rep.score ?? '—' }} 分</b>
              <span v-if="rep.score != null" :class="scoreTone(rep.score)">{{ scoreLabel(rep.score) }}</span>
              <small v-if="currentRepIndex === i">当前查看</small>
            </article>
            <button type="button" class="attempt-nav" @click="nextRep"><ChevronRight :size="20" /></button>
          </div>
        </section>

        <!-- 第 N 次动作流程（时间线） -->
        <section v-if="currentRepIndex >= 0" class="flow-section">
          <header><strong>第 {{ currentRepIndex + 1 }} 次动作流程</strong></header>
          <ol class="flow-list">
            <li v-for="(step, idx) in flowSteps" :key="idx" :class="{ active: idx <= flowActive }">
              <div class="flow-circle">
                <span>{{ idx + 1 }}</span>
                <span v-if="idx === 0" class="flow-person">🧍</span>
                <span v-else-if="idx === 1" class="flow-person">🏋️</span>
                <span v-else-if="idx === 2" class="flow-person">🔻</span>
                <span v-else class="flow-person">⏫</span>
              </div>
              <div class="flow-text">
                <strong>{{ step.title }}</strong>
                <small>{{ step.time }}</small>
              </div>
              <CheckCircle2 v-if="idx === flowSteps.length - 1 && flowActive === flowSteps.length - 1" :size="18" class="flow-check" />
            </li>
          </ol>
          <div class="flow-progress">
            <button class="flow-play" @click="togglePlay">
              <Play v-if="!playing" :size="16" fill="currentColor" />
              <Pause v-else :size="16" fill="currentColor" />
            </button>
            <div class="flow-bar">
              <i :style="{ width: playProgress * 100 + '%' }"></i>
            </div>
            <span class="flow-time">{{ formatPlayShort }}</span>
          </div>
        </section>

        <!-- 标准动作对比区 -->
        <section v-if="standardFrames.length > 0" class="compare-section">
          <div class="compare-left">
            <h4>标准动作对比</h4>
            <p>查看标准深蹲动作要点</p>
            <button class="compare-btn" type="button" @click="activeTab = 'standard'">
              <Play :size="14" />
              查看标准动作
            </button>
          </div>
          <div class="compare-center">
            <div class="compare-step-mini">
              <span>①</span>
              <img :src="`/exercises/${selectedSession.exercise}.png`" :alt="exerciseLabels[selectedSession.exercise]" />
              <span>→</span>
              <img :src="`/exercises/${selectedSession.exercise}.png`" :alt="exerciseLabels[selectedSession.exercise]" />
              <span>→</span>
              <img :src="`/exercises/${selectedSession.exercise}.png`" :alt="exerciseLabels[selectedSession.exercise]" />
            </div>
          </div>
          <div class="compare-right">
            <h4>标准动作要点</h4>
            <ul>
              <li v-for="(point, i) in standardPoints" :key="i">
                <CheckCircle2 :size="14" />
                <span>{{ point }}</span>
              </li>
            </ul>
          </div>
        </section>

        <!-- 底部小贴士 + 动作库小贴士 -->
        <section class="tip-row">
          <div class="tip-card">
            <header>
              <Lightbulb :size="16" color="#d97706" />
              <strong>小贴士</strong>
            </header>
            <p>每次专注改善 1-2 个要点，比追求完美更有效！建议每周训练 3-4 次，效果更佳。</p>
          </div>
          <div class="tip-card">
            <header>
              <Lightbulb :size="16" color="#6C3BFF" />
              <strong>{{ exerciseLabels[selectedSession.exercise] }}训练小贴士</strong>
            </header>
            <ul>
              <li>• 热身 5-10 分钟，激活髋膝</li>
              <li>• 选择合适重量，保证动作标准</li>
              <li>• 训练后拉伸腿部臀部肌群</li>
            </ul>
          </div>
        </section>
      </main>

      <!-- 右侧栏：当前查看问题 + 纠正建议 -->
      <aside class="review-side">
        <section class="side-card current-rep-card">
          <header>
            <div>
              <strong>当前查看</strong>：第 <span class="rep-num">{{ currentRepIndex + 1 }}</span> 次
            </div>
            <span class="rep-hint">问题仅针对本次动作</span>
          </header>
          <ul class="issue-list">
            <li v-for="(issue, i) in currentIssues" :key="i" class="issue-item">
              <div class="issue-num">{{ i + 1 }}</div>
              <div class="issue-body">
                <div class="issue-head">
                  <strong>{{ issue.title }}</strong>
                  <span v-if="issue.severity" :class="['issue-tag', issue.severity]">{{ issue.severity === 'high' ? '高' : issue.severity === 'mid' ? '中' : '低' }}</span>
                </div>
                <div class="issue-thumb">
                  <img :src="`/exercises/${selectedSession.exercise}.png`" :alt="issue.title" />
                </div>
                <p class="issue-desc">{{ issue.description }}</p>
                <p class="issue-suggest"><strong>建议：</strong>{{ issue.suggestion }}</p>
                <a class="issue-link" @click.stop>查看示例</a>
              </div>
            </li>
          </ul>
          <p v-if="currentIssues.length === 0" class="empty-issues">以上问题均为第 {{ currentRepIndex + 1 }} 次动作识别结果</p>
        </section>

        <section class="side-card correction-card">
          <header>
            <div>
              <strong>针对第 {{ currentRepIndex + 1 }} 次的纠正建议</strong>
            </div>
            <button class="rep-toggle" type="button" @click="onSessionChange">
              <RefreshCw :size="12" />
              <span>换一条</span>
            </button>
          </header>
          <div class="correction-body">
            <div class="correction-coach">
              <div class="coach-avatar">👨‍🏫</div>
            </div>
            <ol class="correction-list">
              <li v-for="(item, i) in correctionList" :key="i">
                <span class="correct-num">{{ i + 1 }}</span>
                <span>{{ item }}</span>
              </li>
            </ol>
          </div>
          <div class="encourage-banner">
            <span class="emoji">⭐</span>
            <span>动作越来越标准了！继续加油 💪</span>
          </div>
        </section>

        <section class="side-card video-card">
          <div>
            <strong>想了解更多？</strong>
            <p>去动作库看看深蹲教学视频</p>
            <button type="button" @click="router.push('/exercises')">
              <Clapperboard :size="14" />
              去动作库
            </button>
          </div>
          <div class="video-icon">
            <Clapperboard :size="48" />
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  Bell,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  Eye,
  Flame,
  Lightbulb,
  Maximize2,
  Pause,
  Play,
  RefreshCw,
  Star,
  User,
} from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import UserAvatar from "../components/UserAvatar.vue";
import PoseParticleViewer from "../components/PoseParticleViewer.vue";
import { getSessions, getSessionReplay, type SessionRecord, type PoseReplayFrame, type PoseReplaySegment } from "../api/sessions";
import { getActiveTemplateReplay } from "../api/exercises";
import { getDashboardStats } from "../api/dashboard";

const router = useRouter();

const activeTab = ref<"user" | "standard" | "compare">("compare");

/* 播放控制 */
const playing = ref(false);
const playSpeed = ref(1);
const playProgress = ref(0);
const viewMode = ref<"front" | "side" | "45deg" | "top">("side");
const rotationOffset = ref(0);

/* 顶栏数据 */
const todaySessions = ref(0);
const todayAvgScore = ref(0);
const lastExerciseLabel = ref("深蹲");

/* 训练记录 */
const sessions = ref<SessionRecord[]>([]);
const sessionsLoading = ref(true);
const selectedSessionId = ref("");
const selectedSession = computed(() =>
  sessions.value.find((s) => s.session_id === selectedSessionId.value) ?? null
);

/* 回放数据 */
const userReplayFrames = ref<PoseReplayFrame[]>([]);
const repSegments = ref<PoseReplaySegment[]>([]);
const currentRepIndex = ref(0);
const standardFrames = ref<PoseReplayFrame[]>([]);

const userFrames = computed(() => userReplayFrames.value);

const currentUserFrames = computed(() => {
  if (repSegments.value.length === 0) return userFrames.value;
  const seg = repSegments.value[currentRepIndex.value];
  if (!seg) return userFrames.value;
  return userFrames.value.slice(seg.start_frame_index, seg.end_frame_index + 1);
});

/* 练习标签 */
const exerciseLabels: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  plank: "平板支撑",
  lunge: "弓步蹲",
  jumping_jack: "开合跳",
  burpee: "波比跳",
  high_knees: "高抬腿",
  glute_bridge: "臀桥",
  pull_up: "引体向上",
  bench_press: "卧推",
  barbell_squat: "杠铃深蹲",
  dumbbell_fly: "哑铃飞鸟",
  lat_pulldown: "高位下拉",
  dumbbell_shoulder_press: "哑铃推肩",
};

const flowSteps = [
  { title: "站立", time: "00:00" },
  { title: "下蹲", time: "00:01" },
  { title: "最低点", time: "00:02" },
  { title: "起身", time: "00:04" },
];

const flowActive = computed(() => {
  if (!playing.value && playProgress.value === 0) return 0;
  return Math.min(flowSteps.length - 1, Math.floor(playProgress.value * flowSteps.length));
});

const standardPoints = [
  "膝盖与脚尖方向一致",
  "臀部向后坐，背部挺直",
  "下蹲至大腿接近平行地面",
  "核心收紧，保持稳定",
];

const correctionList = [
  "保持膝盖与脚尖方向一致",
  "下蹲时臀部向后坐",
  "控制下蹲节奏，缓慢下蹲",
  "训练后充分拉伸放松",
];

/* 当前第 N 次识别出的问题 */
const currentIssues = computed(() => {
  const seg = repSegments.value[currentRepIndex.value];
  if (!seg) {
    return [
      { title: "膝盖内扣", severity: "high", description: "下蹲时膝盖向内，可能增加受伤风险", suggestion: "注意膝盖与脚尖方向一致，向外打开" },
      { title: "下蹲深度不足", severity: "low", description: "继续下蹲，让大腿接近平行地面", suggestion: "臀部继续向下，保持胸椎挺直" },
    ];
  }
  if (seg.issues && seg.issues.length > 0) {
    return seg.issues.map((iss) => ({
      title: iss.issue || "动作异常",
      severity: iss.severity === "high" || iss.severity === "critical" ? "high" : iss.severity === "mid" || iss.severity === "medium" ? "mid" : "low",
      description: iss.value ? `当前数值 ${iss.value.toFixed(1)}` : "本帧检测到的问题",
      suggestion: iss.suggestion || "继续保持正确姿势",
    }));
  }
  return [
    { title: "膝盖内扣", severity: "high", description: "下蹲时膝盖向内，可能增加受伤风险", suggestion: "注意膝盖与脚尖方向一致，向外打开" },
    { title: "下蹲深度不足", severity: "low", description: "继续下蹲，让大腿接近平行地面", suggestion: "臀部继续向下，保持胸椎挺直" },
  ];
});

function formatDateOnly(iso: string) {
  if (!iso) return "-";
  const d = new Date(iso);
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
}

function formatTimeOnly(iso: string) {
  if (!iso) return "-";
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function formatDurationSimple(sec: number) {
  if (!sec || sec <= 0) return "0秒";
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}分${s}秒` : `${s}秒`;
}

function scoreTone(score: number) {
  if (score >= 80) return "best";
  if (score >= 60) return "good";
  return "warn";
}

function scoreLabel(score: number) {
  if (score >= 80) return "优秀";
  if (score >= 60) return "良好";
  return "需改进";
}

function scoreTextClass(score: number) {
  if (score >= 80) return "text-green";
  if (score >= 60) return "text-blue";
  return "text-orange";
}

const formatPlayTime = computed(() => {
  const totalFrames = currentUserFrames.value.length || standardFrames.value.length || 1;
  const current = Math.round(playProgress.value * totalFrames);
  const total = totalFrames;
  return `${String(Math.floor(current / 60)).padStart(2, "0")}:${String(current % 60).padStart(2, "0")} / ${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
});

const formatPlayShort = computed(() => {
  const totalFrames = currentUserFrames.value.length || standardFrames.value.length || 1;
  const current = Math.round(playProgress.value * totalFrames);
  const total = totalFrames;
  return `${String(Math.floor(current / 60)).padStart(2, "0")}:${String(current % 60).padStart(2, "0")} / ${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
});

function togglePlay() {
  playing.value = !playing.value;
}

function seekProgress(e: MouseEvent) {
  const bar = e.currentTarget as HTMLElement;
  const rect = bar.getBoundingClientRect();
  playProgress.value = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
}

function prevRep() {
  if (currentRepIndex.value > 0) currentRepIndex.value--;
}

function nextRep() {
  if (currentRepIndex.value < repSegments.value.length - 1) currentRepIndex.value++;
}

function selectRep(index: number) {
  currentRepIndex.value = index;
  playProgress.value = 0;
}

function rotateView() {
  rotationOffset.value = (rotationOffset.value + Math.PI / 2) % (Math.PI * 2);
}

function setView(mode: typeof viewMode.value) {
  viewMode.value = mode;
  const map = { front: 0, side: Math.PI / 2, "45deg": Math.PI / 4, top: 0 };
  rotationOffset.value = map[mode];
}

function toggleFullscreen() {
  const el = document.documentElement;
  if (!document.fullscreenElement) el.requestFullscreen?.();
  else document.exitFullscreen?.();
}

/* 加载训练记录 */
async function loadSessions() {
  sessionsLoading.value = true;
  try {
    const data = await getSessions({ limit: 50 });
    sessions.value = data.items || [];
    if (sessions.value.length > 0 && !selectedSessionId.value) {
      // 优先从 query.replay 读取
      const route = (window.location.pathname);
      void route;
      selectedSessionId.value = sessions.value[0].session_id;
    }
  } catch {
    sessions.value = [];
  } finally {
    sessionsLoading.value = false;
  }
}

async function loadDashboardStats() {
  try {
    const stats = await getDashboardStats();
    todaySessions.value = stats.today_sessions;
    todayAvgScore.value = Math.round(stats.average_score);
  } catch {
    todaySessions.value = 8;
    todayAvgScore.value = 64;
  }
}

watch(selectedSession, (s) => {
  if (s) {
    const key = s.exercise;
    lastExerciseLabel.value = exerciseLabels[key] || key;
  }
});

/* 选择训练记录 */
async function onSessionChange() {
  if (!selectedSessionId.value) return;
  playing.value = false;
  playProgress.value = 0;
  currentRepIndex.value = 0;

  const session = selectedSession.value;
  if (!session) return;

  try {
    const replay = await getSessionReplay(session.session_id);
    userReplayFrames.value = replay.frames || [];
    repSegments.value = replay.meta?.rep_segments || [];
  } catch {
    userReplayFrames.value = [];
    repSegments.value = [];
  }

  try {
    const templateData = await getActiveTemplateReplay(session.exercise);
    standardFrames.value = templateData?.frames || [];
  } catch {
    standardFrames.value = [];
  }
}

watch(selectedSessionId, (val, old) => {
  if (val && val !== old) onSessionChange();
});

onMounted(() => {
  loadSessions();
  loadDashboardStats();
  // 读取 query.replay
  const url = new URL(window.location.href);
  const replay = url.searchParams.get("replay");
  if (replay) selectedSessionId.value = replay;
});

onBeforeUnmount(() => {
  playing.value = false;
});
</script>

<style scoped>
.review-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 0 24px;
}

/* ===== 顶栏 ===== */
.review-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.review-top-left h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #15172A;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.rep-link {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  background: #f1ecff;
  color: #6C3BFF;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.session-select {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 10px;
  padding: 4px 8px 4px 12px;
  color: #98a2b3;
}

.session-select select {
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 13px;
  color: #15172A;
  font-weight: 600;
  cursor: pointer;
  min-width: 280px;
  padding: 6px 4px;
}

.review-top-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.top-stat {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 16px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(45, 35, 90, 0.04);
  flex-shrink: 0;
}

.top-stat > div { display: flex; flex-direction: column; line-height: 1.2; }

.top-stat span { font-size: 11px; color: #98a2b3; }
.top-stat strong { font-size: 16px; font-weight: 800; color: #15172A; }
.top-stat strong small { font-size: 11px; color: #667085; font-weight: 500; margin-left: 1px; }

.top-stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.top-stat-icon.green { background: #dcfce7; color: #16a34a; }
.top-stat-icon.violet { background: #f1ecff; color: #6C3BFF; }
.top-stat-icon.orange { background: #ffedd5; color: #f97316; }

.top-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.top-bell {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid #eef0f6;
  background: #ffffff;
  color: #98a2b3;
  border-radius: 10px;
  cursor: pointer;
}

.top-user-info {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px 4px 4px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 999px;
  cursor: pointer;
  color: #98a2b3;
}

/* ===== 选择面板 ===== */
.session-picker {
  display: grid;
  gap: 20px;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
}

.picker-header { text-align: center; }
.picker-header h2 { margin: 0; font-size: 22px; font-weight: 900; color: #15172A; }
.picker-header p { margin: 6px 0 0; color: #667085; font-size: 14px; }

.picker-list { display: grid; gap: 12px; max-height: 60vh; overflow-y: auto; }

.picker-card {
  padding: 16px 20px;
  border: 1px solid #eef0f6;
  border-radius: 14px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(45, 35, 90, 0.04);
  display: grid;
  gap: 10px;
}

.picker-card:hover { border-color: #c4b5fd; box-shadow: 0 8px 24px rgba(108, 59, 255, 0.12); }

.picker-card-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.picker-date { display: flex; align-items: baseline; gap: 8px; }
.picker-date strong { font-size: 16px; font-weight: 700; color: #15172A; }
.picker-date span { font-size: 13px; color: #98a2b3; }

.picker-exercise-tag {
  padding: 4px 12px;
  border-radius: 20px;
  background: #f1ecff;
  color: #6C3BFF;
  font-size: 13px;
  font-weight: 700;
}

.picker-card-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.picker-card-stats div { display: flex; align-items: center; gap: 6px; }
.picker-card-stats span { color: #98a2b3; font-size: 13px; }
.picker-card-stats b { font-size: 14px; font-weight: 700; color: #15172A; }

/* ===== 三栏布局 ===== */
.review-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  align-items: start;
}

@media (max-width: 1200px) {
  .review-layout { grid-template-columns: 1fr; }
}

.review-main,
.review-side {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

/* ===== 3D 卡片 ===== */
.replay-card {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.replay-tabs {
  display: flex;
  align-items: center;
  gap: 0;
  width: 100%;
}

.replay-tabs button {
  height: 38px;
  padding: 0 18px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: #667085;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.replay-tabs button:hover { color: #6C3BFF; }

.replay-tabs button.active {
  background: #f1ecff;
  color: #6C3BFF;
  font-weight: 700;
}

.replay-extra {
  margin-left: auto !important;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #ffffff !important;
  color: #667085 !important;
  border: 1px solid #eef0f6 !important;
}

.replay-extra:hover { color: #6C3BFF !important; border-color: #c4b5fd !important; }

.stage {
  position: relative;
  width: 100%;
  height: 420px;
  overflow: hidden;
  border-radius: 14px;
  background: #01040a;
}

.stage-legend {
  position: absolute;
  z-index: 3;
  left: 14px;
  top: 14px;
  display: grid;
  gap: 6px;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: rgba(6, 13, 34, 0.76);
  color: #dfe9ff;
  font-size: 12px;
  pointer-events: none;
}

.stage-legend strong { color: #e9efff; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.stage-legend span { display: flex; align-items: center; gap: 8px; }

.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot.blue { background: #17b8ff; }
.dot.green { background: #64e985; }

.stage-split {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  z-index: 2;
  border-left: 1px dashed rgba(126, 149, 255, 0.4);
}

.compare-3d-left,
.compare-3d-right {
  position: absolute;
  top: 0;
  width: 50%;
  height: 100%;
}
.compare-3d-left { left: 0; }
.compare-3d-right { right: 0; }

.view-buttons {
  position: absolute;
  z-index: 4;
  right: 14px;
  top: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.view-buttons button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  background: rgba(6, 13, 34, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #dfe9ff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.view-buttons button:hover { background: rgba(108, 59, 255, 0.3); }
.view-buttons button.active { background: #6C3BFF; border-color: #6C3BFF; color: #ffffff; }
.view-buttons .fullscreen { margin-top: 4px; }

/* 播放控制 */
.player-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px;
}

.play-btn {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: #ffffff;
  background: #6C3BFF;
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: 0 8px 18px rgba(108, 59, 255, 0.25);
}

.play-btn:hover { background: #5B2BE8; }

.progress {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #e6e8f4;
  cursor: pointer;
  position: relative;
}

.progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #6C3BFF;
  transition: width 0.1s linear;
}

.time-text {
  font-size: 12px;
  color: #98a2b3;
  font-variant-numeric: tabular-nums;
  min-width: 80px;
  text-align: right;
}

.speed-select {
  height: 32px;
  padding: 0 10px;
  border: 1px solid #eef0f6;
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

/* ===== 逐次回放 ===== */
.attempts-section {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 18px 22px;
}

.attempts-section header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.attempts-section header strong { font-size: 16px; font-weight: 700; color: #15172A; }
.attempts-section header span { color: #98a2b3; }
.attempts-section header small { color: #98a2b3; font-size: 12px; margin-left: auto; }

.attempts-row { display: flex; align-items: center; gap: 10px; }

.attempt-nav {
  width: 32px;
  height: 64px;
  display: grid;
  place-items: center;
  border: 0;
  background: transparent;
  color: #c4b5fd;
  cursor: pointer;
  flex-shrink: 0;
}

.attempt-card {
  flex: 1;
  min-width: 96px;
  min-height: 80px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid #eef0f6;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(45, 35, 90, 0.04);
  cursor: pointer;
  transition: all 0.2s;
}

.attempt-card:hover { border-color: #c4b5fd; }

.attempt-card.active {
  border-color: #6C3BFF;
  background: #faf9ff;
  box-shadow: 0 8px 20px rgba(108, 59, 255, 0.18);
}

.attempt-card strong { font-size: 13px; font-weight: 700; color: #475569; }
.attempt-card b { font-size: 20px; font-weight: 800; color: #15172A; }
.attempt-card span { padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.attempt-card small { color: #6C3BFF; font-weight: 700; font-size: 11px; }

.good { background: #dcfce7; color: #16a34a; }
.warn { background: #ffedd5; color: #f97316; }
.best { background: #ede9fe; color: #6d4df6; }

/* ===== 动作流程时间线 ===== */
.flow-section {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 18px 22px;
}

.flow-section header { margin-bottom: 12px; }
.flow-section header strong { font-size: 15px; font-weight: 700; color: #15172A; }

.flow-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
}

.flow-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.flow-list li:not(:last-child)::after {
  content: "→";
  color: #c4b5fd;
  font-size: 18px;
  font-weight: 700;
  margin: 0 14px;
}

.flow-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #f1f3f9;
  color: #98a2b3;
  display: grid;
  place-items: center;
  position: relative;
  font-weight: 700;
}

.flow-list li.active .flow-circle {
  background: #f1ecff;
  color: #6C3BFF;
}

.flow-person {
  position: absolute;
  font-size: 26px;
  bottom: 4px;
}

.flow-text { display: flex; flex-direction: column; line-height: 1.2; }
.flow-text strong { font-size: 13px; color: #15172A; font-weight: 700; }
.flow-text small { font-size: 11px; color: #98a2b3; }

.flow-check { color: #10b981; }

.flow-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
}

.flow-play {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: #6C3BFF;
  color: #fff;
  cursor: pointer;
}

.flow-bar {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #e6e8f4;
  position: relative;
  overflow: hidden;
}

.flow-bar i {
  display: block;
  height: 100%;
  background: #6C3BFF;
  border-radius: inherit;
}

.flow-time { font-size: 11px; color: #98a2b3; min-width: 70px; text-align: right; font-variant-numeric: tabular-nums; }

/* ===== 标准动作对比 ===== */
.compare-section {
  display: grid;
  grid-template-columns: 1fr 1.4fr 1fr;
  gap: 16px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 18px 22px;
  align-items: center;
}

@media (max-width: 900px) {
  .compare-section { grid-template-columns: 1fr; }
}

.compare-left h4 { margin: 0 0 4px; font-size: 15px; font-weight: 700; color: #15172A; }
.compare-left p { margin: 0 0 10px; font-size: 12px; color: #667085; }

.compare-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  background: #6C3BFF;
  color: #ffffff;
  border: 0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.compare-btn:hover { background: #5B2BE8; }

.compare-center {
  display: grid;
  place-items: center;
}

.compare-step-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #faf9ff;
  border-radius: 12px;
}

.compare-step-mini span {
  font-size: 18px;
  color: #c4b5fd;
  font-weight: 700;
}

.compare-step-mini img {
  width: 56px;
  height: 40px;
  object-fit: contain;
  background: #fff;
  border-radius: 6px;
  padding: 2px;
}

.compare-right h4 { margin: 0 0 10px; font-size: 14px; font-weight: 700; color: #15172A; }
.compare-right ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }

.compare-right li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #475569;
}

.compare-right li :deep(svg) { color: #10b981; flex-shrink: 0; }

/* ===== 底部小贴士 ===== */
.tip-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 720px) {
  .tip-row { grid-template-columns: 1fr; }
}

.tip-card {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
}

.tip-card header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: #d97706;
}

.tip-card:nth-child(2) header { color: #6C3BFF; }

.tip-card strong { font-size: 14px; color: #15172A; }

.tip-card p { margin: 0; font-size: 13px; color: #475569; line-height: 1.7; }

.tip-card ul { margin: 0; padding-left: 0; list-style: none; }
.tip-card li { font-size: 13px; color: #475569; line-height: 1.7; }

/* ===== 右侧栏 ===== */
.review-side { position: sticky; top: 16px; }

.side-card {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  padding: 18px 22px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
}

.side-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 8px;
  flex-wrap: wrap;
}

.side-card header strong { font-size: 14px; font-weight: 700; color: #15172A; }

.rep-num {
  color: #6C3BFF;
  font-size: 18px;
  font-weight: 800;
}

.rep-hint {
  font-size: 11px;
  color: #98a2b3;
}

.rep-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: 0;
  color: #6C3BFF;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

/* 问题列表 */
.issue-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.issue-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: #faf9ff;
  border: 1px solid #f1ecff;
  border-radius: 12px;
}

.issue-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #f97316;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 13px;
  flex-shrink: 0;
}

.issue-body { flex: 1; min-width: 0; }

.issue-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}

.issue-head strong { font-size: 14px; font-weight: 700; color: #15172A; }

.issue-tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}

.issue-tag.high { background: #fee2e2; color: #dc2626; }
.issue-tag.mid  { background: #fef3c7; color: #d97706; }
.issue-tag.low  { background: #dcfce7; color: #16a34a; }

.issue-thumb {
  width: 100%;
  aspect-ratio: 16/9;
  background: #ffffff;
  border-radius: 8px;
  display: grid;
  place-items: center;
  margin-bottom: 8px;
  overflow: hidden;
  border: 1px solid #eef0f6;
}

.issue-thumb img { width: 80%; height: 80%; object-fit: contain; }

.issue-desc {
  margin: 0 0 6px;
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}

.issue-suggest {
  margin: 0 0 8px;
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}

.issue-suggest strong { color: #6C3BFF; }

.issue-link {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #6C3BFF;
  cursor: pointer;
  text-decoration: none;
}

.empty-issues {
  margin: 0;
  font-size: 12px;
  color: #98a2b3;
  text-align: center;
  padding: 8px;
  background: #f7f8fc;
  border-radius: 8px;
}

/* 纠正建议 */
.correction-card {
  background: linear-gradient(135deg, #f1ecff 0%, #faf8ff 100%);
  border-color: #e6dbff;
}

.correction-body {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.coach-avatar {
  width: 80px;
  height: 80px;
  background: #fff;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 40px;
  flex-shrink: 0;
  border: 1px solid #e6dbff;
}

.correction-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  counter-reset: num;
}

.correction-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}

.correct-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6C3BFF;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 10px;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 2px;
}

.encourage-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #92400e;
  text-align: center;
  justify-content: center;
}

.encourage-banner .emoji { font-size: 14px; }

/* 视频卡片 */
.video-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #faf9ff;
}

.video-card strong { display: block; font-size: 14px; margin-bottom: 4px; color: #15172A; }
.video-card p { color: #667085; font-size: 12px; margin: 0 0 10px; }

.video-card button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  background: #6C3BFF;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.video-card button:hover { background: #5B2BE8; }

.video-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #f1ecff;
  color: #6C3BFF;
  display: grid;
  place-items: center;
}

.text-green { color: #16a34a; }
.text-blue { color: #2563eb; }
.text-orange { color: #f97316; }
</style>
