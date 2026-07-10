<template>
  <div class="review-page">
    <div v-if="!selectedSession" class="session-picker">
      <header class="picker-header">
        <h2>选择训练记录</h2>
        <p>从最近训练中挑一条记录，查看动作回放、标准参考和 3D 对比。</p>
      </header>
      <StateDisplay
        v-if="sessionsLoading"
        type="loading"
        skeleton="table"
        :skeleton-rows="4"
        text="正在加载训练记录..."
      />
      <div v-else-if="sessions.length === 0" class="picker-empty">
        <StateDisplay
          type="empty"
          title="暂无训练记录"
          text="完成一次训练后，这里会自动展示可回放的记录。"
        />
      </div>
      <div v-else class="picker-list">
        <article
          v-for="session in sessions"
          :key="session.session_id"
          class="picker-card"
          @click="selectedSessionId = session.session_id"
        >
          <div class="picker-card-top">
            <div class="picker-date">
              <strong>{{ formatDateOnly(session.created_at) }}</strong>
              <span>{{ formatTimeOnly(session.created_at) }}</span>
            </div>
            <span class="picker-exercise-tag">{{ exerciseLabel(session.exercise) }}</span>
          </div>
          <div class="picker-card-stats">
            <div>
              <span>得分</span>
              <b :class="scoreTextClass(session.average_score)">{{ session.average_score }}</b>
            </div>
            <div>
              <span>时长</span>
              <b>{{ formatDurationSimple(session.duration_seconds) }}</b>
            </div>
            <div>
              <span>完成</span>
              <b>{{ session.valid_count }}/{{ session.total_count }}</b>
            </div>
          </div>
        </article>
      </div>
    </div>

    <template v-else>
      <header class="review-top">
        <div class="review-title-block">
          <h1>让我们看看哪次动作需要调整 👋</h1>
          <p>我们已为你分析整组动作，挑出需要改进的地方，一起变得更好。</p>
        </div>
        <div class="review-top-figure" aria-hidden="true">
          <img class="review-coach-figure" :src="dashboardSelectCoachImg" alt="" />
        </div>
      </header>

      <section class="session-select-hero">
        <div class="session-select-intro">
          <div class="session-select-icon">
            <Calendar :size="26" />
          </div>
          <div>
            <strong>先选你想看的这次训练</strong>
            <p>挑一条训练记录，我们帮你看看哪几次动作需要注意。</p>
          </div>
        </div>
        <div class="session-select-actions">
          <label class="session-select-box">
            <Calendar :size="18" />
            <select v-model="selectedSessionId" @change="onSessionChange">
              <option v-for="session in sessions" :key="session.session_id" :value="session.session_id">
                {{ formatDateOnly(session.created_at) }} {{ formatTimeOnly(session.created_at) }} · {{ exerciseLabel(session.exercise) }}
              </option>
            </select>
          </label>
          <button class="session-switch-btn" type="button" @click="pickAnotherSession">
            <RefreshCw :size="16" />
            <span>换一条</span>
          </button>
        </div>
      </section>

      <div class="review-layout">
        <main class="review-main">
          <section class="replay-card">
            <div class="replay-tabs">
              <button type="button" :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">动作回放</button>
              <button type="button" :class="{ active: activeTab === 'standard' }" @click="activeTab = 'standard'">标准参考</button>
              <button type="button" :class="{ active: activeTab === 'compare' }" @click="activeTab = 'compare'">3D 对比</button>
            </div>

            <div v-if="activeTab === 'compare'" class="stage stage-compare">
              <div class="stage-legend">
                <span><i class="dot blue"></i>你的动作</span>
              </div>
              <button type="button" class="stage-switch-view" @click="rotateView">
                <RefreshCw :size="15" />
                <span>切换视角</span>
              </button>
              <div class="compare-3d-left">
                <PoseParticleViewer
                  v-if="userFrames.length > 0"
                  :frames="currentUserFrames"
                  :playing="playing"
                  :speed="compareMasterSpeed"
                  :progress="playProgress"
                  :rotation-offset="rotationOffset"
                  :key-joint-highlights="keyJointHighlights"
                  :highlight-instructions="currentHighlights"
                  @update:progress="syncPlayProgress('compare-user', $event)"
                />
              </div>
              <div class="compare-3d-right">
                <div class="stage-legend compare-standard-legend">
                  <span><i class="dot green"></i>标准动作</span>
                </div>
                <PoseParticleViewer
                  v-if="standardFrames.length > 0"
                  :frames="standardFrames"
                  :playing="currentRepIndex < 0 ? playing : false"
                  :speed="playSpeed"
                  :progress="playProgress"
                  :rotation-offset="rotationOffset"
                  @update:progress="syncPlayProgress('compare-standard', $event)"
                />
              </div>
              <div class="stage-split"></div>
            </div>

            <div v-else-if="activeTab === 'user'" class="stage">
              <div class="stage-legend">
                <span><i class="dot violet"></i>视角：{{ viewModeLabel }}</span>
              </div>
              <button type="button" class="stage-switch-view" @click="rotateView">
                <RefreshCw :size="15" />
                <span>切换视角</span>
              </button>
              <PoseParticleViewer
                v-if="userFrames.length > 0"
                :frames="currentUserFrames"
                :playing="playing"
                :speed="playSpeed"
                :progress="playProgress"
                :rotation-offset="rotationOffset"
                :key-joint-highlights="keyJointHighlights"
                :highlight-instructions="currentHighlights"
                @update:progress="syncPlayProgress('user', $event)"
              />
              <StateDisplay v-else type="empty" title="暂无回放数据" text="这条训练记录还没有动作回放数据。" />
            </div>

            <div v-else-if="activeTab === 'standard'" class="stage">
              <div class="stage-legend">
                <span><i class="dot green"></i>标准参考动作</span>
              </div>
              <button type="button" class="stage-switch-view" @click="rotateView">
                <RefreshCw :size="15" />
                <span>切换视角</span>
              </button>
              <PoseParticleViewer
                v-if="standardFrames.length > 0"
                :frames="standardFrames"
                :playing="playing"
                :speed="playSpeed"
                :progress="playProgress"
                :rotation-offset="rotationOffset"
                @update:progress="syncPlayProgress('standard', $event)"
              />
              <StateDisplay v-else type="empty" title="暂无标准动作" text="当前动作还没有可用的标准模板。" />
            </div>

            <div class="player-row">
              <button type="button" class="play-btn" @click="togglePlay">
                <Play v-if="!playing" :size="20" fill="currentColor" />
                <Pause v-else :size="20" fill="currentColor" />
              </button>
              <div class="progress" @click="seekProgress">
                <i :style="{ width: `${playProgress * 100}%` }"></i>
              </div>
              <span class="time-text">{{ formatPlayTime }}</span>
              <select v-model="playSpeed" class="speed-select">
                <option :value="0.5">0.5x</option>
                <option :value="1">1x</option>
                <option :value="1.5">1.5x</option>
                <option :value="2">2x</option>
              </select>
              <button type="button" class="expand-btn" @click="toggleFullscreen">
                <Maximize2 :size="16" />
              </button>
            </div>
          </section>

          <section v-if="repSegments.length > 0" class="attempts-section">
            <header class="attempts-header">
              <div>
                <strong>单次动作回放</strong>
                <span>点击卡片快速切换到对应动作</span>
              </div>
            </header>

            <div class="attempts-row">
              <button type="button" class="attempt-nav" @click="prevRep">
                <ChevronLeft :size="18" />
              </button>

              <div class="attempts-track">
                <article
                  :class="['attempt-card', 'attempt-card-all', { active: currentRepIndex === -1 }]"
                  @click="selectRep(-1)"
                >
                  <div class="attempt-card-head">
                    <strong>全部运动</strong>
                    <span class="attempt-status best">完整</span>
                  </div>
                  <div class="attempt-time">{{ allReplayDuration }}</div>
                  <div class="attempt-line">
                    <i class="attempt-line-dot ok"></i>
                  </div>
                  <button type="button" class="attempt-play-btn">
                    <Play :size="14" fill="currentColor" />
                    <span>回放</span>
                  </button>
                </article>

                <article
                  v-for="(rep, index) in repSegments"
                  :key="index"
                  :class="['attempt-card', { active: currentRepIndex === index }]"
                  @click="selectRep(index)"
                >
                  <div class="attempt-card-head">
                    <strong>第 {{ index + 1 }} 次</strong>
                    <span :class="['attempt-status', hasRealRepIssues(rep) ? 'warn' : 'best']">
                      {{ hasRealRepIssues(rep) ? "需调整" : "正常" }}
                    </span>
                  </div>
                  <div class="attempt-time">{{ formatRepDuration(rep, index) }}</div>
                  <div class="attempt-line">
                    <i :class="['attempt-line-dot', hasRealRepIssues(rep) ? 'warn' : 'ok']"></i>
                  </div>
                  <button type="button" class="attempt-play-btn">
                    <Play :size="14" fill="currentColor" />
                    <span>回放</span>
                  </button>
                </article>
              </div>

              <button type="button" class="attempt-nav" @click="nextRep">
                <ChevronRight :size="18" />
              </button>
            </div>
          </section>
        </main>

        <aside class="review-side">
          <section class="issue-summary-card">
            <div class="issue-summary-head">
              <div>
                <strong>有问题的动作次数</strong>
                <p>共发现 {{ problematicAttempts.length }} 次动作需要注意</p>
              </div>
              <img :src="dashboardSelectHeartImg" alt="" />
            </div>

            <div v-if="problematicAttempts.length > 0" class="issue-summary-list">
              <article
                v-for="(item, index) in problematicAttempts"
                :key="`${item.repIndex}-${item.title}-${index}`"
                class="issue-attempt-card"
                @click="selectRep(item.repIndex)"
              >
                <div class="issue-attempt-head">
                  <div class="issue-attempt-title">
                    <span class="issue-attempt-index">{{ index + 1 }}</span>
                    <strong>第 {{ item.repIndex + 1 }} 次：{{ item.title }}</strong>
                  </div>
                  <span :class="['issue-pill', item.severity]">
                    {{ item.severity === "high" ? "需调整" : "注意" }}
                  </span>
                </div>

                <div class="issue-attempt-body">
                  <div class="issue-attempt-text">
                    <p v-if="item.suggestion"><strong>建议：</strong>{{ item.suggestion }}</p>
                    <p v-if="item.metric || item.valueText" class="issue-attempt-meta">
                      <span v-if="item.metric">{{ item.metric }}</span>
                      <span v-if="item.valueText">{{ item.valueText }}</span>
                    </p>
                  </div>
                </div>
              </article>
            </div>
            <div v-else class="issue-summary-empty">
              <strong>本次没有明显问题动作</strong>
              <p>当前回放分段没有低于阈值或带有问题标记的次数。</p>
            </div>
          </section>

          <section class="encourage-card">
            <img :src="dashboardSelectEncourageImg" alt="" />
          </section>

          <section class="video-card">
            <div>
              <strong>想了解更多？</strong>
              <p>去动作库看看 {{ currentExerciseLabel }} 的教学内容。</p>
              <button type="button" @click="router.push('/exercises')">
                <Clapperboard :size="14" />
                <span>去动作库</span>
              </button>
            </div>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  Maximize2,
  Pause,
  Play,
  RefreshCw,
} from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import PoseParticleViewer from "../components/PoseParticleViewer.vue";
import {
  EXERCISE_KEY_JOINTS,
  METRIC_BODY_PART_MAP,
  inferMetricFromIssue,
  severityToHighlightColor,
  severityToPulseSpeed,
  type HighlightInstruction,
} from "../types/feedback";
import {
  getSessions,
  getSessionReplay,
  type PoseReplayFrame,
  type PoseReplaySegment,
  type SessionRecord,
} from "../api/sessions";
import { getActiveTemplateReplay } from "../api/exercises";
import dashboardSelectCoachImg from "../assets/dashboard-select-coach.png";
import dashboardSelectHeartImg from "../assets/dashboard-select-heart.png";
import dashboardSelectEncourageImg from "../assets/dashboard-select-encourage.png";

