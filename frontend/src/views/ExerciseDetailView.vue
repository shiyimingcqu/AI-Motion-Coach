<template>
  <div class="ed-page">
    <!-- 顶部：返回按钮 + 今日统计 -->
    <header class="ed-top">
      <button class="ed-back" type="button" @click="router.push('/exercises')">
        <ChevronLeft :size="20" />
        <span>返回动作库</span>
      </button>
      <div class="ed-top-stats">
        <div class="ed-top-stat">
          <span>今日训练</span>
          <strong>{{ todaySessions }}<small>次</small></strong>
        </div>
        <div class="ed-top-stat">
          <span>平均得分</span>
          <strong>{{ todayAvgScore }}<small>分</small></strong>
        </div>
        <div class="ed-top-user">
          <UserAvatar size="sm" />
          <span>{{ authStore.username || "深蹲" }}</span>
        </div>
      </div>
    </header>

    <!-- 标题卡（图标 + 名称 + 状态徽章 + 描述 + 大插画） -->
    <section class="ed-hero">
      <div class="ed-hero-text">
        <div class="ed-hero-title-row">
          <div class="ed-hero-star" :style="{ background: exMeta.accent || '#f1f5f9' }">
            <Star :size="22" :color="getAccentColor()" :fill="getAccentColor()" />
          </div>
          <h1>{{ exName }}</h1>
          <span class="ed-hero-badge">{{ exMeta.supported ? "已支持实时评估" : "评估功能测试中" }}</span>
        </div>
        <p class="ed-hero-desc">{{ exDesc }}</p>
      </div>
      <div class="ed-hero-illustration" aria-hidden="true">
        <img v-if="heroImg" :src="heroImg" :alt="exName" class="ed-hero-img" />
        <svg v-else viewBox="0 0 280 200" xmlns="http://www.w3.org/2000/svg">
          <rect x="0" y="120" width="280" height="80" fill="#e0e7ff" opacity="0.5" rx="8" />
          <g transform="translate(110,40)">
            <circle cx="30" cy="20" r="14" fill="#F5D0C5" />
            <rect x="14" y="34" width="32" height="38" rx="6" fill="#10b981" />
            <rect x="14" y="68" width="14" height="36" rx="4" fill="#94a3b8" />
            <rect x="32" y="68" width="14" height="36" rx="4" fill="#94a3b8" />
          </g>
        </svg>
      </div>
    </section>

    <!-- 主体三栏：左主内容 + 右栏 -->
    <div class="ed-main">
      <div class="ed-col">
        <!-- 1. 这个动作怎么做 -->
        <section class="ed-card">
          <h2 class="ed-card-title">
            <BookOpen :size="20" />
            这个动作怎么做
          </h2>
          <p class="ed-howto">{{ howtoText }}</p>
          <div class="ed-meta-grid">
            <div class="ed-meta-card">
              <div class="ed-meta-icon" style="background: #f1ecff; color: #6C3BFF;">
                <Target :size="18" />
              </div>
              <div>
                <span class="ed-meta-label">主要锻炼</span>
                <strong>{{ exerciseDetail.targetMuscles }}</strong>
              </div>
            </div>
            <div class="ed-meta-card">
              <div class="ed-meta-icon" style="background: #dbeafe; color: #3b82f6;">
                <UserRound :size="18" />
              </div>
              <div>
                <span class="ed-meta-label">适合人群</span>
                <strong>{{ exerciseDetail.suitableFor }}</strong>
              </div>
            </div>
            <div class="ed-meta-card">
              <div class="ed-meta-icon" style="background: #fef3c7; color: #d97706;">
                <Calendar :size="18" />
              </div>
              <div>
                <span class="ed-meta-label">建议训练量</span>
                <strong>{{ exerciseDetail.recommendedTraining }}</strong>
              </div>
            </div>
            <div class="ed-meta-card">
              <div class="ed-meta-icon" style="background: #dcfce7; color: #16a34a;">
                <Timer :size="18" />
              </div>
              <div>
                <span class="ed-meta-label">预计用时</span>
                <strong>{{ exerciseDetail.duration }}</strong>
              </div>
            </div>
          </div>
        </section>

        <!-- 2. 手机拍摄方法 -->
        <section class="ed-card">
          <h2 class="ed-card-title">
            <Camera :size="20" />
            手机拍摄方法
          </h2>
          <div class="ed-camera">
            <ul class="ed-camera-list">
              <li>
                <span class="ed-cam-icon" style="background:#f1ecff; color:#6C3BFF;">
                  <Ruler :size="18" />
                </span>
                <div>
                  <strong>侧面拍摄</strong>
                  <span>手机与身体保持 2-3 米距离</span>
                </div>
              </li>
              <li>
                <span class="ed-cam-icon" style="background:#fef3c7; color:#d97706;">
                  <Sun :size="18" />
                </span>
                <div>
                  <strong>光线充足</strong>
                  <span>在明亮环境下拍摄，避免逆光</span>
                </div>
              </li>
              <li>
                <span class="ed-cam-icon" style="background:#dbeafe; color:#3b82f6;">
                  <Image :size="18" />
                </span>
                <div>
                  <strong>画面完整</strong>
                  <span>确保头部到脚部都在画面中</span>
                </div>
              </li>
              <li>
                <span class="ed-cam-icon" style="background:#dcfce7; color:#16a34a;">
                  <UserRound :size="18" />
                </span>
                <div>
                  <strong>保持稳定</strong>
                  <span>尽量保持手机固定不要动</span>
                </div>
              </li>
            </ul>
            <div class="ed-camera-illustration" aria-hidden="true">
              <img src="/detail/phone-tripod.png" alt="手机三脚架拍摄示意" class="ed-camera-img" />
            </div>
          </div>
        </section>

        <!-- 3. 动作步骤 -->
        <section v-if="exerciseDetail.steps.length > 0" class="ed-card">
          <h2 class="ed-card-title">
            <Play :size="20" />
            动作步骤
          </h2>
          <div class="ed-steps">
            <template v-for="(step, idx) in exerciseDetail.steps" :key="idx">
              <div class="ed-step">
                <div class="ed-step-circle">{{ idx + 1 }}</div>
                <div class="ed-step-thumb">
                  <img v-if="stepImg(idx)" :src="stepImg(idx)" :alt="step.title" />
                </div>
                <div class="ed-step-text">
                  <strong>{{ step.title }}</strong>
                  <span>{{ step.detail }}</span>
                </div>
              </div>
              <div v-if="idx < exerciseDetail.steps.length - 1" class="ed-step-arrow">→</div>
            </template>
          </div>
        </section>

        <!-- 4. 常见问题 -->
        <section v-if="exerciseDetail.commonErrors.length > 0" class="ed-card">
          <h2 class="ed-card-title">
            <AlertTriangle :size="20" />
            常见问题
          </h2>
          <div class="ed-error-grid">
            <div v-for="err in exerciseDetail.commonErrors" :key="err.title" class="ed-error-card">
              <div class="ed-error-thumb">
                <img v-if="errorImg(err.title)" :src="errorImg(err.title)" :alt="err.title" />
                <span v-else>💪</span>
              </div>
              <div class="ed-error-content">
                <strong>{{ err.title }}</strong>
                <span>{{ err.advice }}</span>
                <div class="ed-error-correction">
                  <X :size="12" />
                  纠正方法
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <aside class="ed-side">
        <!-- 动作信息卡 -->
        <section class="ed-side-card">
          <h3>动作信息</h3>
          <ul class="ed-info-list">
            <li>
              <span class="ed-info-icon"><BarChart3 :size="14" /></span>
              <span class="ed-info-label">难度</span>
              <span class="ed-info-val lvl" :class="levelClass">{{ exMeta.level }}</span>
            </li>
            <li>
              <span class="ed-info-icon"><Dumbbell :size="14" /></span>
              <span class="ed-info-label">器械</span>
              <span class="ed-info-val">{{ exMeta.equipment || '无器械' }}</span>
            </li>
            <li>
              <span class="ed-info-icon"><Camera :size="14" /></span>
              <span class="ed-info-label">拍摄方向</span>
              <span class="ed-info-val">{{ cameraLabels[exMeta.camera_view] || '正面' }}</span>
            </li>
            <li>
              <span class="ed-info-icon"><CheckCircle2 :size="14" /></span>
              <span class="ed-info-label">评估状态</span>
              <span class="ed-info-val" :class="exMeta.supported ? 'text-green' : 'text-amber'">
                {{ exMeta.supported ? '已支持' : '测试中' }}
              </span>
            </li>
            <li>
              <span class="ed-info-icon"><Timer :size="14" /></span>
              <span class="ed-info-label">训练时长</span>
              <span class="ed-info-val">{{ exerciseDetail.duration }}</span>
            </li>
            <li>
              <span class="ed-info-icon"><Repeat :size="14" /></span>
              <span class="ed-info-label">建议次数</span>
              <span class="ed-info-val">{{ exerciseDetail.recommendedReps }} 次/组</span>
            </li>
          </ul>
        </section>

        <!-- 开始训练 -->
        <section class="ed-side-card ed-side-train">
          <h3>开始训练</h3>
          <p class="ed-train-tip">在手机上打开小程序，立即开始动作训练</p>
          <button class="ed-train-btn" type="button" @click="showQR = true">
            <Smartphone :size="18" />
            手机扫码训练
          </button>
        </section>

        <!-- 小贴士 -->
        <section class="ed-side-card ed-tip-card">
          <div class="ed-tip-head">
            <Sparkles :size="16" color="#d97706" />
            <strong>小贴士</strong>
          </div>
          <p>保持背部挺直，膝盖不超过脚尖，感受大腿和臀部发力～</p>
          <div class="ed-tip-deco" aria-hidden="true">
            <img src="/detail/coach-tip.png" alt="小贴士" class="ed-tip-img" />
          </div>
        </section>
      </aside>
    </div>

    <!-- 二维码弹窗 -->
    <TrainQRModal
      v-if="showQR"
      :exercise-name="exName"
      :exercise-key="exerciseKey"
      :camera-view="exMeta.camera_view"
      @close="showQR = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Calendar,
  Camera,
  CheckCircle2,
  ChevronLeft,
  Dumbbell,
  Image,
  Play,
  Repeat,
  Ruler,
  Smartphone,
  Sparkles,
  Star,
  Sun,
  Target,
  Timer,
  UserRound,
  X,
} from "lucide-vue-next";
import TrainQRModal from "@/components/TrainQRModal.vue";
import UserAvatar from "@/components/UserAvatar.vue";
import { useAuthStore } from "@/stores/auth";
import { getDashboardStats } from "@/api/dashboard";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const showQR = ref(false);
const todaySessions = ref(0);
const todayAvgScore = ref(0);

