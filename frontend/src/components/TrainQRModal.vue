<template>
  <Teleport to="body">
    <div class="tqm-overlay" @click.self="emit('close')">
      <div class="tqm-card">
        <button class="tqm-close" type="button" @click="emit('close')">
          <X :size="20" />
        </button>

        <h2 class="tqm-title">手机扫码开始训练</h2>
        <p class="tqm-subtitle">使用微信扫描二维码，在小程序中开始 {{ exerciseName }} 评估</p>

        <div class="tqm-qr-wrap">
          <img v-if="qrImageUrl" :src="qrImageUrl" alt="小程序码" class="tqm-qr-img" />
          <div v-else class="tqm-loading">
            <div class="tqm-spinner"></div>
            <span>{{ loadingText }}</span>
          </div>
        </div>

        <div class="tqm-params">
          <div class="tqm-param">
            <span>动作</span>
            <strong>{{ exerciseName }}</strong>
          </div>
          <div class="tqm-param">
            <span>拍摄方向</span>
            <strong>{{ cameraLabel }}</strong>
          </div>
          <div class="tqm-param" v-if="version">
            <span>模板版本</span>
            <strong>{{ version }}</strong>
          </div>
        </div>

        <p class="tqm-hint">扫码后将在小程序中自动进入训练页面</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { X } from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const props = defineProps<{
  exerciseName: string;
  exerciseKey: string;
  cameraView?: string;
  version?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const qrImageUrl = ref("");
const loadingText = ref("生成二维码中...");

const cameraLabel = computed(() => {
  const m: Record<string, string> = { side: "侧面", front: "正面", "45deg": "45°" };
  return m[props.cameraView || ""] || "侧面";
});

async function loadQrCode() {
  try {
    const authStore = useAuthStore();
    const token = authStore.token || "";
    const url = `${API_BASE}/qrcode?exercise=${encodeURIComponent(props.exerciseKey)}&view=${encodeURIComponent(props.cameraView || "side")}`;
    const resp = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "生成二维码失败");
    }
    const blob = await resp.blob();
    qrImageUrl.value = URL.createObjectURL(blob);
  } catch (e: any) {
    loadingText.value = "生成失败，请重试";
  }
}

onMounted(loadQrCode);
</script>

<style scoped>
.tqm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: tqmFadeIn 0.2s ease;
}

@keyframes tqmFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tqm-card {
  background: #fff;
  border-radius: 20px;
  padding: 32px;
  max-width: 380px;
  width: 90vw;
  text-align: center;
  position: relative;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
  animation: tqmSlideUp 0.25s ease;
}

@keyframes tqmSlideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.tqm-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 0;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.tqm-close:hover {
  background: #e2e8f0;
  color: #334155;
}

.tqm-title {
  font-size: 20px;
  font-weight: 700;
  color: #101828;
  margin: 0 0 6px;
}

.tqm-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 24px;
  line-height: 1.5;
}

.tqm-qr-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  min-height: 200px;
}

.tqm-qr-img {
  width: 200px;
  height: 200px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 2px solid #e2e8f0;
  object-fit: contain;
}

.tqm-loading {
  width: 200px;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  color: #94a3b8;
  font-size: 14px;
}

.tqm-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tqm-params {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 12px;
  text-align: left;
}

.tqm-param {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.tqm-param span {
  color: #94a3b8;
}

.tqm-param strong {
  color: #101828;
}

.tqm-hint {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}
</style>