const router = useRouter();

const activeTab = ref<"user" | "standard" | "compare">("user");
const playing = ref(false);
const playSpeed = ref(1);
const playProgress = ref(0);
const viewMode = ref<"front" | "side" | "45deg">("front");
const rotationOffset = ref(0);

const sessions = ref<SessionRecord[]>([]);
const sessionsLoading = ref(true);
const selectedSessionId = ref("");
const selectedSession = computed(() =>
  sessions.value.find((session) => session.session_id === selectedSessionId.value) ?? null
);

const userReplayFrames = ref<PoseReplayFrame[]>([]);
const standardFrames = ref<PoseReplayFrame[]>([]);
const repSegments = ref<PoseReplaySegment[]>([]);
const currentRepIndex = ref(-1);
const currentHighlights = ref<HighlightInstruction[]>([]);

const keyJointHighlights = computed<Array<[number, number]>>(() => {
  const exercise = selectedSession.value?.exercise;
  if (!exercise) return [];
  return EXERCISE_KEY_JOINTS[exercise] || EXERCISE_KEY_JOINTS[exercise.replace(/_/g, '')] || [];
});

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
  mountain_climber: "登山跑",
  dumbbell_press: "哑铃推举",
  dumbbell_curl: "哑铃弯举",
  dumbbell_fly: "哑铃飞鸟",
  dumbbell_shoulder_press: "哑铃推肩",
  lat_pulldown: "高位下拉",
  barbell_squat: "杠铃深蹲",
};