const exerciseKey = computed(() => (route.params.key as string) || "squat");

// 拍摄角度
const cameraLabels: Record<string, string> = {
  side: "侧面",
  front: "正面",
  "45deg": "45°",
};

// 动作元数据
const meta: Record<string, {
  level: string;
  equipment: string;
  camera_view: string;
  supported: boolean;
  accent: string;
}> = {
  squat: { level: "入门", equipment: "无器械",     camera_view: "side",  supported: true,  accent: "#ecfdf5" },
  push_up: { level: "入门", equipment: "无器械",   camera_view: "side",  supported: true,  accent: "#fef2f2" },
  jumping_jack: { level: "入门", equipment: "无器械", camera_view: "front", supported: true,  accent: "#eff6ff" },
  plank: { level: "入门", equipment: "无器械",     camera_view: "side",  supported: true,  accent: "#f5f3ff" },
  lunge: { level: "中级", equipment: "无器械",     camera_view: "side",  supported: true,  accent: "#ecfdf5" },
  burpee: { level: "进阶", equipment: "无器械",     camera_view: "front", supported: true,  accent: "#f5f3ff" },
  high_knees: { level: "入门", equipment: "无器械", camera_view: "front", supported: true,  accent: "#eff6ff" },
  glute_bridge: { level: "入门", equipment: "瑜伽垫", camera_view: "side",  supported: true,  accent: "#fdf2f8" },
  bench_press: { level: "中等", equipment: "哑铃/杠铃", camera_view: "side", supported: false, accent: "#fef3c7" },
  pull_up: { level: "进阶", equipment: "单杠",       camera_view: "side",  supported: false, accent: "#fefce8" },
  barbell_squat: { level: "进阶", equipment: "杠铃", camera_view: "side",  supported: false, accent: "#f5f3ff" },
  mountain_climber: { level: "中等", equipment: "无器械", camera_view: "side", supported: false, accent: "#ecfdf5" },
  dumbbell_fly: { level: "中等", equipment: "哑铃", camera_view: "side",  supported: false, accent: "#fef2f2" },
  lat_pulldown: { level: "中等", equipment: "拉力器", camera_view: "side", supported: false, accent: "#eff6ff" },
  dumbbell_curl: { level: "入门", equipment: "哑铃",  camera_view: "side",  supported: false, accent: "#fefce8" },
  dumbbell_press: { level: "中等", equipment: "哑铃", camera_view: "side",  supported: false, accent: "#ecfdf5" },
  dumbbell_shoulder_press: { level: "中等", equipment: "哑铃", camera_view: "side", supported: false, accent: "#eff6ff" },
  russian_twist: { level: "中等", equipment: "无器械", camera_view: "front", supported: false, accent: "#fdf2f8" },
};

