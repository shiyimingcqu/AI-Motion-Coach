<template>
  <div class="ss-page">
    <section class="ss-hero-grid" aria-label="评估方式">
      <article class="ss-choice-card ss-choice-purple">
        <div class="ss-choice-copy">
          <h2>用手机拍摄新动作</h2>
          <p>打开小程序，实时识别并保存训练数据</p>

          <div class="ss-feature-row">
            <div v-for="feature in phoneFeatures" :key="feature.title" class="ss-feature">
              <span class="ss-feature-icon purple">
                <component :is="feature.icon" :size="26" :stroke-width="2.4" />
              </span>
              <strong>{{ feature.title }}</strong>
              <small>{{ feature.desc }}</small>
            </div>
          </div>

          <button class="ss-action ss-action-purple" type="button" @click="showPhoneQR = true">
            <ScanLine :size="20" />
            <span>打开小程序拍摄</span>
          </button>
        </div>
        <img class="ss-phone-visual" :src="phoneCameraImg" alt="" />
      </article>

      <article class="ss-choice-card ss-choice-green">
        <div class="ss-choice-copy">
          <h2>从训练记录中评估</h2>
          <p>选择已有训练，进行3D回放与纠错分析</p>

          <div class="ss-feature-row">
            <div v-for="feature in recordFeatures" :key="feature.title" class="ss-feature">
              <span class="ss-feature-icon green">
                <component :is="feature.icon" :size="26" :stroke-width="2.4" />
              </span>
              <strong>{{ feature.title }}</strong>
              <small>{{ feature.desc }}</small>
            </div>
          </div>

          <button class="ss-action ss-action-green" type="button" @click="goToSessions">
            <ArrowRight :size="20" />
            <span>选择训练记录</span>
          </button>
        </div>
        <img class="ss-tablet-visual" :src="tabletReplayImg" alt="" />
      </article>
    </section>

    <section class="ss-flow-section" aria-label="训练评估流程">
      <h2 class="ss-section-title">训练评估流程</h2>
      <div class="ss-flow">
        <article v-for="(step, index) in flowSteps" :key="step.title" class="ss-flow-card">
          <img :src="step.image" alt="" />
          <div>
            <strong>{{ index + 1 }}. {{ step.title }}</strong>
            <p>{{ step.desc }}</p>
          </div>
          <Check :size="15" />
          <span v-if="index < flowSteps.length - 1" class="ss-flow-arrow" aria-hidden="true">
            <ChevronRight :size="30" />
          </span>
        </article>
        <button class="ss-next" type="button" aria-label="查看更多训练记录">
          <ChevronRight :size="24" />
        </button>
      </div>
    </section>

    <section class="ss-qr-band">
      <div class="ss-qr-code" aria-hidden="true">
        <img v-if="qrDataUrl" :src="qrDataUrl" alt="小程序码" class="ss-qr-img" />
        <div v-else class="ss-qr-loading">
          <div class="ss-qr-spinner"></div>
        </div>
      </div>
      <div class="ss-qr-copy">
        <h2>在手机上开始评估</h2>
        <p>微信扫一扫，打开小程序开始你的姿态评估之旅</p>
        <small v-if="qrExpiry" class="ss-qr-expiry">有效期至 {{ qrExpiry }}</small>
      </div>
      <button class="ss-refresh" type="button" @click="refreshQrCode" :disabled="qrLoading">
        <RefreshCw :size="18" :class="{ 'ss-spin': qrLoading }" />
        <span>{{ qrLoading ? '生成中...' : '刷新二维码' }}</span>
      </button>
    </section>

    <TrainQRModal
      v-if="showPhoneQR"
      exercise-name="小程序"
      exercise-key="miniapp"
      camera-view="front"
      @close="showPhoneQR = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  BarChart3,
  Box,
  Check,
  ChevronRight,
  ClipboardList,
  CloudUpload,
  Lightbulb,
  MessageSquare,
  RefreshCw,
  ScanLine,
  Smartphone,
  Target,
} from "lucide-vue-next";
import QRCode from "qrcode";
import TrainQRModal from "@/components/TrainQRModal.vue";
import { useAuthStore } from "@/stores/auth";
import phoneCameraImg from "@/assets/start-phone-camera.png";
import tabletReplayImg from "@/assets/start-tablet-replay.png";
import stepPhoneImg from "@/assets/start-step-phone.png";
import stepRecordImg from "@/assets/start-step-record.png";
import stepCloudImg from "@/assets/start-step-cloud.png";
import stepLaptopImg from "@/assets/start-step-laptop.png";
import stepCoachImg from "@/assets/start-step-coach.png";

const router = useRouter();
const authStore = useAuthStore();
const showPhoneQR = ref(false);

// 动态二维码
const qrDataUrl = ref("");
const qrLoading = ref(false);
const qrExpiry = ref("");
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
let qrTimer: ReturnType<typeof setInterval> | null = null;