const userFrames = computed(() => userReplayFrames.value);

const currentExerciseLabel = computed(() => {
  return exerciseLabel(selectedSession.value?.exercise || "squat");
});

const currentUserFrames = computed(() => {
  if (currentRepIndex.value < 0 || repSegments.value.length === 0) return userFrames.value;
  const range = getExpandedRepFrameRange(currentRepIndex.value);
  if (!range) return userFrames.value;
  return userFrames.value.slice(range.start, range.end + 1);
});

const currentUserDurationMs = computed(() => getFramesDurationMs(currentUserFrames.value));

const standardDurationMs = computed(() => getFramesDurationMs(standardFrames.value));

const compareDurationMs = computed(() => {
  return Math.max(currentUserDurationMs.value, standardDurationMs.value, 1000);
});

const activePlaybackDurationMs = computed(() => {
  if (activeTab.value === "compare") return compareDurationMs.value;
  if (activeTab.value === "standard") return Math.max(standardDurationMs.value, 1000);
  return Math.max(currentUserDurationMs.value, 1000);
});

const allReplayDuration = computed(() => {
  const durationMs = getFramesDurationMs(userFrames.value);
  return formatClockTime(Math.max(1, Math.ceil(durationMs / 1000)));
});

const compareMasterSpeed = computed(() => {
  const userDuration = Math.max(currentUserDurationMs.value, 1);
  return playSpeed.value * (userDuration / compareDurationMs.value);
});