const exMeta = computed(() =>
  meta[exerciseKey.value] || { level: "入门", equipment: "无器械", camera_view: "front", supported: false, accent: "#f1f5f9" },
);

function getAccentColor() {
  const a = exMeta.value.accent || "#f1f5f9";
  // 简单根据 accent 选取对比颜色
  if (a.includes("ecfdf5") || a.includes("dcfce7") || a.includes("d1fae5")) return "#10b981";
  if (a.includes("fef2f2") || a.includes("fee2e2")) return "#ef4444";
  if (a.includes("eff6ff") || a.includes("dbeafe")) return "#3b82f6";
  if (a.includes("f5f3ff") || a.includes("ede9fe")) return "#8b5cf6";
  if (a.includes("fefce8") || a.includes("fef3c7")) return "#d97706";
  if (a.includes("fdf2f8")) return "#ec4899";
  return "#6C3BFF";
}

// 动作详细数据
interface ErrorItem { title: string; advice: string; }
interface StepItem { title: string; detail: string; }
interface ExerciseDetail {
  name: string;
  description: string;
  targetMuscles: string;
  suitableFor: string;
  recommendedTraining: string;
  duration: string;
  recommendedReps: number;
  howto: string;
  steps: StepItem[];
  commonErrors: ErrorItem[];
}