async function refreshQrCode() {
  qrLoading.value = true;
  try {
    const token = authStore.token || "";
    // 先尝试后端微信小程序码
    try {
      const resp = await fetch(
        `${API_BASE}/qrcode?exercise=squat&view=front&t=${Date.now()}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
      if (resp.ok) {
        const blob = await resp.blob();
        qrDataUrl.value = URL.createObjectURL(blob);
      } else {
        throw new Error("backend qrcode failed");
      }
    } catch {
      // 后端不可用时，前端生成动态二维码（编码当前页面 URL + 时间戳）
      const ts = Date.now();
      const targetUrl = `${window.location.origin}/start?t=${ts}`;
      qrDataUrl.value = await QRCode.toDataURL(targetUrl, {
        width: 200,
        margin: 1,
        color: { dark: "#111827", light: "#ffffff" },
      });
    }
    // 设置5分钟有效期
    const expiry = new Date(Date.now() + 5 * 60 * 1000);
    qrExpiry.value = `${expiry.getHours().toString().padStart(2, "0")}:${expiry.getMinutes().toString().padStart(2, "0")}`;
  } catch (e) {
    console.error("QR generation failed:", e);
  } finally {
    qrLoading.value = false;
  }
}

onMounted(() => {
  refreshQrCode();
  // 每5分钟自动刷新
  qrTimer = setInterval(refreshQrCode, 5 * 60 * 1000);
});

onUnmounted(() => {
  if (qrTimer) clearInterval(qrTimer);
});

const phoneFeatures = [
  { title: "实时识别", desc: "智能捕捉骨骼", icon: Smartphone },
  { title: "自动保存", desc: "数据上传云端", icon: CloudUpload },
  { title: "AI分析", desc: "生成评分与建议", icon: BarChart3 },
  { title: "即时反馈", desc: "给出纠正建议", icon: MessageSquare },
];

const recordFeatures = [
  { title: "3D回放", desc: "多角度查看动作", icon: Box },
  { title: "问题识别", desc: "精准定位错误", icon: Target },
  { title: "纠正建议", desc: "个性化改善方案", icon: Lightbulb },
  { title: "数据对比", desc: "历史成绩对比", icon: ClipboardList },
];

const flowSteps = [
  { title: "打开手机", desc: "在小程序中选择动作开始拍摄训练", image: stepPhoneImg },
  { title: "录制动作", desc: "保持全身在画面中完成动作录制", image: stepRecordImg },
  { title: "数据保存", desc: "训练数据自动保存到云端服务器", image: stepCloudImg },
  { title: "Web端评估", desc: "在本页进行3D回放查看评分与建议", image: stepLaptopImg },
  { title: "改善提升", desc: "根据建议调整动作持续进步", image: stepCoachImg },
];

function goToSessions() {
  router.push("/start/playback");
}
</script>

<style scoped>
.ss-page {
  height: 100%;
  min-height: 720px;
  display: grid;
  grid-template-rows: minmax(0, 52fr) minmax(0, 30fr) minmax(88px, 14fr);
  gap: clamp(18px, 2.1vh, 26px);
  padding-bottom: 0;
}

.ss-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.18fr);
  gap: clamp(18px, 1.4vw, 22px);
  min-height: 0;
}

.ss-choice-card {
  position: relative;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border: 1px solid rgba(217, 225, 237, 0.9);
  border-radius: 16px;
  padding: clamp(26px, 2.2vw, 34px) clamp(26px, 2vw, 32px) clamp(24px, 1.8vw, 30px);
  box-shadow: 0 14px 42px rgba(38, 48, 69, 0.06);
}

.ss-choice-purple {
  background: #fbf9ff;
}

.ss-choice-green {
  background: #f8fdfb;
}

.ss-choice-copy {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 0;
}

.ss-choice-copy h2 {
  margin: 0;
  font-size: clamp(27px, 1.75vw, 31px);
  font-weight: 900;
  line-height: 1.2;
}

.ss-choice-purple h2 {
  color: #6938ef;
}

.ss-choice-green h2 {
  color: #079455;
}

.ss-choice-copy p {
  margin: 16px 0 clamp(26px, 3vh, 34px);
  color: #344054;
  font-size: clamp(16px, 1vw, 18px);
  line-height: 1.55;
}

.ss-feature-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(70px, 1fr));
  gap: 14px;
  margin-bottom: clamp(26px, 3vh, 34px);
  max-width: 500px;
}

.ss-feature {
  display: grid;
  justify-items: center;
  gap: 7px;
  text-align: center;
}

.ss-feature-icon {
  width: 68px;
  height: 68px;
  display: grid;
  place-items: center;
  border-radius: 50%;
}

.ss-feature-icon.purple {
  color: #7c3aed;
  background: linear-gradient(180deg, #f2ecff, #fbfaff);
}

.ss-feature-icon.green {
  color: #079455;
  background: linear-gradient(180deg, #e8f8ef, #f7fffa);
}

.ss-feature strong {
  color: #111827;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.2;
}

.ss-feature small {
  color: #667085;
  font-size: 12px;
  line-height: 1.25;
}

.ss-action,
.ss-refresh,
.ss-next {
  border: 0;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.ss-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 246px;
  min-height: 56px;
  border-radius: 999px;
  color: #fff;
  font-size: 17px;
  font-weight: 800;
}

.ss-action:hover,
.ss-refresh:hover,
.ss-next:hover {
  transform: translateY(-1px);
  filter: brightness(1.02);
}

.ss-action-purple {
  background: linear-gradient(135deg, #7c3aed, #6d5dfc);
  box-shadow: 0 14px 24px rgba(124, 58, 237, 0.22);
}

.ss-action-green {
  background: linear-gradient(135deg, #16a34a, #079455);
  box-shadow: 0 14px 24px rgba(7, 148, 85, 0.2);
}

.ss-phone-visual {
  width: min(33%, 196px);
  min-width: 142px;
  object-fit: contain;
  filter: drop-shadow(0 16px 18px rgba(33, 28, 65, 0.12));
}

.ss-tablet-visual {
  width: min(44%, 350px);
  min-width: 230px;
  object-fit: contain;
  filter: drop-shadow(0 18px 22px rgba(17, 24, 39, 0.16));
}

.ss-section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 10px;
  color: #101828;
  font-size: 22px;
  font-weight: 900;
}

.ss-flow-section {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.ss-section-title::before {
  content: "";
  width: 4px;
  height: 25px;
  border-radius: 99px;
  background: #7c3aed;
}

.ss-flow {
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr)) 50px;
  gap: clamp(16px, 1.4vw, 22px);
  align-items: stretch;
  flex: 1;
  min-height: 0;
}

.ss-flow-card {
  position: relative;
  min-height: 0;
  height: 100%;
  display: grid;
  grid-template-columns: 98px minmax(0, 1fr);
  align-items: center;
  gap: 14px;
  padding: 18px 18px 16px;
  border: 1px solid rgba(217, 225, 237, 0.95);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(38, 48, 69, 0.06);
}

.ss-flow-card img {
  width: 98px;
  max-height: 110px;
  object-fit: contain;
}

.ss-flow-card strong {
  color: #111827;
  font-size: 15px;
  font-weight: 900;
  line-height: 1.35;
}

.ss-flow-card p {
  margin: 12px 0 0;
  color: #526070;
  font-size: 13px;
  line-height: 1.65;
}

.ss-flow-card > svg {
  position: absolute;
  left: 50%;
  bottom: 14px;
  width: 22px;
  height: 22px;
  padding: 3px;
  transform: translateX(-50%);
  border-radius: 50%;
  color: #fff;
  background: #7c3aed;
  box-shadow: 0 5px 12px rgba(124, 58, 237, 0.25);
}

.ss-flow-arrow {
  position: absolute;
  top: 50%;
  right: -27px;
  z-index: 2;
  display: grid;
  place-items: center;
  color: #d8cdfc;
  transform: translateY(-50%);
}

.ss-next {
  align-self: center;
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #344054;
  background: #fff;
  box-shadow: 0 10px 25px rgba(38, 48, 69, 0.08);
}

.ss-qr-band {
  display: flex;
  align-items: center;
  gap: 22px;
  min-height: 88px;
  height: 100%;
  padding: 14px 28px;
  border-radius: 14px;
  background: #fbf7ff;
}

.ss-qr-code {
  width: 84px;
  height: 84px;
  flex: 0 0 84px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ss-qr-img {
  display: block;
  width: 84px;
  height: 84px;
  border-radius: 10px;
  box-shadow: 0 8px 18px rgba(38, 48, 69, 0.08);
  object-fit: contain;
}

.ss-qr-loading {
  width: 84px;
  height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #f1f5f9;
}

.ss-qr-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #e2e8f0;
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.ss-spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ss-qr-expiry {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.ss-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ss-qr-copy {
  flex: 1;
  min-width: 0;
}

.ss-qr-copy h2 {
  margin: 0;
  color: #101828;
  font-size: 21px;
  font-weight: 900;
}

.ss-qr-copy p {
  margin: 8px 0 0;
  color: #526070;
  font-size: 14px;
}

.ss-refresh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-width: 154px;
  min-height: 50px;
  padding: 0 20px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, #7c3aed, #6d5dfc);
  box-shadow: 0 12px 22px rgba(124, 58, 237, 0.2);
  font-size: 15px;
  font-weight: 800;
}

@media (max-width: 1280px) {
  .ss-page {
    height: auto;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .ss-hero-grid,
  .ss-flow {
    grid-template-columns: 1fr;
  }

  .ss-choice-card {
    min-height: 280px;
    height: auto;
  }

  .ss-flow {
    gap: 14px;
  }

  .ss-flow-card {
    grid-template-columns: 100px minmax(0, 1fr);
    min-height: 150px;
    height: auto;
  }

  .ss-flow-arrow,
  .ss-next {
    display: none;
  }
}

@media (max-width: 760px) {
  .ss-choice-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 24px 20px;
  }

  .ss-feature-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ss-phone-visual,
  .ss-tablet-visual {
    align-self: center;
    width: min(78%, 260px);
  }

  .ss-flow-card {
    grid-template-columns: 86px minmax(0, 1fr);
    padding: 18px;
  }

  .ss-qr-band {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
