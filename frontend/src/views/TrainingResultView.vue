<template>
  <div class="page training-result-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Training Result</p>
        <h1>训练结果</h1>
        <p class="subtle">{{ exerciseLabel }} 训练已完成</p>
      </div>
      <button class="secondary-button" type="button" @click="discardAndGoHome">
        放弃保存，返回首页
      </button>
    </header>

    <!-- 汇总卡片 -->
    <section class="result-summary">
      <div class="summary-card">
        <div class="summary-header">
          <h2>本次训练摘要</h2>
          <span class="session-badge">{{ exerciseLabel }}</span>
        </div>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="metric-label">训练时长</span>
            <strong class="metric-value">{{ formatDuration(durationSeconds) }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">总次数</span>
            <strong class="metric-value">{{ totalCount }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">有效次数</span>
            <strong class="metric-value accent-green">{{ validCount }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">错误次数</span>
            <strong class="metric-value accent-red">{{ errorCount }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">平均评分</span>
            <strong class="metric-value accent-blue">{{ formatScore(averageScore) }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">有效率</span>
            <strong class="metric-value">{{ validRate }}%</strong>
          </div>
        </div>
        <!-- 进度条可视化 -->
        <div class="progress-bar-wrap">
          <div class="progress-bar">
            <div class="progress-valid" :style="{ width: validRate + '%' }"></div>
            <div class="progress-error" :style="{ width: errorRate + '%' }"></div>
          </div>
          <small>{{ validCount }} 有效 / {{ errorCount }} 错误</small>
        </div>
      </div>

      <!-- 视频信息卡片 -->
      <div v-if="hasVideo" class="video-info-card">
        <h3>视频文件</h3>
        <p>{{ videoName }}</p>
        <small>保存后将上传至视频分析，生成带标注的分析视频。</small>
      </div>
      <div v-else class="video-info-card no-video">
        <h3>无视频文件</h3>
        <small>本次使用的是摄像头实时检测，仅保存训练统计数据。</small>
      </div>
    </section>

    <!-- 动作按钮 -->
    <section class="result-actions">
      <button
        class="primary-button save-button"
        type="button"
        :disabled="saving"
        @click="saveTraining"
      >
        <Save :size="18" />
        {{ saving ? '保存中...' : '保存本次训练' }}
      </button>
      <p v-if="saveError" class="form-error">{{ saveError }}</p>
    </section>

    <!-- 保存成功 -->
    <section v-if="saveSuccess" class="success-banner">
      <p>训练数据已成功保存！</p>
      <div class="success-links">
        <router-link to="/sessions" class="primary-button">查看训练记录</router-link>
        <router-link v-if="hasVideo" to="/upload" class="secondary-button">查看视频分析</router-link>
        <router-link to="/" class="secondary-button">返回首页</router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Save } from "lucide-vue-next";
import { apiUpload } from "../api/client";
import { createSession, type CreateSessionPayload } from "../api/sessions";
import { pendingVideoFile } from "../composables/usePendingVideo";

const route = useRoute();
const router = useRouter();

const saving = ref(false);
const saveError = ref("");
const saveSuccess = ref(false);

// 从路由 query 中读取训练数据
const sessionId = computed(() => (route.query.session_id as string) || "");
const exercise = computed(() => (route.query.exercise as string) || "squat");
const totalCount = computed(() => Number(route.query.total_count) || 0);
const validCount = computed(() => Number(route.query.valid_count) || 0);
const errorCount = computed(() => Number(route.query.error_count) || 0);
const averageScore = computed(() => Number(route.query.average_score) || 0);
const durationSeconds = computed(() => Number(route.query.duration_seconds) || 0);
const hasVideo = computed(() => route.query.has_video === "1");
const videoName = computed(() => (route.query.video_name as string) || "未知文件");

const exerciseMap: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  jumping_jack: "开合跳",
  plank: "平板支撑",
};
const exerciseLabel = computed(() => exerciseMap[exercise.value] ?? exercise.value);

const validRate = computed(() => {
  if (totalCount.value <= 0) return 0;
  return Math.round((validCount.value / totalCount.value) * 100);
});
const errorRate = computed(() => {
  if (totalCount.value <= 0) return 0;
  return Math.round((errorCount.value / totalCount.value) * 100);
});

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m > 0) return `${m} 分 ${s} 秒`;
  return `${s} 秒`;
}

function formatScore(score: number): string {
  if (typeof score !== "number" || !Number.isFinite(score)) return "--";
  return score.toFixed(1);
}

async function saveTraining() {
  saveError.value = "";
  saving.value = true;

  try {
    // 1. 确保训练会话已保存（如果 WebSocket 已保存则跳过，否则补存）
    if (!sessionId.value) {
      const payload: CreateSessionPayload = {
        exercise: exercise.value,
        duration_seconds: durationSeconds.value,
        total_count: totalCount.value,
        valid_count: validCount.value,
        error_count: errorCount.value,
        average_score: averageScore.value,
      };
      await createSession(payload);
    }

    // 2. 如果有视频文件，上传到视频分析
    if (hasVideo.value && pendingVideoFile.value) {
      const formData = new FormData();
      formData.append("exercise", exercise.value);
      formData.append("camera_view", "front");
      formData.append("file", pendingVideoFile.value);
      if (sessionId.value) {
        formData.append("session_id", sessionId.value);
      }
      await apiUpload("/videos/upload", formData);
    }

    // 清理暂存的视频文件
    pendingVideoFile.value = null;

    saveSuccess.value = true;
  } catch (e: any) {
    saveError.value = e?.message || "保存失败，请重试。";
  } finally {
    saving.value = false;
  }
}

function discardAndGoHome() {
  pendingVideoFile.value = null;
  router.push("/");
}

onMounted(() => {
  // 如果没有数据，跳回首页
  if (totalCount.value <= 0 && !sessionId.value) {
    router.replace("/");
  }
});
</script>

<style scoped>
.training-result-page {
  max-width: 880px;
  margin: 0 auto;
}

.result-summary {
  display: grid;
  gap: 20px;
  margin-bottom: 28px;
}

.summary-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.summary-header h2 {
  margin: 0;
  font-size: 18px;
  color: #16211b;
}

.session-badge {
  background: #eef2ff;
  color: #4f46e5;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
}

.metric-label {
  font-size: 12px;
  color: #5f6b63;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: #16211b;
}

.accent-green { color: #16a34a; }
.accent-red { color: #dc2626; }
.accent-blue { color: #2563eb; }

.progress-bar-wrap {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  background: #e2e8f0;
}

.progress-valid {
  background: #22c55e;
  transition: width 0.5s ease;
}

.progress-error {
  background: #ef4444;
  transition: width 0.5s ease;
}

.progress-bar-wrap small {
  color: #5f6b63;
  font-size: 12px;
}

.video-info-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  border-left: 4px solid #3b82f6;
}

.video-info-card h3 {
  margin: 0 0 4px;
  font-size: 15px;
  color: #16211b;
}

.video-info-card p {
  margin: 0;
  font-size: 14px;
  color: #3b82f6;
  font-weight: 500;
}

.video-info-card small {
  color: #5f6b63;
  font-size: 12px;
}

.video-info-card.no-video {
  border-left-color: #9ca3af;
}

.result-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}

.save-button {
  min-width: 200px;
  justify-content: center;
  gap: 8px;
  padding: 12px 28px;
  font-size: 15px;
}

.form-error {
  color: #ef4444;
  font-size: 13px;
  margin: 0;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 16px;
  padding: 24px 28px;
  text-align: center;
}

.success-banner p {
  margin: 0 0 16px;
  font-size: 16px;
  color: #166534;
  font-weight: 600;
}

.success-links {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.success-links a {
  text-decoration: none;
}
</style>