const viewModeLabel = computed(() => {
  if (viewMode.value === "front") return "正面";
  if (viewMode.value === "side") return "侧面";
  return "45°";
});

const currentIssues = computed(() => {
  if (currentRepIndex.value < 0) return [];
  const segment = repSegments.value[currentRepIndex.value];
  if (segment?.issues?.length) {
    return segment.issues.map((issue) => ({
      title: issue.issue || "动作异常",
      severity:
        issue.severity === "high" || issue.severity === "critical"
          ? "high"
          : issue.severity === "mid" || issue.severity === "medium"
            ? "mid"
            : "low",
      description: issue.value != null ? `当前数值 ${issue.value.toFixed(1)}` : "本次识别到姿态偏差",
      suggestion: issue.suggestion || "继续保持稳定发力和正确姿态。",
    }));
  }

  return [
    {
      title: "膝盖内扣",
      severity: "high",
      description: "下蹲时膝盖向内，会增加关节压力。",
      suggestion: "保持膝盖与脚尖方向一致，主动向外打开。",
    },
    {
      title: "下蹲不够深",
      severity: "mid",
      description: "重心后坐不足，大腿还没有接近平行地面。",
      suggestion: "收紧核心，臀部继续向后向下坐。",
    },
  ];
});

const issueImageRules = [
  {
    exercise: "squat",
    keywords: ["膝", "内扣", "不对称"],
    image: "/detail/squat-knees-in.jpg",
  },
  {
    exercise: "squat",
    keywords: ["前倾", "躯干", "重心"],
    image: "/detail/squat-lean.jpg",
  },
  {
    exercise: "squat",
    keywords: ["深度", "下蹲", "不够深", "偏浅", "不足"],
    image: "/detail/squat-depth.jpg",
  },
  {
    exercise: "squat",
    keywords: ["脊柱", "腰背", "背部", "塌腰"],
    image: "/detail/squat-spine.jpg",
  },
  {
    exercise: "squat",
    keywords: ["脚跟", "足跟", "抬脚", "离地"],
    image: "/detail/squat-heel.jpg",
  },
  {
    exercise: "push_up",
    keywords: ["下降", "幅度", "深度", "过浅", "不足"],
    image: "/detail/pushup-depth.jpg",
  },
  {
    exercise: "push_up",
    keywords: ["手臂", "肘", "伸直"],
    image: "/detail/pushup-arm.jpg",
  },
  {
    exercise: "push_up",
    keywords: ["塌腰", "下榻", "弯腰", "撅臀", "身体直线", "核心", "髋"],
    image: "/detail/pushup-body-line.jpg",
  },
];

function getIssueImage(exercise: string, issueTitle: string) {
  const title = issueTitle || "";
  const rule = issueImageRules.find((item) =>
    item.exercise === exercise && item.keywords.some((keyword) => title.includes(keyword))
  );
  return rule?.image || `/exercises/${exercise || "squat"}.png`;
}

const problematicAttempts = computed(() => {
  return repSegments.value
    .map((rep, index) => ({ rep, index }))
    .filter(({ rep }) => (rep.issues?.length ?? 0) > 0)
    .map(({ rep, index }) => {
      const issue = rep.issues?.find((item) => item.issue || item.suggestion || item.metric);
      const severity =
        issue?.severity === "high" || issue?.severity === "critical"
          ? "high"
          : issue?.severity === "mid" || issue?.severity === "medium"
            ? "mid"
            : "low";

      return {
        repIndex: index,
        title: issue?.issue || issue?.metric || "未命名问题",
        severity,
        suggestion: issue?.suggestion || "",
        metric: issue?.metric || "",
        valueText: typeof issue?.value === "number" && Number.isFinite(issue.value)
          ? `当前值：${issue.value.toFixed(1)}`
          : "",
      };
    })
    .filter((item) => item.title !== "未命名问题" || item.suggestion || item.metric || item.valueText);
});

function exerciseLabel(key: string) {
  return exerciseLabels[key] || key;
}

function formatDateOnly(iso: string) {
  if (!iso) return "-";
  const date = new Date(iso);
  return `${date.getFullYear()}年${String(date.getMonth() + 1).padStart(2, "0")}月${String(date.getDate()).padStart(2, "0")}日`;
}

