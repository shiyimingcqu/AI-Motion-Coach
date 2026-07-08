<template>
  <Teleport to="body">
    <div class="tqm-overlay" @click.self="emit('close')">
      <div class="tqm-card">
        <button class="tqm-close" type="button" @click="emit('close')">
          <X :size="20" />
        </button>

        <h2 class="tqm-title">手机扫码开始训练</h2>
        <p class="tqm-subtitle">使用微信扫描二维码，在小程序中开始 {{ exerciseName }} 评估</p>

        <!-- 二维码 SVG -->
        <div class="tqm-qr-wrap">
          <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="tqm-qr">
            <!-- 外层边框 -->
            <rect x="0" y="0" width="200" height="200" rx="12" fill="#fff" />

            <!-- 模拟二维码图案 -->
            <g fill="#1e293b">
              <!-- 定位图案 (左上) -->
              <rect x="16" y="16" width="8" height="8" />
              <rect x="24" y="16" width="8" height="8" />
              <rect x="32" y="16" width="8" height="8" />
              <rect x="40" y="16" width="8" height="8" />
              <rect x="48" y="16" width="8" height="8" />
              <rect x="56" y="16" width="8" height="8" />
              <rect x="64" y="16" width="8" height="8" />
              <rect x="16" y="24" width="8" height="8" />
              <rect x="56" y="24" width="8" height="8" />
              <rect x="64" y="24" width="8" height="8" />
              <rect x="16" y="32" width="8" height="8" />
              <rect x="24" y="32" width="8" height="8" />
              <rect x="32" y="32" width="8" height="8" />
              <rect x="40" y="32" width="8" height="8" />
              <rect x="48" y="32" width="8" height="8" />
              <rect x="56" y="32" width="8" height="8" />
              <rect x="64" y="32" width="8" height="8" />
              <rect x="16" y="40" width="8" height="8" />
              <rect x="64" y="40" width="8" height="8" />
              <rect x="16" y="48" width="8" height="8" />
              <rect x="32" y="48" width="8" height="8" />
              <rect x="48" y="48" width="8" height="8" />
              <rect x="64" y="48" width="8" height="8" />
              <rect x="16" y="56" width="8" height="8" />
              <rect x="24" y="56" width="8" height="8" />
              <rect x="40" y="56" width="8" height="8" />
              <rect x="56" y="56" width="8" height="8" />
              <rect x="64" y="56" width="8" height="8" />

              <!-- 定位图案 (右上) -->
              <rect x="128" y="16" width="8" height="8" />
              <rect x="136" y="16" width="8" height="8" />
              <rect x="144" y="16" width="8" height="8" />
              <rect x="152" y="16" width="8" height="8" />
              <rect x="160" y="16" width="8" height="8" />
              <rect x="168" y="16" width="8" height="8" />
              <rect x="176" y="16" width="8" height="8" />
              <rect x="128" y="24" width="8" height="8" />
              <rect x="168" y="24" width="8" height="8" />
              <rect x="176" y="24" width="8" height="8" />
              <rect x="128" y="32" width="8" height="8" />
              <rect x="136" y="32" width="8" height="8" />
              <rect x="144" y="32" width="8" height="8" />
              <rect x="152" y="32" width="8" height="8" />
              <rect x="160" y="32" width="8" height="8" />
              <rect x="168" y="32" width="8" height="8" />
              <rect x="176" y="32" width="8" height="8" />
              <rect x="128" y="40" width="8" height="8" />
              <rect x="176" y="40" width="8" height="8" />
              <rect x="128" y="48" width="8" height="8" />
              <rect x="144" y="48" width="8" height="8" />
              <rect x="160" y="48" width="8" height="8" />
              <rect x="176" y="48" width="8" height="8" />
              <rect x="128" y="56" width="8" height="8" />
              <rect x="136" y="56" width="8" height="8" />
              <rect x="152" y="56" width="8" height="8" />
              <rect x="168" y="56" width="8" height="8" />
              <rect x="176" y="56" width="8" height="8" />

              <!-- 定位图案 (左下) -->
              <rect x="16" y="128" width="8" height="8" />
              <rect x="24" y="128" width="8" height="8" />
              <rect x="32" y="128" width="8" height="8" />
              <rect x="40" y="128" width="8" height="8" />
              <rect x="48" y="128" width="8" height="8" />
              <rect x="56" y="128" width="8" height="8" />
              <rect x="64" y="128" width="8" height="8" />
              <rect x="16" y="136" width="8" height="8" />
              <rect x="56" y="136" width="8" height="8" />
              <rect x="64" y="136" width="8" height="8" />
              <rect x="16" y="144" width="8" height="8" />
              <rect x="24" y="144" width="8" height="8" />
              <rect x="32" y="144" width="8" height="8" />
              <rect x="40" y="144" width="8" height="8" />
              <rect x="48" y="144" width="8" height="8" />
              <rect x="56" y="144" width="8" height="8" />
              <rect x="64" y="144" width="8" height="8" />
              <rect x="16" y="152" width="8" height="8" />
              <rect x="64" y="152" width="8" height="8" />
              <rect x="16" y="160" width="8" height="8" />
              <rect x="32" y="160" width="8" height="8" />
              <rect x="48" y="160" width="8" height="8" />
              <rect x="64" y="160" width="8" height="8" />
              <rect x="16" y="168" width="8" height="8" />
              <rect x="24" y="168" width="8" height="8" />
              <rect x="40" y="168" width="8" height="8" />
              <rect x="56" y="168" width="8" height="8" />
              <rect x="64" y="168" width="8" height="8" />

              <!-- 中间数据区 (模拟) -->
              <rect x="88" y="16" width="8" height="8" />
              <rect x="104" y="16" width="8" height="8" />
              <rect x="96" y="32" width="8" height="8" />
              <rect x="112" y="40" width="8" height="8" />
              <rect x="88" y="56" width="8" height="8" />
              <rect x="104" y="64" width="8" height="8" />
              <rect x="112" y="80" width="8" height="8" />
              <rect x="88" y="88" width="8" height="8" />
              <rect x="96" y="104" width="8" height="8" />
              <rect x="104" y="112" width="8" height="8" />
              <rect x="88" y="128" width="8" height="8" />
              <rect x="104" y="136" width="8" height="8" />
              <rect x="112" y="152" width="8" height="8" />

              <!-- 更多随机填充 -->
              <rect x="80" y="72" width="8" height="8" />
              <rect x="96" y="80" width="8" height="8" />
              <rect x="80" y="96" width="8" height="8" />
              <rect x="88" y="120" width="8" height="8" />
              <rect x="112" y="128" width="8" height="8" />
              <rect x="80" y="136" width="8" height="8" />
              <rect x="96" y="144" width="8" height="8" />
              <rect x="112" y="160" width="8" height="8" />

              <!-- 底部 -->
              <rect x="128" y="128" width="8" height="8" />
              <rect x="144" y="136" width="8" height="8" />
              <rect x="136" y="152" width="8" height="8" />
              <rect x="160" y="160" width="8" height="8" />
              <rect x="168" y="144" width="8" height="8" />
              <rect x="152" y="168" width="8" height="8" />
              <rect x="176" y="128" width="8" height="8" />
              <rect x="128" y="160" width="8" height="8" />
              <rect x="144" y="168" width="8" height="8" />
              <rect x="176" y="176" width="8" height="8" />
            </g>

            <!-- 中心 Logo -->
            <rect x="82" y="82" width="36" height="36" rx="8" fill="#fff" />
            <rect x="83" y="83" width="34" height="34" rx="7" fill="#8b5cf6" opacity="0.12" />
            <text x="100" y="105" text-anchor="middle" font-size="16">💪</text>
          </svg>
        </div>

        <!-- 参数信息 -->
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
import { computed } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps<{
  exerciseName: string;
  exerciseKey: string;
  cameraView?: string;
  version?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const cameraLabel = computed(() => {
  const m: Record<string, string> = { side: "侧面", front: "正面", "45deg": "45°" };
  return m[props.cameraView || ""] || "侧面";
});
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
  margin-bottom: 20px;
}

.tqm-qr {
  width: 200px;
  height: 200px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 2px solid #e2e8f0;
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
