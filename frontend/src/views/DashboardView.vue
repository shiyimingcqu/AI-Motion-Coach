<template>
  <div class="sports-dashboard">
    <section class="top-header">
      <div class="th-left">
        <div class="th-avatar">{{ userInitial }}</div>
        <div class="th-info">
          <strong>{{ userName }}</strong>
          <p>{{ summarySubtitle }}</p>
        </div>
      </div>

      <div class="th-score">
        <span class="th-score-label">综合评分</span>
        <div class="th-score-value">
          <span class="th-score-num">{{ displayScore }}</span>
          <span class="th-score-unit">/100</span>
        </div>
        <span class="th-score-badge" :class="scoreLevel">{{ scoreLabel }}</span>
      </div>

      <div class="th-compare">
        <span class="th-compare-label">对比上次</span>
        <strong class="th-compare-value" :class="scoreChangeTone">
          <svg
            v-if="scoreChangeIcon === 'up'"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path d="M12 19V5" />
            <path d="m5 12 7-7 7 7" />
          </svg>
          <svg
            v-else
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path d="M12 5v14" />
            <path d="m19 12-7 7-7-7" />
          </svg>
          {{ scoreChangeText }}
        </strong>
      </div>

      <div class="th-actions">
        <button class="btn-outline" @click="router.push('/reference-videos')" style="margin-right:10px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="20" rx="3" /><polygon points="10,8 16,12 10,16" fill="currentColor" stroke="none" />
          </svg>
          标准视频
        </button>
        <button class="btn-primary" @click="router.push('/exercises')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5,3 19,12 5,21" />
          </svg>
          开始训练
        </button>
      </div>
    </section>

    <section class="core-row">
      <div class="main-panel">
        <header class="panel-header">
          <div class="panel-left">
            <div class="panel-title-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
              </svg>
              <h2>深蹲动作评估</h2>
            </div>
            <div class="phase-badge">
              <span class="phase-dot" :class="hasLatestAnalysis ? 'pulse-blue' : ''"></span>
              当前阶段：<strong>{{ hasLatestAnalysis ? exerciseDisplayName(latestExercise) + '分析完成' : '暂无分析数据' }}</strong>
            </div>
            <span class="status-pill warn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              检测到 {{ problems.length }} 个问题
            </span>
          </div>
        </header>

        <div class="metric-strip">
          <div v-for="metric in sideMetrics" :key="metric.label" class="ms-item" :title="metric.tip">
            <span class="ms-label">{{ metric.label }}</span>
            <strong :class="metric.cls">{{ metric.value }}</strong>
            <div class="ms-track">
              <i :style="{ width: `${metric.value}%` }" :class="metric.cls"></i>
            </div>
          </div>
        </div>

        <div ref="replayFullscreenRef" class="replay-fullscreen-shell">
        <div class="skel-area replay-stage">
          <div class="skel-grid"></div>
          <PoseParticleViewer
            v-model:progress="replayProgress"
            :frames="selectedReplayFrames"
            :playing="replayPlaying"
            :speed="replaySpeed"
            :background-image="selectedReplayBackgroundImage"
            :highlight-instructions="currentHighlights"
            @frame-change="onReplayFrameChange"
            @body-part-clicked="on3DBodyPartClicked"
          />
          <div class="skel-stage-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span class="replay-stage-text">{{ replayStageLabel }}</span>
            <span v-if="replaySessionsLoading" class="replay-loading-spinner"></span>
          </div>
          <select
            v-if="completedVideos.length > 0"
            class="video-selector video-selector--standalone"
            :value="selectedVideoIndex"
            @change="switchToVideo(Number(($event.target as HTMLSelectElement).value))"
          >
            <option v-for="(v, i) in completedVideos" :key="v.task_id" :value="i">
              {{ v.label }}
            </option>
          </select>

          <button
            class="replay-fullscreen-button"
            type="button"
            :aria-label="isReplayFullscreen ? 'Exit fullscreen' : 'Fullscreen'"
            :title="isReplayFullscreen ? 'Exit fullscreen' : 'Fullscreen'"
            @click="toggleReplayFullscreen"
          >
            <Minimize2 v-if="isReplayFullscreen" :size="18" />
            <Maximize2 v-else :size="18" />
          </button>

          <button
            v-if="isReplayFullscreen"
            class="replay-settings-button"
            type="button"
            :aria-label="showReplaySettings ? 'Hide settings' : 'Show settings'"
            :title="showReplaySettings ? 'Hide settings' : 'Show settings'"
            @click="showReplaySettings = !showReplaySettings"
          >
            <Settings :size="18" />
          </button>

          <aside v-if="isReplayFullscreen && showReplaySettings" class="replay-settings-panel">
            <header>
              <strong>背景设置</strong>
              <button type="button" aria-label="Close settings" @click="showReplaySettings = false">×</button>
            </header>
            <div class="replay-background-list">
              <button
                v-for="option in replayBackgroundOptions"
                :key="option.value"
                type="button"
                class="replay-background-option"
                :class="{ active: selectedReplayBackground === option.value }"
                @click="selectedReplayBackground = option.value"
              >
                <span v-if="!option.image" class="replay-background-none"></span>
                <img v-else :src="option.image" :alt="option.label" />
                <b>{{ option.label }}</b>
              </button>
            </div>
          </aside>

          <div class="skel-layout">
            <video
              v-if="latestVideoUrl"
              :key="latestVideoUrl"
              :src="latestVideoUrl"
              class="pose-video"
              autoplay
              loop
              muted
              playsinline
              @loadedmetadata="onVideoMetadata"
              @timeupdate="onVideoTimeUpdate"
            />
            <svg v-else viewBox="0 0 300 520" class="pose-skeleton breathing-skel">
              <circle cx="150" cy="42" r="20" fill="none" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="150" y1="62" x2="150" y2="90" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="150" y1="90" x2="150" y2="210" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="110" y1="210" x2="190" y2="210" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="150" y1="110" x2="90" y2="172" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="90" y1="172" x2="72" y2="230" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="150" y1="110" x2="210" y2="172" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="210" y1="172" x2="228" y2="230" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="130" y1="210" x2="70" y2="350" stroke="#f97316" stroke-width="3" />
              <line x1="70" y1="350" x2="55" y2="470" stroke="#f97316" stroke-width="2.5" />
              <line x1="170" y1="210" x2="230" y2="350" stroke="#5b8cff" stroke-width="2.5" />
              <line x1="230" y1="350" x2="245" y2="470" stroke="#5b8cff" stroke-width="2.5" />
              <g fill="#5b8cff">
                <circle cx="150" cy="90" r="5" />
                <circle cx="150" cy="130" r="5" />
                <circle cx="90" cy="172" r="5" />
                <circle cx="72" cy="230" r="4.5" />
                <circle cx="210" cy="172" r="5" />
                <circle cx="228" cy="230" r="4.5" />
                <circle cx="130" cy="210" r="5" />
                <circle cx="170" cy="210" r="5" />
              </g>
              <g fill="#f97316">
                <circle cx="70" cy="350" r="5" />
                <circle cx="55" cy="470" r="4.5" />
              </g>
              <circle cx="230" cy="350" r="5" fill="#5b8cff" />
              <circle cx="245" cy="470" r="4.5" fill="#5b8cff" />
              <g class="warning-anim">
                <circle
                  cx="70"
                  cy="350"
                  r="24"
                  fill="none"
                  stroke="#ef4444"
                  stroke-width="1.5"
                  stroke-dasharray="4 3"
                  opacity="0.7"
                />
                <text x="70" y="390" text-anchor="middle" fill="#ef4444" font-size="10" font-weight="700">
                  膝内扣
                </text>
              </g>
            </svg>
          </div>

          <div class="score-card-overlay">
            <div class="score-ring-big" :style="{ '--ring-pct': `${scoreValueForRing}%` }">
              <span class="score-ring-num">{{ scoreValueForRing }}</span>
              <span class="score-ring-label">综合评分</span>
            </div>
            <div class="score-ring-meta">
              <span class="score-ring-grade good">{{ scoreLabel }}</span>
              <div class="score-ring-issues">
                <span>主要问题：</span>
                <strong>{{ issueSummary }}</strong>
              </div>
            </div>
          </div>

          <div class="view-strip">
            <button :class="['view-angle', { active: activeView === 'front' }]" @click="switchView('front')">正面</button>
            <button :class="['view-angle', { active: activeView === 'side' }]" @click="switchView('side')">侧面</button>
          </div>
        </div>

        <div class="phase-flow-bar">
          <div class="replay-toolbar">
            <label class="replay-session-picker">
              <span>选择运动记录</span>
              <select v-model="selectedReplaySessionId" @change="loadSelectedReplay">
                <option value="">{{ replaySessionsLoading ? '加载中...' : (replaySessions.length === 0 ? '暂无训练记录' : '请选择一次训练') }}</option>
                <option v-for="(session, index) in replaySessions" :key="session ? session.session_id : index" :value="session ? session.session_id : ''">
                  {{ session ? sessionOptionLabel(session) : '无效记录' }}
                </option>
              </select>
            </label>

            <div class="score-card-overlay">
              <div class="score-ring-big">
                <span class="score-ring-num">{{ selectedReplayScore }}</span>
                <span class="score-ring-label">综合评分</span>
              </div>
              <div class="score-ring-meta">
                <span class="score-ring-grade good">{{ selectedReplayExerciseName }}</span>
                <div class="score-ring-issues">
                  <span>回放帧数：</span>
                  <strong>{{ selectedReplayFrames.length }} 帧</strong>
                </div>
              </div>
            </div>
          </div>

          <!-- Rep filter segmented control (按单次动作筛选) -->
          <div v-if="repFilters.length > 0" class="rep-filter-bar">
            <button
              :class="['rep-filter-btn', { active: selectedRepFilter === null }]"
              @click="switchToRep(null)"
            >
              全部
            </button>
            <button
              v-for="seg in repFilters"
              :key="seg.rep_index"
              :class="['rep-filter-btn', { active: selectedRepFilter === seg.rep_index }]"
              @click="switchToRep(seg.rep_index)"
            >
              第{{ seg.rep_index }}次
            </button>
          </div>

          <p v-if="!hasLatestAnalysis && selectedReplayFrames.length === 0" class="phase-no-data">暂无分析数据，上传视频完成分析后此处将显示动作阶段</p>
          <div v-else class="phase-flow">
            <div
              v-for="(phase, index) in phases"
              :key="phase"
              class="phase-step"
              :class="{ done: index < phaseDoneCount }"
            >
              <div class="phase-circle">
                <svg v-if="index < phaseDoneCount" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <span class="phase-label">{{ phase }}</span>
            </div>
            <div class="phase-connector">
              <div class="phase-connector-fill" :style="{ width: hasLatestAnalysis ? '100%' : '0%' }"></div>
            </div>
          </div>

          <div class="play-controls">
            <button class="play-btn-small" type="button" :disabled="selectedReplayFrames.length === 0" @click="replayPlaying = !replayPlaying">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <polygon v-if="!replayPlaying" points="8,5 19,12 8,19" />
                <path v-else d="M7 5h4v14H7zM13 5h4v14h-4z" />
              </svg>
            </button>
            <div class="timeline-mini">
              <input
                v-model.number="replayProgress"
                class="replay-range"
                type="range"
                min="0"
                max="1"
                step="0.001"
                :disabled="selectedReplayFrames.length === 0"
              />
              <div class="tl-labels"><span>{{ replayCurrentTime }}</span><span>{{ replayDurationText }}</span></div>
            </div>
            <div class="speed-mini">
              <button
                v-for="speed in [0.5, 1, 1.5]"
                :key="speed"
                type="button"
                :class="{ active: replaySpeed === speed }"
                @click="replaySpeed = speed"
              >
                {{ speed.toFixed(1) }}x
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>

      <aside class="right-col">
        <div class="section-card">
          <header class="sc-header">
            <div class="sc-header-icon danger">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div>
              <h3>问题识别</h3>
              <p>发现 <strong>{{ problems.length }}</strong> 个动作问题</p>
            </div>
          </header>

          <div class="problem-list">
            <div
              v-for="(item, index) in problems"
              :key="`${item.title}-${index}`"
              :class="['problem-item', item.level, { selected: selectedProblem === index }]"
              @click="onProblemClick(index)"
            >
              <div class="pi-top">
                <div class="pi-num" :class="item.level">{{ index + 1 }}</div>
                <div class="pi-info">
                  <div class="pi-title-row">
                    <strong>{{ item.title }}</strong>
                    <span v-if="item.bodyPart" class="pi-body-part">{{ item.bodyPart.label_zh }}</span>
                    <span class="pi-badge" :class="item.level">{{ item.badge }}</span>
                  </div>
                  <p>{{ item.desc }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="section-card">
          <header class="sc-header">
            <div class="sc-header-icon success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <div>
              <h3>纠正建议</h3>
              <p v-if="selectedProblem !== null && currentProblem">针对「{{ currentProblem.title }}」</p>
              <p v-else>请先选择一个动作问题</p>
            </div>
          </header>
          <div v-if="selectedProblem !== null && currentProblem" style="padding: 0 16px 16px; font-size: 13px; line-height: 1.6; color: #475569;">
            {{ currentProblem.recommend }}
          </div>
        </div>
      </aside>
    </section>

    <section class="charts-row">
      <div class="chart-card">
        <header class="chart-card-header">
          <h3>评分趋势</h3>
          <span class="chart-pill up">近 7 天 · {{ scoreValueForRing }}</span>
        </header>
        <div ref="trendChartRef" class="chart-body"></div>
      </div>

      <div class="chart-card">
        <header class="chart-card-header">
          <h3>能力雷达图</h3>
          <span class="chart-pill">短板：关节活动度</span>
        </header>
        <div ref="radarChartRef" class="chart-body"></div>
        <div class="chart-footer">
          <span class="cf-badge good">优势：动作流畅度 {{ sideMetrics[0]?.value ?? 0 }}</span>
          <span class="cf-badge warn">短板：关节活动度 {{ sideMetrics[2]?.value ?? 0 }}</span>
        </div>
      </div>

      <div class="chart-card">
        <header class="chart-card-header">
          <h3>左右对称性</h3>
          <span class="chart-pill">左右对比</span>
        </header>
        <div ref="symmetryChartRef" class="chart-body"></div>
      </div>
    </section>

    <section class="bottom-actions">
      <button class="ba-btn">重新评估</button>
      <button class="ba-btn">生成纠正计划</button>
      <button class="ba-btn" @click="router.push('/export')">导出 PDF</button>
      <button class="ba-btn primary" @click="router.push('/export')">查看完整报告</button>
    </section>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "DashboardView" });
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts/core";
import { BarChart, LineChart, RadarChart } from "echarts/charts";
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { Maximize2, Minimize2, Settings } from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";
import { getDashboardStats } from "../api/dashboard";
import { getFeedbacks, type FeedbackItem } from "../api/feedback";
import { getSessionReplay, getSessions, getSession, type PoseReplayFrame, type PoseReplayNode, type SessionRecord, type PoseReplaySegment, type PoseReplaySegmentIssue } from "../api/sessions";
import PoseParticleViewer from "../components/PoseParticleViewer.vue";
import { apiGet } from "../api/client";
import {
  METRIC_BODY_PART_MAP,
  inferMetricFromIssue,
  severityToHighlightColor,
  severityToPulseSpeed,
  type HighlightInstruction,
  type BodyPartMapping,
} from "../types/feedback";