function formatTimeOnly(iso: string) {
  if (!iso) return "-";
  const date = new Date(iso);
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function formatDurationSimple(seconds: number) {
  if (!seconds || seconds <= 0) return "0秒";
  const minute = Math.floor(seconds / 60);
  const second = seconds % 60;
  return minute > 0 ? `${minute}分${second}秒` : `${second}秒`;
}

function formatClockTime(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const remainingSeconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function getFramesDurationMs(frames: PoseReplayFrame[]) {
  if (frames.length < 2) return 0;
  const first = frames[0]?.timestamp_ms ?? 0;
  const last = frames[frames.length - 1]?.timestamp_ms ?? first;
  return Math.max(0, last - first);
}

function clampFrameIndex(index: number) {
  const lastIndex = Math.max(0, userFrames.value.length - 1);
  return Math.max(0, Math.min(lastIndex, index));
}

function getRepCenterFrameIndex(index: number) {
  const segment = repSegments.value[index];
  if (!segment) return null;
  const start = clampFrameIndex(Number(segment.start_frame_index) || 0);
  const end = clampFrameIndex(Number(segment.end_frame_index) || start);
  return Math.round((start + end) / 2);
}

function getExpandedRepFrameRange(index: number) {
  if (index < 0 || userFrames.value.length === 0) return null;

  const currentCenter = getRepCenterFrameIndex(index);
  if (currentCenter == null) return null;

  const previousCenter = getRepCenterFrameIndex(index - 1);
  const nextCenter = getRepCenterFrameIndex(index + 1);
  const lastFrameIndex = userFrames.value.length - 1;

  const start = previousCenter == null
    ? 0
    : clampFrameIndex(Math.floor((previousCenter + currentCenter) / 2) + 1);
  const end = nextCenter == null
    ? lastFrameIndex
    : clampFrameIndex(Math.ceil((currentCenter + nextCenter) / 2));

  if (end <= start) {
    const segment = repSegments.value[index];
    return {
      start: clampFrameIndex(Number(segment?.start_frame_index) || 0),
      end: clampFrameIndex(Number(segment?.end_frame_index) || 0),
    };
  }

  return { start, end };
}

function formatRepDuration(rep: PoseReplaySegment, index?: number) {
  const range = typeof index === "number" ? getExpandedRepFrameRange(index) : null;
  if (range) {
    return formatClockTime(Math.max(1, Math.ceil(getFramesDurationMs(userFrames.value.slice(range.start, range.end + 1)) / 1000)));
  }

  const durationMs = Math.max(0, (rep.end_timestamp_ms ?? 0) - (rep.start_timestamp_ms ?? 0));
  if (durationMs > 0) return formatClockTime(Math.max(1, Math.ceil(durationMs / 1000)));
  const frames = Math.max(1, rep.end_frame_index - rep.start_frame_index + 1);
  return formatClockTime(Math.max(1, Math.ceil(frames / 30)));
}

function hasRealRepIssues(rep: PoseReplaySegment) {
  return Boolean(rep.issues?.some((issue) => issue.issue || issue.suggestion || issue.metric));
}

function scoreTextClass(score: number) {
  if (score >= 80) return "text-green";
  if (score >= 60) return "text-blue";
  return "text-orange";
}

const formatPlayTime = computed(() => {
  const totalMs = activePlaybackDurationMs.value;
  const totalSeconds = Math.max(1, Math.ceil(totalMs / 1000));
  const currentSeconds = Math.min(totalSeconds, Math.floor(playProgress.value * totalMs / 1000));
  return `${formatClockTime(currentSeconds)} / ${formatClockTime(totalSeconds)}`;
});

function togglePlay() {
  playing.value = !playing.value;
}

function syncPlayProgress(source: "user" | "standard" | "compare-user" | "compare-standard", value: number) {
  const shouldSync =
    (activeTab.value === "user" && source === "user") ||
    (activeTab.value === "standard" && source === "standard") ||
    (activeTab.value === "compare" && source === "compare-user");

  if (shouldSync) {
    playProgress.value = Math.max(0, Math.min(1, value));
  }
}

function seekProgress(event: MouseEvent) {
  const bar = event.currentTarget as HTMLElement;
  const rect = bar.getBoundingClientRect();
  playProgress.value = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
}

function prevRep() {
  if (repSegments.value.length === 0) return;
  currentRepIndex.value = currentRepIndex.value > -1 ? currentRepIndex.value - 1 : repSegments.value.length - 1;
  playProgress.value = 0;
  applyHighlightsForRep(currentRepIndex.value);
}

function nextRep() {
  if (repSegments.value.length === 0) return;
  currentRepIndex.value = currentRepIndex.value < repSegments.value.length - 1 ? currentRepIndex.value + 1 : -1;
  playProgress.value = 0;
  applyHighlightsForRep(currentRepIndex.value);
}

function applyHighlightsForRep(index: number) {
  if (index < 0) {
    currentHighlights.value = [];
    return;
  }

  const segment = repSegments.value[index];
  if (segment?.issues?.length) {
    const hls: HighlightInstruction[] = [];
    for (const issue of segment.issues) {
      const metric = issue.metric || inferMetricFromIssue(issue.issue || "");
      if (!metric) continue;
      const mapping = METRIC_BODY_PART_MAP[metric];
      if (!mapping) continue;
      const severity = (issue.severity === "critical" || issue.severity === "high") ? "high"
        : issue.severity === "mid" || issue.severity === "medium" ? "medium" : "low";
      hls.push({
        bonePairs: mapping.bones,
        color: severityToHighlightColor(severity),
        pulseSpeed: severityToPulseSpeed(severity),
      });
    }
    currentHighlights.value = hls;
  } else {
    currentHighlights.value = [];
  }
}

function selectRep(index: number) {
  currentRepIndex.value = index;
  playProgress.value = 0;
  applyHighlightsForRep(index);
}

function rotateView() {
  const nextMode = viewMode.value === "front" ? "side" : viewMode.value === "side" ? "45deg" : "front";
  setView(nextMode);
}

function setView(mode: "front" | "side" | "45deg") {
  viewMode.value = mode;
  const rotationMap = {
    front: 0,
    side: Math.PI / 2,
    "45deg": Math.PI / 4,
  };
  rotationOffset.value = rotationMap[mode];
}

function toggleFullscreen() {
  const element = document.documentElement;
  if (!document.fullscreenElement) {
    element.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

function pickAnotherSession() {
  if (sessions.value.length <= 1 || !selectedSessionId.value) return;
  const index = sessions.value.findIndex((session) => session.session_id === selectedSessionId.value);
  const nextIndex = index >= 0 ? (index + 1) % sessions.value.length : 0;
  selectedSessionId.value = sessions.value[nextIndex].session_id;
}

async function loadSessions() {
  sessionsLoading.value = true;
  try {
    const data = await getSessions({ limit: 50 });
    sessions.value = data.items || [];

    if (sessions.value.length > 0 && !selectedSessionId.value) {
      selectedSessionId.value = sessions.value[0].session_id;
    }
  } catch {
    sessions.value = [];
  } finally {
    sessionsLoading.value = false;
  }
}

async function onSessionChange() {
  if (!selectedSessionId.value) return;

  playing.value = false;
  playProgress.value = 0;
  currentRepIndex.value = -1;

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

  // 有骨架帧时自动开始播放
  if (userReplayFrames.value.length > 0) {
    playProgress.value = 0;
    await nextTick();
    playing.value = true;
  }
}

watch(selectedSessionId, (value, oldValue) => {
  if (value && value !== oldValue) {
    void onSessionChange();
  }
});

onMounted(() => {
  void loadSessions();
  const url = new URL(window.location.href);
  const replay = url.searchParams.get("replay");
  if (replay) {
    selectedSessionId.value = replay;
  }
});

onBeforeUnmount(() => {
  playing.value = false;
});
</script>

<style scoped>
.review-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0 0 24px;
}

.session-picker {
  display: grid;
  gap: 20px;
  max-width: 760px;
  width: 100%;
  margin: 0 auto;
}

.picker-header {
  text-align: center;
}

.picker-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 900;
  color: #15172a;
}

.picker-header p {
  margin: 10px 0 0;
  font-size: 15px;
  color: #667085;
}

.picker-list {
  display: grid;
  gap: 14px;
}

.picker-card {
  display: grid;
  gap: 12px;
  padding: 18px 22px;
  background: #ffffff;
  border: 1px solid #eceffd;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(81, 61, 168, 0.08);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.picker-card:hover {
  transform: translateY(-2px);
  border-color: #cdbdff;
  box-shadow: 0 16px 34px rgba(108, 59, 255, 0.12);
}

.picker-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.picker-date {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.picker-date strong {
  font-size: 17px;
  font-weight: 800;
  color: #161827;
}

.picker-date span {
  font-size: 14px;
  color: #8b94a8;
}

.picker-exercise-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f1ecff;
  color: #6c3bff;
  font-size: 13px;
  font-weight: 700;
}

.picker-card-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.picker-card-stats div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker-card-stats span {
  color: #8b94a8;
  font-size: 14px;
}

.picker-card-stats b {
  font-size: 15px;
  color: #15172a;
}

.review-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  align-items: end;
  gap: 24px;
}

.review-title-block h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.18;
  font-weight: 900;
  color: #101223;
}