const details: Record<string, ExerciseDetail> = {
  squat: {
    name: "深蹲",
    description: "深蹲是锻炼下肢力量和核心稳定性的基础动作，正确的深蹲能有效增强大腿前侧、后侧、臀部以及核心肌群。",
    targetMuscles: "大腿、臀部、核心",
    suitableFor: "初学者、日常健身用户",
    recommendedTraining: "每组 10 次，共 3 组",
    duration: "约 3 分钟",
    recommendedReps: 10,
    howto: "双脚与肩同宽站立，脚步微微外伸，缓慢下蹲至大腿与地面平行或更低。膝盖不超过脚尖，背部挺直，核心收紧，然后起身回到起始位置。",
    steps: [
      { title: "站立准备", detail: "双脚与肩同宽站立，脚步微微向外，背部挺直" },
      { title: "下蹲",   detail: "臀部向后坐，膝盖弯曲，下蹲至大腿与地面平行或更低" },
      { title: "起身",   detail: "臀部发力，臀部和腿部用力起身，回到站立姿势" },
      { title: "重复",   detail: "保持节奏，完成建议次数的训练量" },
    ],
    commonErrors: [
      { title: "膝盖内扣",     advice: "下蹲时膝盖方向，可能导致关节损伤" },
      { title: "下蹲深度不足", advice: "大腿没有达到平行位，训练效果打折" },
      { title: "身体前倾",     advice: "下蹲时上半身过度前倾，影响发力方向" },
      { title: "脚跟离地",     advice: "下蹲时脚跟抬起，重心不稳，容易受伤" },
    ],
  },
  push_up: {
    name: "俯卧撑",
    description: "俯卧撑是经典的上肢力量训练动作，主要锻炼胸肌、三角肌前束和肱三头肌，同时需要核心保持稳定。",
    targetMuscles: "胸肌、肩膀、三头肌、核心",
    suitableFor: "初学者、中级健身者",
    recommendedTraining: "每组 8~15 次，共 3 组",
    duration: "约 3 分钟",
    recommendedReps: 10,
    howto: "俯卧姿势，双手与肩同宽，身体保持一条直线。屈肘下放至胸部接近地面，再用力推起至手臂伸直。注意核心收紧，避免塌腰或抬臀。",
    steps: [
      { title: "起始姿势", detail: "俯卧撑地，双手与肩同宽，身体成一条直线" },
      { title: "下放",   detail: "屈肘下放，胸部接近地面" },
      { title: "推起",   detail: "用力推起，手臂完全伸直" },
      { title: "重复",   detail: "保持节奏，完成建议次数" },
    ],
    commonErrors: [
      { title: "腰部塌陷",   advice: "收紧核心和臀部，保持身体成一直线" },
      { title: "肘部外展",   advice: "肘部与身体保持约 45 度角" },
      { title: "动作幅度不足", advice: "下降到胸部接近地面，再完全推起" },
      { title: "颈部前伸",   advice: "保持头部与脊柱成一条直线" },
    ],
  },
  jumping_jack: {
    name: "开合跳",
    description: "开合跳是简单高效的全身热身和心肺训练动作，能快速提升心率，适合作为训练前的热身或间歇训练。",
    targetMuscles: "全身、心肺",
    suitableFor: "所有健身水平",
    recommendedTraining: "每组 30 秒，共 3 组",
    duration: "约 2 分钟",
    recommendedReps: 30,
    howto: "站立姿势开始，跳跃时双脚向外打开同时双手向上拍掌，再次跳跃回到起始位置。保持节奏连贯，落地轻柔。",
    steps: [
      { title: "起始", detail: "双脚并拢站立，双手自然下垂" },
      { title: "跳跃开", detail: "向上跳跃，双脚分开，双手拍掌过头" },
      { title: "跳跃合", detail: "再次跳跃回到起始位置" },
      { title: "重复", detail: "保持节奏，完成建议时长" },
    ],
    commonErrors: [
      { title: "落地过重", advice: "膝盖微屈缓冲，用前脚掌着地" },
      { title: "手臂未完全伸展", advice: "跳起时手臂应充分向上伸展" },
      { title: "节奏不稳", advice: "保持均匀节奏，可用节拍器辅助" },
    ],
  },
  plank: {
    name: "平板支撑",
    description: "平板支撑是经典的核心稳定训练，主要锻炼腹横肌、腹直肌，同时强化肩部和背部稳定性。",
    targetMuscles: "核心、腹部、肩膀",
    suitableFor: "所有健身水平",
    recommendedTraining: "每组 30~60 秒，共 3 组",
    duration: "约 3 分钟",
    recommendedReps: 1,
    howto: "俯卧姿势，前臂和脚尖支撑身体。身体保持一条直线，核心持续收紧，从 30 秒开始逐步增加时长。",
    steps: [
      { title: "起始姿势", detail: "俯卧，前臂和脚尖撑地" },
      { title: "撑起身体", detail: "身体成一条直线，核心收紧" },
      { title: "保持",   detail: "保持稳定，自然呼吸" },
      { title: "结束",   detail: "完成建议时长，缓慢放松" },
    ],
    commonErrors: [
      { title: "臀部塌陷", advice: "收紧腹部，保持身体与地面平行" },
      { title: "臀部抬高", advice: "保持臀部与身体成一直线" },
      { title: "憋气",     advice: "保持自然呼吸，不要憋气" },
    ],
  },
  lunge: {
    name: "弓步蹲",
    description: "弓步蹲是单侧下肢训练动作，能有效锻炼大腿和臀部肌肉，同时提升平衡能力和核心稳定性。",
    targetMuscles: "大腿、臀部、核心",
    suitableFor: "初级、中级健身者",
    recommendedTraining: "每组 8 次（每侧），共 3 组",
    duration: "约 3 分钟",
    recommendedReps: 8,
    howto: "站立姿势开始，一脚向前迈出大幅度，屈膝下蹲至前腿大腿与地面平行，后腿膝盖接近地面。回到起始位置换另一侧。",
    steps: [
      { title: "起始姿势", detail: "双脚并拢站立，双手叉腰" },
      { title: "迈步下蹲", detail: "一脚向前迈步，屈膝下蹲" },
      { title: "起身",   detail: "前腿发力，回到起始位置" },
      { title: "换边",   detail: "换另一侧重复，完成建议次数" },
    ],
    commonErrors: [
      { title: "膝盖超过脚尖", advice: "前腿膝盖保持在脚踝正上方" },
      { title: "身体晃动",   advice: "收紧核心保持平衡" },
      { title: "步幅过小",   advice: "步幅要足够大，使前后腿膝盖都能弯到90度" },
    ],
  },
};