echarts.use([
  BarChart,
  LineChart,
  RadarChart,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
  CanvasRenderer,
]);

type Severity = "high" | "medium" | "low";

type ProblemItem = {
  title: string;
  desc: string;
  level: Severity;
  badge: string;
  time: string;
  deduct: number;
  recommend: string;
  metric: string | null;
  bodyPart: BodyPartMapping | null;
  repIndex?: number | null;
};

type AdviceGroup = {
  label: string;
  color: string;
  items: Array<{
    title: string;
    desc: string;
    sets: string;
    freq: string;
  }>;
};

type ReplayBackgroundOption = {
  label: string;
  value: string;
  image?: string;
};

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const statsData = ref<any>(null);
const statsLoading = ref(true);
const feedbackItems = ref<FeedbackItem[]>([]);
const replaySessions = ref<SessionRecord[]>([]);
const replaySessionsLoading = ref(true);
const selectedReplaySessionId = ref("");
const selectedReplay = ref<SessionRecord | null>(null);
const selectedReplayFrames = computed<PoseReplayFrame[]>(() => {
  if (allReplayFrames.value.length === 0) return [];
  if (selectedRepFilter.value === null) return allReplayFrames.value;
  const range = resolveRepFrameRange(selectedRepFilter.value);
  if (!range) return allReplayFrames.value;
  return normalizeReplayFrames(allReplayFrames.value.slice(range.start, range.end + 1));
});
const replayPlaying = ref(false);
const replaySpeed = ref(1);
const replayProgress = ref(0);
const replayFrame = ref<PoseReplayFrame | null>(null);
const replayLoadError = ref("");

// Rep-level filtering (按单次动作筛选回放)
const allReplayFrames = ref<PoseReplayFrame[]>([]);
const repSegments = ref<PoseReplaySegment[]>([]);
const repNodes = ref<PoseReplayNode[]>([]);
const selectedRepFilter = ref<number | null>(null); // null = 全部, number = 第N次