.review-title-block p {
  margin: 14px 0 0;
  font-size: 18px;
  line-height: 1.7;
  color: #6b7280;
}

.review-top-figure {
  position: relative;
  min-height: 150px;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.review-coach-figure {
  width: 500px;
  max-width: 100%;
  height: auto;
  object-fit: contain;
}

.session-select-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 24px;
  padding: 26px 28px;
  background: #ffffff;
  border: 2px solid #aa8bff;
  border-radius: 28px;
  box-shadow: 0 14px 42px rgba(98, 75, 177, 0.08);
}

.session-select-intro {
  display: flex;
  align-items: center;
  gap: 18px;
}

.session-select-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #8258ff 0%, #6934ff 100%);
  color: #ffffff;
  box-shadow: 0 16px 28px rgba(108, 59, 255, 0.24);
  flex-shrink: 0;
}

.session-select-intro strong {
  display: block;
  font-size: 22px;
  font-weight: 900;
  color: #101223;
}

.session-select-intro p {
  margin: 8px 0 0;
  font-size: 15px;
  color: #6b7280;
}

.session-select-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.session-select-box {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 420px;
  height: 58px;
  padding: 0 18px;
  background: #ffffff;
  border: 1px solid #e7e9f3;
  border-radius: 18px;
  color: #667085;
}