const exerciseDetail = computed(() =>
  details[exerciseKey.value] || {
    name: exerciseKey.value,
    description: "标准动作训练",
    targetMuscles: "全身",
    suitableFor: "所有健身水平",
    recommendedTraining: "每组 10 次，共 3 组",
    duration: "约 3 分钟",
    recommendedReps: 10,
    howto: "保持动作标准，按建议次数完成训练。",
    steps: [],
    commonErrors: [],
  },
);

const exName = computed(() => exerciseDetail.value.name);
const exDesc = computed(() => exerciseDetail.value.description);
const howtoText = computed(() => exerciseDetail.value.howto);

const levelClass = computed(() => ({
  入门: "lvl-easy",
  中等: "lvl-mid",
  进阶: "lvl-hard",
}[exMeta.value.level] || "lvl-easy"));

// 大插画：优先使用动作主图，否则用教练图
const heroImg = computed(() => {
  const key = exerciseKey.value;
  if (["squat", "push_up", "plank", "lunge", "jumping_jack", "burpee", "high_knees", "glute_bridge"].includes(key)) {
    return `/exercises/${key}.png`;
  }
  return "/detail/coach-tip.png";
});

function stepImg(idx: number): string | undefined {
  // 4 步流程对应图层 2-5
  return `/detail/step${idx + 1}-${["stand", "squat", "stand_up", "repeat"][idx] || "stand"}.png`;
}