const replayFullscreenRef = ref<HTMLDivElement | null>(null);
const isReplayFullscreen = ref(false);
const showReplaySettings = ref(false);
const selectedReplayBackground = ref("none");
const currentHighlights = ref<HighlightInstruction[]>([]);

const replayBackgroundOptions: ReplayBackgroundOption[] = [
  { label: "默认", value: "none" },
  { label: "背景 1", value: "bg-1", image: "/backgrounds/bg-1.png" },
  { label: "背景 2", value: "bg-2", image: "/backgrounds/bg-2.png" },
  { label: "背景 3", value: "bg-3", image: "/backgrounds/bg-3.png" },
];

const latestVideoUrl = ref<string>("");
const latestVideoLabel = ref<string>("最近分析结果");
const hasLatestAnalysis = ref(false);
const videoDuration = ref(0); // seconds
const videoCurrentTime = ref(0); // seconds
const latestExercise = ref("squat");

type VideoItem = { task_id: string; output_uri: string; exercise: string; created_at?: string; label: string; camera_view?: string };
const completedVideos = ref<VideoItem[]>([]);
const selectedVideoIndex = ref(0);
const activeView = ref<"front" | "side">("front");

const trendChartRef = ref<HTMLDivElement | null>(null);
const radarChartRef = ref<HTMLDivElement | null>(null);
const symmetryChartRef = ref<HTMLDivElement | null>(null);
const chartInstances: echarts.ECharts[] = [];

const activeTab = ref<"problems">("problems");
const selectedProblem = ref<number | null>(0);
const openAccordion = ref<number | null>(0);
const phases = ["准备阶段", "下蹲阶段", "底部停顿", "起身阶段", "结束阶段"];

// How many phases are "done" based on whether we have real analysis data
const phaseDoneCount = computed(() => hasLatestAnalysis.value ? phases.length : 0);

function exerciseDisplayName(key: string) {
  const names: Record<string, string> = {
    squat: "深蹲", pushup: "俯卧撑", jumping_jack: "开合跳", plank: "平板支撑"
  };
  return names[key] ?? key;
}

// Timeline helper
function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

const timelineStart = computed(() => formatTime(videoCurrentTime.value));
const timelineEnd = computed(() => {
  if (!videoDuration.value) return "--:--";
  return formatTime(videoDuration.value);
});
const timelineProgress = computed(() => {
  if (!videoDuration.value) return 0;
  return (videoCurrentTime.value / videoDuration.value) * 100;
});

const feedbackDescriptions: Record<string, string> = {
  下蹲深度不足: "下蹲深度不够，说明髋膝协同和动作控制还可以继续优化。",
  膝盖内扣: "膝关节向内偏移，可能带来额外膝部压力，需要加强外展控制。",
  躯干前倾过大: "躯干前倾幅度偏大，通常和髋部灵活性或核心稳定不足有关。",
  身体塌腰: "塌腰说明腹压和核心控制不足，动作稳定性会明显下降。",
  臀部下沉: "臀部下沉意味着核心与臀部发力不均衡，姿态保持能力不足。",
  手臂未举过肩: "肩部活动度受限，举臂路线不完整。",
  双脚打开不足: "站距偏窄会影响重心分配和下肢稳定性。",
};

const feedbackSuggestionMap: Record<string, string> = {
  下蹲深度不足: "继续降低重心，同时保持脚跟贴地和膝盖跟随脚尖方向。",
  膝盖内扣: "加入弹力带侧步和臀中肌激活训练，起身时主动向外推膝。",
  躯干前倾过大: "先建立腹压，再维持胸椎伸展，避免依赖腰背代偿完成动作。",
  身体塌腰: "强化核心稳定训练，保持骨盆中立，避免腰椎过度参与。",
  臀部下沉: "补充臀桥、平板支撑等训练，提升臀部与核心的协同控制。",
  手臂未举过肩: "增加肩关节灵活性和胸椎伸展练习，再逐步提高举臂角度。",
  双脚打开不足: "将站距调整到肩宽到 1.5 倍肩宽之间，找到更稳定的发力位置。",
};
const userName = computed(() => authStore.username || "用户");
const userInitial = computed(() => (userName.value || "U").charAt(0).toUpperCase());

const scoreValue = computed(() => statsData.value?.average_score);
const scoreValueForRing = computed(() => Math.round(Number(scoreValue.value ?? 86)));
const displayScore = computed(() => (scoreValue.value == null ? "--" : scoreValueForRing.value));

const scoreLabel = computed(() => {
  if (scoreValue.value == null) return "暂无";
  if (scoreValue.value >= 85) return "优秀";
  if (scoreValue.value >= 75) return "良好";
  if (scoreValue.value >= 60) return "中等";
  return "需改进";
});

const scoreLevel = computed(() => (scoreValue.value != null && scoreValue.value >= 75 ? "good" : ""));
const scoreChangeValue = computed(() => Number(statsData.value?.average_score_change ?? 0));
const scoreChangeTone = computed(() => (scoreChangeValue.value >= 0 ? "up" : "down"));
const scoreChangeIcon = computed(() => (scoreChangeValue.value >= 0 ? "up" : "down"));
const scoreChangeText = computed(() => {
  if (statsData.value?.average_score_change == null) return "--";
  return `${scoreChangeValue.value >= 0 ? "+" : ""}${scoreChangeValue.value.toFixed(1)}`;
});

const summarySubtitle = computed(() => {
  const stats = statsData.value;
  if (!stats || stats.total_sessions === 0) return "暂无训练记录，开始你的第一次训练吧";
  const last = stats.recent_sessions?.[0];
  if (last) {
    return `${last.exercise} · ${formatSessionDateTime(last.created_at)}`;
  }
  return `共 ${stats.total_sessions} 次训练`;
});

const sideMetrics = computed(() => {
  const base = Number(scoreValue.value ?? 0);
  return [
    {
      label: "动作流畅度",
      value: Math.min(100, Math.max(0, base ? base + 5 : 0)),
      cls: base >= 80 ? "good" : "warn",
      tip: "根据动作连续性与停顿时长综合评估。",
    },
    {
      label: "动作稳定性",
      value: Math.min(100, Math.max(0, base)),
      cls: base >= 80 ? "good" : "warn",
      tip: "根据重心偏移和关键点波动综合评估。",
    },
    {
      label: "关节活动度",
      value: Math.min(100, Math.max(0, base - 8)),
      cls: base >= 75 ? "good" : "warn",
      tip: "根据关键关节活动范围与动作深度综合评估。",
    },
    {
      label: "左右对称性",
      value: Math.min(100, Math.max(0, base - 3)),
      cls: base >= 78 ? "good" : "warn",
      tip: "根据左右侧角度差异和动作轨迹综合评估。",
    },
    {
      label: "姿态控制力",
      value: Math.min(100, Math.max(0, base ? base + 2 : 0)),
      cls: base >= 80 ? "good" : "warn",
      tip: "根据核心稳定和关键点控制能力综合评估。",
    },
  ];
});