.session-select-box select {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  cursor: pointer;
}

.session-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 58px;
  padding: 0 24px;
  border: 0;
  border-radius: 18px;
  background: linear-gradient(180deg, #703dff 0%, #5d28ed 100%);
  color: #ffffff;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 14px 26px rgba(108, 59, 255, 0.24);
}

.review-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 344px;
  gap: 22px;
  align-items: start;
}

.review-main,
.review-side {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.replay-card,
.attempts-section,
.issue-summary-card,
.video-card {
  background: #ffffff;
  border: 1px solid #eceffd;
  border-radius: 24px;
  box-shadow: 0 12px 34px rgba(81, 61, 168, 0.07);
}

.replay-card {
  padding: 16px 16px 12px;
}

.replay-tabs {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.replay-tabs button {
  height: 48px;
  padding: 0 22px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: #2f3446;
  font-size: 17px;
  font-weight: 800;
  cursor: pointer;
}

.replay-tabs button.active {
  color: #6c3bff;
  box-shadow: inset 0 -4px 0 #6c3bff;
  border-radius: 0;
}

.stage {
  position: relative;
  width: 100%;
  height: 380px;
  overflow: hidden;
  border-radius: 22px;
  background: linear-gradient(180deg, #02040c 0%, #040915 100%);
}

.stage-compare .compare-3d-left,
.stage-compare .compare-3d-right {
  position: absolute;
  top: 0;
  width: 50%;
  height: 100%;
}

.stage-compare .compare-3d-left {
  left: 0;
}

.stage-compare .compare-3d-right {
  right: 0;
}

.compare-standard-legend {
  left: 18px;
  top: 18px;
}

.stage-split {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  border-left: 1px dashed rgba(134, 147, 255, 0.45);
  z-index: 2;
}

.stage-legend {
  position: absolute;
  left: 18px;
  top: 18px;
  z-index: 4;
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  border-radius: 14px;
  background: rgba(15, 20, 33, 0.88);
  color: #eef2ff;
  font-size: 14px;
  font-weight: 700;
}

.stage-legend span {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.dot.blue {
  background: #49bcff;
}

.dot.green {
  background: #61e48f;
}

.dot.violet {
  background: #9f84ff;
}

.stage-switch-view {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 4;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  background: rgba(15, 20, 33, 0.88);
  color: #f5f7ff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.player-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 6px 2px;
}

.play-btn {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: #6c3bff;
  color: #ffffff;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(108, 59, 255, 0.28);
  flex-shrink: 0;
}

.progress {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #e5e9f6;
  cursor: pointer;
  overflow: hidden;
}

.progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #7a49ff;
}

.time-text {
  min-width: 92px;
  font-size: 14px;
  color: #7b8498;
  font-variant-numeric: tabular-nums;
}

.speed-select,
.expand-btn {
  height: 40px;
  border-radius: 12px;
  border: 1px solid #e6e9f4;
  background: #ffffff;
  color: #2f3446;
  font-size: 14px;
  font-weight: 700;
}

.speed-select {
  padding: 0 14px;
}

.expand-btn {
  width: 40px;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.attempts-section {
  padding: 18px 18px 20px;
}

.attempts-header {
  margin-bottom: 16px;
}

.attempts-header strong {
  display: block;
  font-size: 18px;
  font-weight: 900;
  color: #121528;
}

.attempts-header span {
  display: block;
  margin-top: 6px;
  font-size: 14px;
  color: #8b94a8;
}

.attempts-row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) 32px;
  gap: 12px;
  align-items: center;
}

.attempts-track {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  min-width: 0;
}

.attempt-nav {
  align-self: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 999px;
  background: #f5f3ff;
  color: #7a49ff;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.attempt-card {
  display: grid;
  gap: 14px;
  min-width: 0;
  padding: 16px 16px 14px;
  border: 1px solid #eceffd;
  border-radius: 18px;
  background: #ffffff;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.attempt-card:hover {
  transform: translateY(-2px);
  border-color: #cfbfff;
}

.attempt-card.active {
  border-color: #8c68ff;
  box-shadow: 0 12px 26px rgba(108, 59, 255, 0.14);
}

.attempt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.attempt-card-head strong {
  font-size: 15px;
  font-weight: 900;
  color: #131727;
}

.attempt-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
}

.attempt-status.best,
.attempt-status.good {
  background: #ddf9e7;
  color: #17a34a;
}

.attempt-status.warn {
  background: #ffe7e4;
  color: #ff5b57;
}

.attempt-time {
  font-size: 14px;
  font-weight: 700;
  color: #596275;
}

.attempt-line {
  position: relative;
  height: 3px;
  border-radius: 999px;
  background: repeating-linear-gradient(
    to right,
    #dde2ef 0,
    #dde2ef 8px,
    transparent 8px,
    transparent 14px
  );
}

.attempt-line-dot {
  position: absolute;
  top: 50%;
  right: 12%;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  transform: translateY(-50%);
}

.attempt-line-dot.ok {
  background: #1fbe64;
}

.attempt-line-dot.warn {
  background: #ff5b57;
}

.attempt-play-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 42px;
  border: 1px solid #ebdfff;
  border-radius: 14px;
  background: #faf6ff;
  color: #6c3bff;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}

.issue-summary-card {
  padding: 18px;
}

.issue-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.issue-summary-head strong {
  display: block;
  font-size: 18px;
  font-weight: 900;
  color: #111425;
}

.issue-summary-head p {
  margin: 8px 0 0;
  font-size: 15px;
  color: #7b8498;
}

.issue-summary-head img {
  width: 62px;
  height: auto;
  flex-shrink: 0;
}

.issue-summary-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 460px;
  overflow-y: auto;
  padding-right: 6px;
}
.issue-summary-list::-webkit-scrollbar { width: 6px; }
.issue-summary-list::-webkit-scrollbar-thumb { background: #c7cbe0; border-radius: 3px; }
.issue-summary-list::-webkit-scrollbar-track { background: transparent; }

.issue-summary-empty {
  padding: 18px;
  border-radius: 18px;
  background: #f7fbf7;
  border: 1px solid #dff4e5;
}

.issue-summary-empty strong {
  display: block;
  font-size: 16px;
  font-weight: 900;
  color: #16703a;
}

.issue-summary-empty p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.65;
  color: #5f7467;
}