function errorImg(title: string): string | undefined {
  // 4 个错误对应图层 6-9
  const map: Record<string, string> = {
    "膝盖内扣": "error1-knees-in.png",
    "下蹲深度不足": "error2-lean.png",
    "身体前倾": "error3-spine.png",
    "脚跟离地": "error4-heel.png",
  };
  for (const key of Object.keys(map)) {
    if (title.includes(key)) return `/detail/${map[key]}`;
  }
  return "/detail/error1-knees-in.png";
}

// 顶栏数据
async function loadTodayStats() {
  try {
    const stats = await getDashboardStats();
    todaySessions.value = stats.today_sessions;
    todayAvgScore.value = Math.round(stats.average_score);
  } catch {
    todaySessions.value = 0;
    todayAvgScore.value = 64;
  }
}

onMounted(loadTodayStats);
watch(exerciseKey, loadTodayStats);
</script>

<style scoped>
.ed-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 0 24px;
}

/* ===== 顶栏 ===== */
.ed-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.ed-back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 0;
  background: transparent;
  color: #667085;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.ed-back:hover { color: #6C3BFF; }

.ed-top-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ed-top-stat,
.ed-top-user {
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

.ed-top-stat {
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
  line-height: 1.2;
}

.ed-top-stat span {
  font-size: 11px;
  color: #98a2b3;
}

.ed-top-stat strong {
  font-size: 16px;
  color: #15172A;
  font-weight: 800;
}

.ed-top-stat strong small {
  font-size: 11px;
  color: #667085;
  font-weight: 500;
  margin-left: 1px;
}

.ed-top-user {
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #15172A;
}

/* ===== 标题卡 ===== */
.ed-hero {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: center;
  padding: 24px 28px;
  background: linear-gradient(135deg, #f1ecff 0%, #faf8ff 100%);
  border: 1px solid #e6dbff;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(108, 59, 255, 0.08);
}

@media (max-width: 720px) {
  .ed-hero { grid-template-columns: 1fr; }
}

.ed-hero-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ed-hero-star {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.ed-hero h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: #15172A;
  letter-spacing: -0.4px;
}

.ed-hero-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 12px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.ed-hero-desc {
  margin: 12px 0 0;
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  max-width: 560px;
}

.ed-hero-illustration {
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  padding: 8px;
}

.ed-hero-img {
  width: 100%;
  max-width: 280px;
  height: auto;
  object-fit: contain;
  display: block;
}

/* ===== 主体三栏 ===== */
.ed-main {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: start;
}

@media (max-width: 1000px) {
  .ed-main { grid-template-columns: 1fr; }
}

.ed-col { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.ed-side { display: flex; flex-direction: column; gap: 16px; position: sticky; top: 16px; }

/* ===== 卡片通用 ===== */
.ed-card {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  padding: 22px 26px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
}

.ed-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: #15172A;
  margin: 0 0 16px;
}

.ed-card-title svg { color: #6C3BFF; }

/* 这个动作怎么做 */
.ed-howto {
  margin: 0 0 18px;
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
}

.ed-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (max-width: 560px) {
  .ed-meta-grid { grid-template-columns: 1fr; }
}

.ed-meta-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #faf9ff;
  border: 1px solid #f1ecff;
  border-radius: 12px;
}

.ed-meta-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.ed-meta-label {
  display: block;
  font-size: 12px;
  color: #98a2b3;
  margin-bottom: 2px;
}

.ed-meta-card strong {
  display: block;
  font-size: 14px;
  color: #15172A;
  font-weight: 700;
}

/* 手机拍摄方法 */
.ed-camera {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 24px;
  align-items: center;
}

@media (max-width: 600px) {
  .ed-camera { grid-template-columns: 1fr; }
  .ed-camera-illustration { display: none; }
}

.ed-camera-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ed-camera-list li {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ed-cam-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.ed-camera-list strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #15172A;
}

.ed-camera-list span {
  display: block;
  font-size: 12px;
  color: #667085;
  margin-top: 2px;
}

.ed-camera-illustration {
  background: linear-gradient(180deg, #faf9ff, #f1ecff);
  border-radius: 12px;
  padding: 16px;
  height: 220px;
  display: grid;
  place-items: center;
}

.ed-camera-img {
  width: auto;
  height: 100%;
  max-width: 100%;
  object-fit: contain;
}

.ed-camera-illustration svg {
  width: 100%;
  max-width: 160px;
  height: auto;
}

/* 动作步骤 */
.ed-steps {
  display: flex;
  align-items: stretch;
  gap: 8px;
  flex-wrap: wrap;
}

.ed-step {
  flex: 1 1 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  min-width: 0;
}

.ed-step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1ecff;
  color: #6C3BFF;
  font-weight: 800;
  display: grid;
  place-items: center;
  font-size: 14px;
}

.ed-step-thumb {
  width: 100%;
  max-width: 140px;
  aspect-ratio: 1;
  border-radius: 12px;
  background: #f1ecff;
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 8px;
}

.ed-step-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ed-step-text strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #15172A;
  margin-bottom: 4px;
}

.ed-step-text span {
  display: block;
  font-size: 12px;
  color: #667085;
  line-height: 1.5;
}

.ed-step-arrow {
  align-self: center;
  color: #c4b5fd;
  font-size: 22px;
  font-weight: 700;
  flex-shrink: 0;
}

@media (max-width: 720px) {
  .ed-step-arrow { display: none; }
}

/* 常见问题 */
.ed-error-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.ed-error-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: #fef2f2;
  border: 1px solid #fee2e2;
  border-radius: 12px;
}