const problems = computed<ProblemItem[]>(() => {
  // Use rep nodes/segments for per-rep filtering when available.
  if (repFeedbackSources.value.length > 0) {
    if (selectedRepFilter.value !== null) {
      // Show only issues from the selected rep
      const seg = repFeedbackSources.value.find((s) => s.rep_index === selectedRepFilter.value);
      if (!seg || !seg.issues || seg.issues.length === 0) {
        return [{
          title: `第${selectedRepFilter.value}次动作无问题`,
          desc: "该次动作表现良好，没有检测到明显问题。",
          level: "low", badge: "信息", time: "-", deduct: 0,
          recommend: "继续保持当前动作质量。", metric: null, bodyPart: null,
        }];
      }
      return seg.issues.map((item: PoseReplaySegmentIssue, idx: number) => {
        const level = (item.severity === "error" ? "high" : item.severity === "warning" ? "medium" : "low") as Severity;
        const metric = item.metric || inferMetricFromIssue(item.issue);
        const bodyPart = metric ? METRIC_BODY_PART_MAP[metric] ?? null : null;
        return {
          title: item.issue,
          desc: item.suggestion || `检测到动作问题：${item.issue}`,
          level,
          badge: level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险",
          time: `第${selectedRepFilter.value}次`,
          deduct: level === "high" ? 8 : level === "medium" ? 6 : 4,
          recommend: item.suggestion || "建议安排专项控制训练并结合视频回放逐步修正。",
          metric,
          bodyPart,
          repIndex: selectedRepFilter.value,
        };
      });
    }

    // Show all rep issues with "第N次" prefix
    const allProblems: ProblemItem[] = [];
    for (const seg of repFeedbackSources.value) {
      for (const item of seg.issues) {
        const level = (item.severity === "error" ? "high" : item.severity === "warning" ? "medium" : "low") as Severity;
        const metric = item.metric || inferMetricFromIssue(item.issue);
        const bodyPart = metric ? METRIC_BODY_PART_MAP[metric] ?? null : null;
        allProblems.push({
          title: `第${seg.rep_index}次：${item.issue}`,
          desc: item.suggestion || `检测到动作问题：${item.issue}`,
          level,
          badge: level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险",
          time: `第${seg.rep_index}次`,
          deduct: level === "high" ? 8 : level === "medium" ? 6 : 4,
          recommend: item.suggestion || "建议安排专项控制训练并结合视频回放逐步修正。",
          metric,
          bodyPart,
          repIndex: seg.rep_index,
        });
      }
    }
    if (allProblems.length === 0) {
      return [{
        title: "动作表现良好",
        desc: "全部动作均未检测到明显问题。",
        level: "low", badge: "信息", time: "-", deduct: 0,
        recommend: "继续保持当前动作质量。", metric: null, bodyPart: null,
      }];
    }
    return allProblems;
  }

  // Fallback: use feedbackItems from session feedback_summary
  if (feedbackItems.value.length === 0) {
    return [
      {
        title: "暂无问题数据",
        desc: "完成一次训练后，这里会自动展示识别到的主要动作问题。",
        level: "low",
        badge: "信息",
        time: "-",
        deduct: 0,
        recommend: "先开始一次训练，我们会基于结果给出更准确的纠正建议。",
        metric: null,
        bodyPart: null,
      },
    ];
  }

  return feedbackItems.value.slice(0, 5).map((feedback) => {
    const level = (feedback.severity || "low") as Severity;
    const metric = (feedback as any).metric || inferMetricFromIssue(feedback.issue);
    const bodyPart = metric ? METRIC_BODY_PART_MAP[metric] ?? null : null;
    return {
      title: feedback.issue,
      desc: feedbackDescriptions[feedback.issue] || `检测到动作问题：${feedback.issue}`,
      level,
      badge: level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险",
      time: feedback.created_at?.slice(0, 10) || "最近",
      deduct: level === "high" ? 8 : level === "medium" ? 6 : 4,
      recommend: feedbackSuggestionMap[feedback.issue] || "建议安排专项控制训练并结合视频回放逐步修正。",
      metric,
      bodyPart,
    };
  });
});
const currentProblem = computed(() => {
  if (selectedProblem.value === null) return null;
  return problems.value[selectedProblem.value] || null;
});

const issueSummary = computed(() => {
  return problems.value.slice(0, 2).map((item) => item.title).join(" · ") || "暂无";
});

// const totalDeduction = computed(() => problems.value.reduce((sum, item) => sum + item.deduct, 0));

const exerciseNameMap: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  jumping_jack: "开合跳",
  plank: "平板支撑",
  lunge: "弓步蹲",
  burpee: "波比跳",
  high_knees: "高抬腿",
  glute_bridge: "臀桥",
};

const selectedReplayExerciseName = computed(() => {
  const exercise = selectedReplay.value?.exercise;
  return exercise ? (exerciseNameMap[exercise] || exercise) : "未选择";
});

const selectedReplayScore = computed(() => {
  return selectedReplay.value ? Math.round(selectedReplay.value.average_score || 0) : scoreValueForRing.value;
});

const repFilters = computed<Array<{ rep_index: number }>>(() => {
  if (repNodes.value.length > 0) {
    return repNodes.value
      .filter((node) => Number.isFinite(node.rep_index))
      .sort((a, b) => a.rep_index - b.rep_index);
  }
  return repSegments.value;
});

const repFeedbackSources = computed<Array<{ rep_index: number; issues: PoseReplaySegmentIssue[] }>>(() => {
  if (repSegments.value.length > 0) {
    return repSegments.value.map((seg) => ({
      rep_index: seg.rep_index,
      issues: seg.issues || [],
    }));
  }
  return repNodes.value.map((node) => ({
    rep_index: node.rep_index,
    issues: node.issues || [],
  }));
});

function clampFrameIndex(value: number, fallback: number) {
  const max = Math.max(0, allReplayFrames.value.length - 1);
  if (!Number.isFinite(value)) return Math.min(max, Math.max(0, fallback));
  return Math.min(max, Math.max(0, Math.round(value)));
}

function estimateReplayFrameIntervalMs(frames: PoseReplayFrame[]) {
  const intervals: number[] = [];
  for (let index = 1; index < frames.length; index += 1) {
    const diff = frames[index].timestamp_ms - frames[index - 1].timestamp_ms;
    if (diff > 0 && diff < 1000) intervals.push(diff);
  }
  if (intervals.length === 0) return 100;
  intervals.sort((a, b) => a - b);
  return intervals[Math.floor(intervals.length / 2)] || 100;
}

function normalizeReplayFrames(frames: PoseReplayFrame[]) {
  if (frames.length === 0) return [];
  const baseTimestamp = frames[0].timestamp_ms || 0;
  const interval = estimateReplayFrameIntervalMs(frames);
  let previous = -interval;
  return frames.map((frame, index) => {
    const raw = Math.max(0, (frame.timestamp_ms || 0) - baseTimestamp);
    const timestamp_ms = raw > previous ? raw : previous + interval;
    previous = timestamp_ms;
    return {
      ...frame,
      timestamp_ms,
      landmarks: frame.landmarks,
    };
  });
}

function resolveRepFrameRange(repIndex: number) {
  const frameCount = allReplayFrames.value.length;
  if (frameCount === 0) return null;

  const nodes = [...repNodes.value]
    .filter((node) => Number.isFinite(node.rep_index) && Number.isFinite(node.frame_index))
    .sort((a, b) => a.rep_index - b.rep_index);
  const nodePosition = nodes.findIndex((node) => node.rep_index === repIndex);
  const segment = repSegments.value.find((seg) => seg.rep_index === repIndex);
  const intervalMs = estimateReplayFrameIntervalMs(allReplayFrames.value);
  const preRollFrames = Math.max(3, Math.round(450 / intervalMs));
  const postRollFrames = Math.max(4, Math.round(650 / intervalMs));

  if (nodePosition >= 0) {
    const node = nodes[nodePosition];
    const completion = clampFrameIndex(node.frame_index, 0);
    const previousCompletion = nodePosition > 0
      ? clampFrameIndex(nodes[nodePosition - 1].frame_index, 0)
      : -1;
    const nextCompletion = nodePosition < nodes.length - 1
      ? clampFrameIndex(nodes[nodePosition + 1].frame_index, frameCount - 1)
      : frameCount;

    const nodeStart = Number.isFinite(node.start_frame_index)
      ? clampFrameIndex(node.start_frame_index as number, completion)
      : null;
    const segmentStart = segment ? clampFrameIndex(segment.start_frame_index, completion) : null;
    const lowerBound = previousCompletion >= 0 ? previousCompletion + 1 : 0;
    const upperBound = nextCompletion < frameCount ? nextCompletion - 1 : frameCount - 1;
    const inferredStart = nodeStart ?? segmentStart ?? Math.max(lowerBound, completion - Math.round((completion - lowerBound) * 0.75));

    const start = Math.max(lowerBound, clampFrameIndex(inferredStart - preRollFrames, completion));
    const end = Math.max(start, Math.min(upperBound, completion + postRollFrames));
    return { start, end };
  }

  if (segment) {
    const start = clampFrameIndex(segment.start_frame_index, 0);
    const end = Math.max(start, clampFrameIndex(segment.end_frame_index, start));
    return { start, end };
  }

  return null;
}

const replayDurationMs = computed(() => {
  return Math.max(0, selectedReplayFrames.value[selectedReplayFrames.value.length - 1]?.timestamp_ms || 0);
});

const replayCurrentTime = computed(() => formatReplayTime(replayProgress.value * replayDurationMs.value));
const replayDurationText = computed(() => formatReplayTime(replayDurationMs.value));
const replayStageLabel = computed(() => {
  if (replayLoadError.value) return replayLoadError.value;
  if (!selectedReplaySessionId.value) return "请选择一次保存的运动";
  if (selectedReplayFrames.value.length === 0) return "该记录暂无 3D 回放数据";
  return `${selectedReplayExerciseName.value} · ${replayCurrentTime.value} / ${replayDurationText.value}`;
});

const selectedReplayBackgroundImage = computed(() => {
  const selected = replayBackgroundOptions.find((option) => option.value === selectedReplayBackground.value);
  return selected?.image ?? "";
});

function toggleAccordion(index: number) {
  openAccordion.value = openAccordion.value === index ? null : index;
}