.issue-attempt-card {
  padding: 16px;
  border: 1px solid #eef1fa;
  border-radius: 20px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  cursor: pointer;
}

.issue-attempt-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.issue-attempt-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.issue-attempt-index {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #ff654f 0%, #ff4d42 100%);
  color: #ffffff;
  font-size: 16px;
  font-weight: 900;
  flex-shrink: 0;
}

.issue-attempt-title strong {
  font-size: 16px;
  font-weight: 900;
  color: #161a2d;
}

.issue-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
  flex-shrink: 0;
}

.issue-pill.high {
  background: #ffe7e4;
  color: #ff5b57;
}

.issue-pill.mid,
.issue-pill.low {
  background: #fff1d9;
  color: #d97706;
}

.issue-attempt-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  margin-top: 14px;
}

.issue-attempt-text p {
  margin: 0;
  font-size: 15px;
  line-height: 1.75;
  color: #596275;
}

.issue-attempt-text strong {
  color: #6c3bff;
}

.issue-attempt-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px !important;
}

.issue-attempt-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f5f3ff;
  color: #6c3bff;
  font-size: 13px;
  font-weight: 800;
}

.encourage-card {
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  overflow: visible;
}

.encourage-card img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 0;
}

.video-card {
  padding: 18px 20px;
}

.video-card strong {
  display: block;
  font-size: 18px;
  font-weight: 900;
  color: #111425;
}

.video-card p {
  margin: 8px 0 14px;
  font-size: 15px;
  line-height: 1.7;
  color: #7b8498;
}

.video-card button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 14px;
  background: linear-gradient(180deg, #703dff 0%, #5d28ed 100%);
  color: #ffffff;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}

.text-green {
  color: #16a34a;
}

.text-blue {
  color: #2563eb;
}

.text-orange {
  color: #f97316;
}

@media (max-width: 1380px) {
  .review-top {
    grid-template-columns: minmax(0, 1fr) 290px;
  }

  .review-title-block h1 {
    font-size: 38px;
  }

  .session-select-hero {
    grid-template-columns: 1fr;
  }

  .session-select-actions {
    width: 100%;
  }

  .session-select-box {
    min-width: 0;
    flex: 1;
  }

  .attempts-track {
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  }
}

@media (max-width: 1200px) {
  .review-layout {
    grid-template-columns: 1fr;
  }

  .review-side {
    order: 2;
  }
}

@media (max-width: 900px) {
  .review-top {
    grid-template-columns: 1fr;
  }

  .review-top-figure {
    justify-content: center;
  }

  .review-title-block h1 {
    font-size: 32px;
  }

  .session-select-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .issue-attempt-body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .picker-card-top,
  .picker-card-stats {
    grid-template-columns: 1fr;
  }

  .picker-card-top {
    display: grid;
  }

  .stage {
    height: 300px;
  }

  .player-row {
    flex-wrap: wrap;
  }

  .attempts-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .attempt-nav {
    display: none;
  }

  .attempts-track {
    grid-template-columns: 1fr;
  }
}
</style>