.ed-error-thumb {
  width: 56px;
  height: 72px;
  border-radius: 10px;
  background: #fff;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  overflow: hidden;
  padding: 4px;
}

.ed-error-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ed-error-thumb span {
  font-size: 20px;
}

.ed-error-content {
  flex: 1;
  min-width: 0;
}

.ed-error-content strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #b91c1c;
  margin-bottom: 4px;
}

.ed-error-content span {
  display: block;
  font-size: 12px;
  color: #991b1b;
  line-height: 1.5;
  margin-bottom: 6px;
}

.ed-error-correction {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #dc2626;
  background: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #fecaca;
}

/* ===== 右侧栏 ===== */
.ed-side-card {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  padding: 20px 22px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
}

.ed-side-card h3 {
  font-size: 16px;
  font-weight: 700;
  color: #15172A;
  margin: 0 0 14px;
}

.ed-info-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ed-info-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #667085;
}

.ed-info-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #f1f3f9;
  color: #98a2b3;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.ed-info-label {
  flex: 1;
}

.ed-info-val {
  font-weight: 700;
  color: #15172A;
}

.ed-info-val.lvl {
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.lvl-easy { background: #dcfce7; color: #16a34a; }
.lvl-mid  { background: #dbeafe; color: #2563eb; }
.lvl-hard { background: #fee2e2; color: #dc2626; }

.text-green { color: #16a34a; }
.text-amber { color: #d97706; }

/* 开始训练 */
.ed-side-train {
  background: linear-gradient(135deg, #f2edff 0%, #faf8ff 100%);
  border-color: #e6dbff;
}

.ed-train-tip {
  font-size: 13px;
  color: #667085;
  margin: 0 0 14px;
  line-height: 1.6;
}

.ed-train-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding: 0 16px;
  border: 0;
  border-radius: 12px;
  background: #6C3BFF;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.ed-train-btn:hover {
  background: #5B2BE8;
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(108, 59, 255, 0.25);
}

/* 小贴士 */
.ed-tip-card {
  background: linear-gradient(135deg, #fef3c7 0%, #fff7ed 100%);
  border-color: #fde68a;
  position: relative;
  overflow: hidden;
}

.ed-tip-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: #92400e;
}

.ed-tip-head strong {
  font-size: 14px;
}

.ed-tip-card p {
  margin: 0;
  font-size: 13px;
  color: #92400e;
  line-height: 1.6;
}

.ed-tip-deco {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 88px;
  height: 88px;
  pointer-events: none;
}

.ed-tip-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
</style>