async function toggleReplayFullscreen() {
  const target = replayFullscreenRef.value;
  if (!target || !document.fullscreenEnabled) return;

  if (document.fullscreenElement === target) {
    await document.exitFullscreen();
    return;
  }

  await target.requestFullscreen();
}

function syncReplayFullscreenState() {
  isReplayFullscreen.value = document.fullscreenElement === replayFullscreenRef.value;
  if (!isReplayFullscreen.value) {
    showReplaySettings.value = false;
  }
}

function formatReplayTime(ms: number) {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function formatSessionDateTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 16).replace("T", " ");
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function sessionOptionLabel(session: SessionRecord) {
  const date = formatSessionDateTime(session.created_at);
  const exercise = exerciseNameMap[session.exercise] || session.exercise;
  const replayMark = session.has_pose_replay ? " 🎬" : "  ·";
  return `${date} · ${exercise} · ${Math.round(session.average_score || 0)}分${replayMark}`;
}

function onReplayFrameChange(frame: PoseReplayFrame | null) {
  replayFrame.value = frame;
}

// Rep filter switching
function switchToRep(repIndex: number | null) {
  if (selectedRepFilter.value === repIndex) return;
  selectedRepFilter.value = repIndex;
  replayProgress.value = 0;
  replayPlaying.value = true;
  selectedProblem.value = 0;
  currentHighlights.value = [];
}

// Watch rep filter changes to reset highlights
watch(selectedRepFilter, () => {
  selectedProblem.value = 0;
  currentHighlights.value = [];
});

// Load feedback from the selected session's feedback_summary
async function loadSessionFeedback(sessionId: string) {
  try {
    const session = await getSession(sessionId);
    if (session && (session as any).feedback_summary) {
      let summary = (session as any).feedback_summary;
      if (typeof summary === "string") summary = JSON.parse(summary);
      if (summary && Array.isArray(summary.items)) {
        // Map feedback_summary items to FeedbackItem-like shape for the problems computed
        feedbackItems.value = summary.items.map((item: any) => ({
          id: item.id || sessionId,
          session_id: sessionId,
          exercise: session.exercise || "",
          issue: item.issue || "",
          severity: item.severity === "error" ? "high" : item.severity === "warning" ? "medium" : "low",
          suggestion: item.suggestion || "",
          metric: item.metric || "",
          value: item.value || 0,
          created_at: item.created_at || session.created_at || "",
        }));
      } else {
        feedbackItems.value = [];
      }
    } else {
      feedbackItems.value = [];
    }
  } catch (error) {
    console.warn("Session feedback load failed:", error);
    feedbackItems.value = [];
  }
  // Reset highlight and selection
  selectedProblem.value = 0;
  currentHighlights.value = [];
}

// Click on right panel problem → highlight 3D body part
function onProblemClick(index: number) {
  selectedProblem.value = index;
  const problem = problems.value[index];
  const canHighlightCurrentRep = selectedRepFilter.value !== null
    && problem?.repIndex === selectedRepFilter.value;
  if (!canHighlightCurrentRep) {
    currentHighlights.value = [];
    return;
  }
  if (!problem || !problem.metric) {
    currentHighlights.value = [];
    return;
  }
  const mapping = METRIC_BODY_PART_MAP[problem.metric];
  if (mapping) {
    currentHighlights.value = [
      {
        bonePairs: mapping.bones,
        color: severityToHighlightColor(problem.level),
        pulseSpeed: severityToPulseSpeed(problem.level),
      },
    ];
  } else {
    currentHighlights.value = [];
  }
}

// Click on 3D body part → select corresponding problem in right panel
function on3DBodyPartClicked(bonePair: [number, number]) {
  const idx = problems.value.findIndex((p) => {
    if (!p.bodyPart) return false;
    return p.bodyPart.bones.some(
      (b) => (b[0] === bonePair[0] && b[1] === bonePair[1]) || (b[0] === bonePair[1] && b[1] === bonePair[0]),
    );
  });
  if (idx >= 0) {
    onProblemClick(idx);
    activeTab.value = "problems";
    nextTick(() => {
      document.querySelector(`.problem-item:nth-child(${idx + 1})`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }
}

async function loadReplaySessions() {
  replaySessionsLoading.value = true;
  try {
    const response = await getSessions({ limit: 20 });
    replaySessions.value = (response.items || []).filter(Boolean);

    if (!selectedReplaySessionId.value && replaySessions.value.length > 0) {
      // 过滤掉可能的 null 项
      const validItems = replaySessions.value.filter(Boolean);
      // 优先使用 has_pose_replay 标记找到有回放数据的记录
      const replaySession = validItems.find((s) => s.has_pose_replay);
      if (replaySession) {
        selectedReplaySessionId.value = replaySession.session_id;
        selectedReplay.value = replaySession;
        await loadSelectedReplay();
        return;
      }
      // 没有回放标记时，回退到按顺序探测
      for (const session of validItems) {
        if (await tryLoadReplayForSession(session)) return;
      }
      // 实在没有，就加载最新一条
      const firstValid = validItems[0];
      if (firstValid) {
        selectedReplaySessionId.value = firstValid.session_id;
        await loadSelectedReplay();
      }
    }
  } catch (error) {
    console.warn("Replay sessions load failed:", error);
    replaySessions.value = [];
  } finally {
    replaySessionsLoading.value = false;
  }
}

async function tryLoadReplayForSession(session: SessionRecord) {
  try {
    const replay = await getSessionReplay(session.session_id);
    if (!replay.has_replay || replay.frames.length === 0) return false;
    selectedReplaySessionId.value = session.session_id;
    selectedReplay.value = session;
    allReplayFrames.value = replay.frames;
    repSegments.value = replay.meta?.rep_segments || [];
    repNodes.value = replay.meta?.rep_nodes || [];
    replayPlaying.value = true;
    replayProgress.value = 0;
    replayLoadError.value = "";
    await loadSessionFeedback(session.session_id);
    return true;
  } catch (error) {
    console.warn("Replay probe failed:", error);
    return false;
  }
}

async function loadSelectedReplay() {
  replayLoadError.value = "";
  replayPlaying.value = false;
  replayProgress.value = 0;
  allReplayFrames.value = [];
  repSegments.value = [];
  repNodes.value = [];
  selectedRepFilter.value = null;
  selectedReplay.value = (replaySessions.value.find((session) => session && session.session_id === selectedReplaySessionId.value)) || null;

  if (!selectedReplaySessionId.value) return;

  try {
    const replay = await getSessionReplay(selectedReplaySessionId.value);
    if (!replay) {
      replayLoadError.value = "未找到回放数据";
      return;
    }
    allReplayFrames.value = replay.has_replay ? replay.frames : [];
    replayPlaying.value = allReplayFrames.value.length > 0;
    if (replay.has_replay && replay.frames.length === 0) {
      replayLoadError.value = "该记录已标记有回放但数据为空";
    }
    // Capture rep nodes/segments from meta.
    repSegments.value = replay.meta?.rep_segments || [];
    repNodes.value = replay.meta?.rep_nodes || [];
    // Load session feedback for the selected replay
    await loadSessionFeedback(selectedReplaySessionId.value);
  } catch (error) {
    console.warn("Replay load failed:", error);
    replayLoadError.value = "回放数据加载失败";
  }
}

function encodeFilePath(path: string) {
  return path.replace(/\\/g, "/").split("/").map(encodeURIComponent).join("/");
}

function disposeCharts() {
  while (chartInstances.length > 0) {
    chartInstances.pop()?.dispose();
  }
}

function createChart(el: HTMLDivElement, option: echarts.EChartsCoreOption) {
  const chart = echarts.init(el);
  chart.setOption(option);
  chartInstances.push(chart);
}

function resizeCharts() {
  chartInstances.forEach((chart) => chart.resize());
}

function buildCharts() {
  disposeCharts();

  const trendData = statsData.value?.recent_trend || [];
  const trendDates = trendData.length ? trendData.map((item: any) => String(item.date).slice(5)) : ["暂无数据"];
  const trendScores = trendData.length ? trendData.map((item: any) => Number(item.score)) : [0];
  const score = Number(scoreValue.value ?? 80);
  const metricValues = sideMetrics.value.map((item) => item.value);

  if (trendChartRef.value) {
    createChart(trendChartRef.value, {
      color: ["#5b8cff"],
      grid: { left: 40, right: 14, top: 12, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(255,255,255,0.94)",
        borderColor: "#cbd5e1",
        textStyle: { color: "#0f172a" },
        formatter: (params: any[]) => {
          const point = params[0];
          return `${point.axisValue}: ${point.value} 分`;
        },
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: trendDates,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisTick: { show: false },
        axisLabel: { color: "#64748b", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        min: 60,
        max: 100,
        interval: 10,
        splitLine: { lineStyle: { color: "rgba(203,213,225,0.6)", type: "dashed" } },
        axisLabel: { color: "#64748b", fontSize: 11 },
      },
      series: [
        {
          type: "line",
          smooth: true,
          symbolSize: 7,
          lineStyle: { width: 2.5 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(91,140,255,0.2)" },
              { offset: 1, color: "rgba(91,140,255,0.02)" },
            ]),
          },
          data: trendScores,
        },
      ],
    });
  }

  if (radarChartRef.value) {
    createChart(radarChartRef.value, {
      color: ["#5b8cff"],
      tooltip: {
        backgroundColor: "rgba(255,255,255,0.94)",
        borderColor: "#cbd5e1",
        textStyle: { color: "#0f172a" },
      },
      radar: {
        center: ["50%", "52%"],
        radius: "68%",
        indicator: [
          { name: "动作流畅度", max: 100 },
          { name: "动作稳定性", max: 100 },
          { name: "关节活动度", max: 100 },
          { name: "左右对称性", max: 100 },
          { name: "姿态控制力", max: 100 },
        ],
        axisName: { color: "#64748b", fontSize: 11 },
        splitArea: { areaStyle: { color: ["#f8fafc", "#f1f5f9"] } },
        splitLine: { lineStyle: { color: "#cbd5e1" } },
        axisLine: { lineStyle: { color: "#cbd5e1" } },
      },
      series: [
        {
          type: "radar",
          data: [{ value: metricValues, name: "当前表现" }],
          areaStyle: { color: "rgba(91,140,255,0.15)" },
          lineStyle: { color: "#5b8cff", width: 2 },
          itemStyle: { color: "#5b8cff" },
          symbolSize: 4,
        },
      ],
    });
  }

  if (symmetryChartRef.value) {
    createChart(symmetryChartRef.value, {
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(255,255,255,0.94)",
        borderColor: "#cbd5e1",
        textStyle: { color: "#0f172a" },
      },
      legend: {
        data: ["左侧", "右侧"],
        textStyle: { color: "#64748b", fontSize: 10 },
        top: 0,
      },
      grid: { left: 40, right: 14, top: 26, bottom: 28 },
      xAxis: {
        type: "category",
        data: ["髋部", "腿部", "膝关节", "踝关节"],
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisTick: { show: false },
        axisLabel: { color: "#64748b", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: "rgba(203,213,225,0.6)", type: "dashed" } },
        axisLabel: { color: "#64748b", fontSize: 11 },
      },
      series: [
        {
          type: "bar",
          name: "左侧",
          data: [score + 5, score, score - 10, score - 3],
          color: "#5b8cff",
          barWidth: 14,
          itemStyle: { borderRadius: [3, 3, 0, 0] },
        },
        {
          type: "bar",
          name: "右侧",
          data: [score + 8, score + 3, score - 14, score],
          color: "#25b87b",
          barWidth: 14,
          itemStyle: { borderRadius: [3, 3, 0, 0] },
        },
      ],
    });
  }
}

function onVideoMetadata(e: Event) {
  const video = e.target as HTMLVideoElement;
  if (video && video.duration && isFinite(video.duration)) {
    videoDuration.value = video.duration;
  }
}

function onVideoTimeUpdate(e: Event) {
  const video = e.target as HTMLVideoElement;
  videoCurrentTime.value = video.currentTime;
}

async function loadVideoBlob(outputUri: string): Promise<string | null> {
  const fileUrl = `/api/files/${encodeFilePath(outputUri)}`;
  const token = authStore.token;
  const res = await fetch(fileUrl, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) return null;
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

async function switchToVideo(index: number) {
  if (index === selectedVideoIndex.value) return;
  const item = completedVideos.value[index];
  if (!item) return;
  // Revoke old blob
  if (latestVideoUrl.value && latestVideoUrl.value.startsWith("blob:")) {
    URL.revokeObjectURL(latestVideoUrl.value);
  }
  const url = await loadVideoBlob(item.output_uri);
  if (!url) return;
  selectedVideoIndex.value = index;
  latestVideoUrl.value = url;
  latestVideoLabel.value = item.label;
  latestExercise.value = item.exercise || "squat";
  // Reset timeline state for new video
  videoDuration.value = 0;
  videoCurrentTime.value = 0;
}

async function loadCompletedVideos() {
  // Revoke old blob
  if (latestVideoUrl.value && latestVideoUrl.value.startsWith("blob:")) {
    URL.revokeObjectURL(latestVideoUrl.value);
  }
  latestVideoUrl.value = "";
  hasLatestAnalysis.value = false;
  completedVideos.value = [];
  selectedVideoIndex.value = 0;
  videoDuration.value = 0;
  videoCurrentTime.value = 0;

  try {
    const data = await apiGet<{ items: Array<{ task_id: string; status: string; output_uri?: string | null; exercise: string; created_at?: string; camera_view?: string }> }>("/analysis/tasks");
    const completed = (data.items || [])
      .filter(t => (t.status === "success" || t.status === "completed") && t.output_uri && (t.camera_view || "front") === activeView.value)
      .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
    completedVideos.value = completed.map(t => {
      const d = t.created_at ? new Date(t.created_at) : null;
      const timeStr = d ? `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}` : "";
      return {
        task_id: t.task_id,
        output_uri: t.output_uri!,
        exercise: t.exercise || "squat",
        created_at: t.created_at,
        camera_view: t.camera_view || "front",
        label: `${exerciseDisplayName(t.exercise || "squat")} · ${timeStr}`,
      };
    });
    if (completedVideos.value.length > 0) {
      const latest = completedVideos.value[0];
      hasLatestAnalysis.value = true;
      latestExercise.value = latest.exercise || "squat";
      latestVideoLabel.value = latest.label;
      const url = await loadVideoBlob(latest.output_uri);
      if (url) latestVideoUrl.value = url;
    }
  } catch {
    // no video available
  }
}

async function switchView(view: "front" | "side") {
  if (activeView.value === view) return;
  activeView.value = view;
  await loadCompletedVideos();
}

onMounted(async () => {
  try {
    const [statsResult, feedbackResult] = await Promise.allSettled([
      getDashboardStats(),
      getFeedbacks({ limit: 10 }),
    ]);

    if (statsResult.status === "fulfilled") {
      statsData.value = statsResult.value;
    }

    if (feedbackResult.status === "fulfilled") {
      feedbackItems.value = feedbackResult.value.items || [];
    }

    // Handle ?replay=sessionId from SessionsView
    const replayParam = route.query.replay as string | undefined;
    if (replayParam) {
      selectedReplaySessionId.value = replayParam;
    }

    await loadReplaySessions();
  } catch (error) {
    console.warn("Dashboard data load failed:", error);
    statsData.value = null;
    feedbackItems.value = [];
  } finally {
    statsLoading.value = false;
    await nextTick();
    buildCharts();
  }

  // Load all completed skeleton videos for the selector
  await loadCompletedVideos();

  window.addEventListener("resize", resizeCharts);
  document.addEventListener("fullscreenchange", syncReplayFullscreenState);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  document.removeEventListener("fullscreenchange", syncReplayFullscreenState);
  disposeCharts();
  if (latestVideoUrl.value && latestVideoUrl.value.startsWith("blob:")) {
    URL.revokeObjectURL(latestVideoUrl.value);
  }
});
</script>

<style scoped>
.sports-dashboard {
  display: grid;
  gap: 18px;
  max-width: 1560px;
  margin: 0 auto;
}

.top-header,
.main-panel,
.section-card,
.chart-card {
  border: 1px solid #d6e3ff;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.07);
}

.top-header {
  display: grid;
  grid-template-columns: auto auto 1fr auto;
  align-items: center;
  gap: 28px;
  padding: 16px 24px;
}

.th-left,
.panel-left,
.th-score,
.th-compare {
  display: flex;
  align-items: center;
}

.th-left {
  gap: 14px;
}

.th-avatar {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: linear-gradient(135deg, #5b8cff, #4f46e5);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
}

.th-info strong,
.panel-title-icon h2,
.chart-card-header h3,
.sc-header h3,
.pi-title-row strong,
.ai-body strong {
  color: #0f172a;
}

.th-info p,
.th-score-label,
.th-score-unit,
.th-compare-label,
.ms-label,
.sc-header p,
.pi-info p,
.pi-meta span,
.accordion-count,
.ai-body p,
.ai-prescription,
.chart-pill,
.tl-labels {
  color: #64748b;
}

.th-score {
  gap: 10px;
}

.th-score-value {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.th-score-num {
  font-size: 30px;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(135deg, #5b8cff, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.th-score-badge,
.phase-badge,
.status-pill,
.phase-now,
.pi-badge,
.tab-count,
.chart-pill,
.cf-badge {
  border-radius: 999px;
  font-weight: 700;
}

.th-score-badge {
  padding: 2px 10px;
  font-size: 10px;
}

.th-score-badge.good,
.score-ring-grade.good,
.cf-badge.good {
  background: rgba(37, 184, 123, 0.12);
  color: #25b87b;
}

.th-compare {
  gap: 8px;
}

.th-compare-value {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 20px;
  font-weight: 800;
}

.th-compare-value.up {
  color: #25b87b;
}

.th-compare-value.down {
  color: #ef4444;
}

.th-actions {
  justify-self: end;
}

.btn-primary,
.btn-full-plan,
.ba-btn,
.tab-btn,
.accordion-header,
.view-angle,
.play-btn-small,
.speed-mini button {
  cursor: pointer;
}

.btn-primary,
.tab-btn.active,
.play-btn-small,
.ba-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #5b8cff, #4f46e5);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(91, 140, 255, 0.3);
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1.5px solid #5b8cff;
  border-radius: 10px;
  background: transparent;
  color: #5b8cff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}
.btn-outline:hover {
  background: #eff6ff;
}

.core-row {
  display: grid;
  grid-template-columns: 1.38fr 1fr;
  gap: 18px;
  align-items: start;
}

.main-panel {
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid #e8effd;
  background: #f8fafc;
}

.panel-left {
  gap: 14px;
  flex-wrap: wrap;
}

.panel-title-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title-icon svg,
.skel-stage-label,
.phase-step.active .phase-label,
.btn-full-plan {
  color: #5b8cff;
}

.phase-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 12px;
  background: rgba(91, 140, 255, 0.08);
  font-size: 12px;
}

.phase-badge strong {
  color: #0f172a;
}

.phase-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.pulse-blue {
  background: #5b8cff;
  box-shadow: 0 0 10px rgba(91, 140, 255, 0.5);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 12px;
  font-size: 12px;
}

.status-pill.warn,
.cf-badge.warn {
  background: rgba(249, 115, 22, 0.08);
  color: #f97316;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e8effd;
}

.ms-item {
  display: grid;
  gap: 4px;
}

.ms-item strong,
.score-ring-num {
  font-weight: 900;
}

.ms-item .good,
.ms-track .good {
  color: #25b87b;
  background: linear-gradient(90deg, #17a36b, #25b87b);
}

.ms-item .warn,
.ms-track .warn {
  color: #f97316;
  background: linear-gradient(90deg, #ea580c, #f97316);
}

.ms-track {
  height: 4px;
  border-radius: 999px;
  overflow: hidden;
  background: #e2e8f0;
}

.ms-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.skel-area {
  position: relative;
  min-height: 400px;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.replay-fullscreen-shell {
  position: relative;
  background: #01040a;
}

.replay-fullscreen-shell:fullscreen {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #01040a;
}

.replay-fullscreen-shell:fullscreen .replay-stage {
  min-height: 0;
  height: 100%;
}

.replay-fullscreen-shell:fullscreen .phase-flow-bar {
  position: relative;
  z-index: 10;
  gap: 0;
  padding: 14px 22px 18px;
  background: rgba(1, 4, 10, 0.92);
  border-top-color: rgba(96, 165, 250, 0.18);
}

.replay-fullscreen-shell:fullscreen .replay-toolbar,
.replay-fullscreen-shell:fullscreen .phase-flow,
.replay-fullscreen-shell:fullscreen .rep-filter-bar {
  display: none;
}

.replay-fullscreen-shell:fullscreen .play-controls {
  max-width: 960px;
  width: min(960px, calc(100vw - 44px));
  margin: 0 auto;
}

.replay-stage {
  min-height: clamp(520px, 58vw, 720px);
  background:
    linear-gradient(rgba(1, 4, 10, 0.56), rgba(1, 4, 10, 0.64)),
    radial-gradient(circle at 50% 46%, rgba(56, 213, 255, 0.13), transparent 26%),
    radial-gradient(circle at 50% 82%, rgba(56, 213, 255, 0.1), transparent 16%),
    linear-gradient(180deg, #000 0%, #01040a 54%, #020710 100%);
}

.replay-stage .skel-layout {
  display: none;
}

.skel-grid {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, transparent, rgba(96, 224, 255, 0.055), transparent),
    radial-gradient(circle at 50% 88%, rgba(96, 224, 255, 0.16), transparent 22%);
  opacity: 0.55;
}

.skel-stage-label,
.view-strip {
  position: absolute;
  z-index: 5;
  border: 1px solid #d6e3ff;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
}

.skel-stage-label {
  top: 10px;
  left: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  max-width: calc(100% - 28px);
  flex-wrap: wrap;
}

.video-selector--standalone {
  position: absolute;
  z-index: 5;
  top: 10px;
  left: 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  max-width: calc(100% - 28px);
}

.video-selector {
  margin-left: 4px;
  padding: 3px 8px;
  border: 1px solid rgba(91, 140, 255, 0.25);
  border-radius: 6px;
  background: #ffffff;
  color: #5b8cff;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  max-width: 200px;
  text-overflow: ellipsis;
}
.video-selector:focus {
  border-color: #5b8cff;
}
.video-selector option {
  background: #ffffff;
  color: #0f172a;
}

.skel-layout {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 220px;
}

.pose-skeleton {
  width: 100%;
  height: auto;
  display: block;
}

.pose-video {
  width: 100%;
  max-width: 320px;
  height: auto;
  border-radius: 8px;
  display: block;
  object-fit: contain;
}

.breathing-skel {
  animation: breathe 4s ease-in-out infinite;
  transform-origin: center center;
}

@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

.warning-anim {
  animation: pulseWarn 1.8s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { opacity: 0.6; r: 5; }
  50% { opacity: 1; r: 6.2; }
}

.score-card-overlay {
  position: static;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border: 1px solid rgba(59, 130, 246, 0.1);
  border-radius: 10px;
  background: rgba(8, 13, 26, 0.42);
}

.replay-fullscreen-button {
  position: absolute;
  right: 16px;
  bottom: 16px;
  z-index: 8;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(96, 165, 250, 0.22);
  border-radius: 8px;
  background: rgba(8, 13, 26, 0.72);
  color: #dbeafe;
  backdrop-filter: blur(10px);
}

.replay-settings-button {
  position: absolute;
  right: 16px;
  bottom: 62px;
  z-index: 8;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(96, 165, 250, 0.22);
  border-radius: 8px;
  background: rgba(8, 13, 26, 0.72);
  color: #dbeafe;
  backdrop-filter: blur(10px);
}

.replay-settings-button:hover {
  border-color: rgba(147, 197, 253, 0.48);
  background: rgba(15, 23, 42, 0.9);
  color: #ffffff;
}

.replay-fullscreen-button:hover {
  border-color: rgba(147, 197, 253, 0.48);
  background: rgba(15, 23, 42, 0.9);
  color: #ffffff;
}

.replay-fullscreen-shell:fullscreen .replay-fullscreen-button {
  right: 22px;
  bottom: 22px;
}

.replay-fullscreen-shell:fullscreen .replay-settings-button {
  right: 22px;
  bottom: 68px;
}

.replay-settings-panel {
  position: absolute;
  top: 22px;
  right: 22px;
  z-index: 12;
  width: min(300px, calc(100vw - 44px));
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(96, 165, 250, 0.24);
  border-radius: 12px;
  background: rgba(5, 10, 24, 0.86);
  color: #e2e8f0;
  backdrop-filter: blur(16px);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

.replay-settings-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.replay-settings-panel header strong {
  color: #f8fafc;
  font-size: 14px;
}

.replay-settings-panel header button {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 7px;
  background: rgba(15, 23, 42, 0.78);
  color: #cbd5e1;
  font-size: 18px;
  line-height: 1;
}

.replay-background-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.replay-background-option {
  display: grid;
  gap: 7px;
  padding: 7px;
  border: 1px solid rgba(96, 165, 250, 0.16);
  border-radius: 9px;
  background: rgba(15, 23, 42, 0.56);
  color: #cbd5e1;
  text-align: left;
}

.replay-background-option.active {
  border-color: rgba(125, 211, 252, 0.78);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.28);
  color: #ffffff;
}

.replay-background-option img,
.replay-background-none {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: block;
  border-radius: 6px;
  object-fit: cover;
  background:
    radial-gradient(circle at 50% 45%, rgba(56, 213, 255, 0.18), transparent 42%),
    linear-gradient(180deg, #000, #07101f);
}

.replay-background-option b {
  font-size: 12px;
}

.score-ring-big {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 1px;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(255, 255, 255, 0.95) 38%, transparent 39%),
    conic-gradient(#25b87b 0 var(--ring-pct, 0%), rgba(203, 213, 225, 0.1) var(--ring-pct, 0%) 100%);
  border: 2px solid rgba(37, 184, 123, 0.2);
  animation: ringPulse 3s ease-in-out infinite;
}

@keyframes ringPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(37, 184, 123, 0.25); }
  50% { box-shadow: 0 0 16px 4px rgba(37, 184, 123, 0.15); }
}

.score-ring-label {
  font-size: 8px;
  color: #64748b;
}

.score-ring-meta {
  display: grid;
  gap: 5px;
}

.score-ring-grade {
  width: fit-content;
  padding: 2px 8px;
  font-size: 10px;
}

.score-ring-issues {
  color: #64748b;
  font-size: 11px;
}

.score-ring-issues strong,
.pi-deduct strong,
.score-deduct {
  color: #ef4444;
}

.view-strip {
  top: 10px;
  right: 14px;
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 8px;
}

.replay-stage .view-strip {
  display: none;
}

.replay-session-picker {
  position: static;
  width: min(360px, 100%);
  display: grid;
  gap: 6px;
  padding: 0;
  border: 1px solid rgba(59, 130, 246, 0.16);
  border-radius: 10px;
  background: rgba(8, 13, 26, 0.42);
}

.replay-session-picker span {
  padding: 8px 10px 0;
  color: #93c5fd;
  font-size: 11px;
  font-weight: 800;
}

.replay-session-picker select {
  width: 100%;
  min-width: 0;
  min-height: 34px;
  padding: 0 10px;
  border: 0;
  border-top: 1px solid rgba(59, 130, 246, 0.16);
  border-radius: 0 0 10px 10px;
  background: rgba(15, 23, 42, 0.72);
  color: #e2e8f0;
  font-size: 12px;
}

.view-angle {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
}

.view-angle.active {
  background: rgba(91, 140, 255, 0.12);
  color: #5b8cff;
}

.view-angle.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.phase-flow-bar {
  display: grid;
  gap: 12px;
  padding: 14px 18px;
  border-top: 1px solid rgba(59, 130, 246, 0.06);
  background: rgba(2, 6, 16, 0.86);
}

.replay-toolbar {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.phase-flow {
  position: relative;
  display: flex;
  align-items: center;
}

.phase-step {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  text-align: center;
}

.phase-circle {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background: #f1f5f9;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 700;
}

.phase-step.done .phase-circle {
  background: rgba(37, 184, 123, 0.15);
  border-color: #25b87b;
  color: #25b87b;
}

.phase-step.active .phase-circle {
  background: rgba(91, 140, 255, 0.15);
  border-color: #5b8cff;
  color: #5b8cff;
}

.phase-label {
  font-size: 10px;
  color: #94a3b8;
}

.phase-now {
  padding: 1px 7px;
  background: rgba(91, 140, 255, 0.12);
  color: #5b8cff;
  font-size: 8px;
}

.phase-connector {
  position: absolute;
  left: 0;
  right: 0;
  top: 12px;
  z-index: 1;
  height: 2px;
  margin: 0 calc(50% + 12px);
  background: #cbd5e1;
  border-radius: 999px;
}

.phase-connector-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5b8cff, #7db4ff);
  transition: width 0.6s ease;
}

.phase-no-data {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 8px 0;
}

.play-controls {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}

.play-btn-small {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 50%;
}

.timeline-mini {
  display: grid;
  gap: 4px;
}

.replay-range {
  width: 100%;
  accent-color: #60a5fa;
}

.tl-track {
  position: relative;
  height: 4px;
  border-radius: 999px;
  background: #cbd5e1;
}

.tl-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5b8cff, #8b5cf6);
  transition: width 0.6s ease;
}

.tl-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #0f172a;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  transition: left 0.6s ease;
}

.tl-labels,
.tab-bar,
.pi-title-row,
.pi-meta,
.chart-footer,
.bottom-actions {
  display: flex;
}

.tl-labels {
  justify-content: space-between;
  font-size: 10px;
}

.speed-mini {
  gap: 2px;
}

.speed-mini button,
.ba-btn,
.btn-full-plan {
  border: 1px solid #d6e3ff;
  background: rgba(91, 140, 255, 0.05);
  color: #64748b;
}

.speed-mini button {
  padding: 3px 7px;
  border-radius: 4px;
  font-size: 10px;
}

.speed-mini button.active {
  background: rgba(91, 140, 255, 0.12);
  color: #5b8cff;
}

/* Rep filter bar (按单次动作筛选) */
.rep-filter-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 0;
}

.rep-filter-btn {
  padding: 4px 12px;
  border: 1px solid rgba(91, 140, 255, 0.16);
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.56);
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.rep-filter-btn:hover {
  border-color: rgba(96, 165, 250, 0.38);
  color: #cbd5e1;
}
.rep-filter-btn.active {
  background: rgba(91, 140, 255, 0.15);
  border-color: rgba(96, 165, 250, 0.48);
  color: #5b8cff;
}

.right-col {
  display: grid;
  gap: 14px;
  align-content: start;
}

.tab-bar {
  gap: 6px;
  padding: 4px;
  border: 1px solid #d6e3ff;
  border-radius: 12px;
  background: #ffffff;
}

.tab-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
}

.section-card {
  padding: 18px;
}

.sc-header {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8effd;
}

.sc-header-icon,
.qa-icon,
.ai-num {
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.sc-header-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.sc-header-icon.danger {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

.sc-header-icon.success,
.qa-icon,
.ai-num {
  background: rgba(37, 184, 123, 0.1);
  color: #25b87b;
}

.problem-list,
.advice-accordion,
.accordion-body {
  display: grid;
  gap: 8px;
}

.problem-item,
.advice-item {
  padding: 12px;
  border-radius: 9px;
}

.problem-item {
  border: 1px solid transparent;
}

.problem-item.high {
  background: rgba(239, 68, 68, 0.04);
  border-color: rgba(239, 68, 68, 0.1);
}

.problem-item.medium {
  background: rgba(249, 115, 22, 0.04);
  border-color: rgba(249, 115, 22, 0.1);
}

.problem-item.low {
  background: rgba(91, 140, 255, 0.03);
  border-color: rgba(91, 140, 255, 0.07);
}

.problem-item.selected {
  outline: 1px solid rgba(91, 140, 255, 0.3);
  box-shadow: 0 0 12px rgba(91, 140, 255, 0.15);
}

.pi-body-part {
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 700;
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
  margin-left: 6px;
}

.pi-top,
.advice-item {
  display: flex;
  gap: 10px;
}

.pi-num {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 800;
  flex-shrink: 0;
}

.pi-num.high,
.pi-badge.high {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.pi-num.medium,
.pi-badge.medium {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.pi-num.low,
.pi-badge.low {
  background: rgba(91, 140, 255, 0.08);
  color: #5b8cff;
}

.pi-badge {
  padding: 1px 8px;
  font-size: 9px;
}

.advice-card {
  margin-top: 14px;
  padding: 12px;
  border-radius: 9px;
  border: 1px solid rgba(37, 184, 123, 0.1);
  background: rgba(37, 184, 123, 0.04);
  display: flex;
  gap: 10px;
}
.advice-card-icon {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: rgba(37, 184, 123, 0.1);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: #25b87b;
}
.advice-card-body strong {
  display: block;
  margin-bottom: 3px;
  font-size: 13px;
}
.advice-card-body p {
  font-size: 12px;
  line-height: 1.5;
  color: #475569;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.chart-card {
  padding: 16px;
}

.chart-card-header,
.chart-footer {
  justify-content: space-between;
  align-items: center;
}

.chart-card-header {
  margin-bottom: 14px;
}

.chart-body {
  width: 100%;
  height: 260px;
}

.chart-footer {
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.cf-badge {
  padding: 4px 10px;
  font-size: 11px;
}

.bottom-actions {
  gap: 12px;
  flex-wrap: wrap;
}

.ba-btn {
  padding: 12px 18px;
  border-radius: 10px;
}

@keyframes pulseWarn {
  0%,
  100% {
    opacity: 0.7;
  }

  50% {
    opacity: 1;
  }
}

@media (max-width: 1200px) {
  .top-header,
  .core-row,
  .charts-row {
    grid-template-columns: 1fr;
  }

  .top-header {
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .sports-dashboard {
    gap: 14px;
  }

  .top-header,
  .chart-card,
  .section-card {
    padding: 14px;
  }

  .metric-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .play-controls {
    grid-template-columns: 1fr;
  }

  .tab-bar,
  .bottom-actions {
    flex-direction: column;
  }
}

.replay-loading-spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-left: 6px;
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: replay-spin 0.6s linear infinite;
}

@keyframes replay-spin {
  to { transform: rotate(360deg); }
}
</style>
