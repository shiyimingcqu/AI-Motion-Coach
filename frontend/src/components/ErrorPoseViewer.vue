<template>
  <div class="error-pose-viewer" :class="variant">
    <div v-if="variant === 'highlight'" class="highlight-badge">✨ 高光时刻</div>
    <canvas
      ref="canvasRef"
      class="pose-canvas"
      @click="handleCanvasClick"
    />
    <div v-if="!frame?.landmarks?.length" class="pose-placeholder">
      <p>{{ frame?.blank_reason || (variant === 'highlight' ? '暂无高光截图' : '暂无姿态截图') }}</p>
      <small v-if="frame && !frame.blank_reason">完成实时检测或视频分析后，系统将自动截取低分/error 画面</small>
    </div>

    <div v-if="frame?.landmarks?.length" class="heatmap-legend">
      <span v-if="variant === 'highlight'" class="legend-item success"><i />优秀部位</span>
      <span v-else class="legend-item error"><i />待改进部位</span>
      <span class="legend-item normal"><i />正常部位</span>
    </div>

    <div v-if="selectedPart" class="part-eval-popup" :style="popupStyle">
      <button class="close-popup" type="button" @click="selectedPart = null">×</button>
      <strong>{{ selectedPart.label }}</strong>
      <p>{{ selectedPart.evaluation }}</p>
    </div>

    <div v-if="frame" class="frame-meta">
      <span class="score-badge" :class="scoreClass">{{ frame.score }} 分</span>
      <span>{{ frame.exercise_name }} · {{ frame.captured_at || frame.date }}</span>
      <span v-if="variant === 'highlight' && frame.praise" class="praise-hint">{{ frame.praise }}</span>
      <span v-else-if="frame.errors.length" class="error-hint">{{ frame.errors[0] }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { ErrorFrameItem } from "@/api/reports";
import {
  drawPoseWithErrorHighlights,
  type PoseHighlightPart,
} from "@/services/poseLandmarker";

const props = withDefaults(defineProps<{
  frame: ErrorFrameItem | null;
  variant?: "error" | "highlight";
}>(), {
  variant: "error",
});

const canvasRef = ref<HTMLCanvasElement | null>(null);
const selectedPart = ref<{ label: string; evaluation: string } | null>(null);
const popupStyle = ref<Record<string, string>>({});
let mappedPoints: Array<{ x: number; y: number }> = [];
let resizeObserver: ResizeObserver | null = null;

const scoreClass = computed(() => {
  const score = props.frame?.score ?? 100;
  if (props.variant === "highlight") return "score-highlight";
  if (score < 60) return "score-bad";
  if (score < 80) return "score-warn";
  return "score-ok";
});

function clearPoseCanvas() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function renderPose() {
  nextTick(() => {
    requestAnimationFrame(() => {
      clearPoseCanvas();
      const canvas = canvasRef.value;
      if (!canvas || !props.frame?.landmarks?.length) {
        mappedPoints = [];
        selectedPart.value = null;
        return;
      }

      const highlights: PoseHighlightPart[] = (props.frame.body_parts || []).map((part) => ({
        landmark_indices: part.landmark_indices,
        severity: part.severity,
      }));

      const result = drawPoseWithErrorHighlights(canvas, props.frame.landmarks, highlights);
      mappedPoints = result || [];
      selectedPart.value = null;
    });
  });
}

function handleCanvasClick(event: MouseEvent) {
  const canvas = canvasRef.value;
  if (!canvas || !props.frame?.body_parts?.length) return;

  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const cx = x * scaleX;
  const cy = y * scaleY;

  let bestPart: (typeof props.frame.body_parts)[number] | null = null;
  let bestDist = 28;

  for (const part of props.frame.body_parts) {
    for (const index of part.landmark_indices) {
      const point = mappedPoints[index];
      if (!point) continue;
      const dist = Math.hypot(point.x - cx, point.y - cy);
      if (dist < bestDist) {
        bestDist = dist;
        bestPart = part;
      }
    }
  }

  if (bestPart) {
    selectedPart.value = { label: bestPart.label, evaluation: bestPart.evaluation };
    popupStyle.value = {
      left: `${Math.min(x + 12, rect.width - 220)}px`,
      top: `${Math.min(y + 12, rect.height - 120)}px`,
    };
  }
}

function handleResize() {
  renderPose();
}

watch(() => props.frame, () => renderPose(), { deep: true });

onMounted(() => {
  renderPose();
  if (canvasRef.value?.parentElement) {
    resizeObserver = new ResizeObserver(() => renderPose());
    resizeObserver.observe(canvasRef.value.parentElement);
  }
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped>
.error-pose-viewer {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: #0b1220;
  border: 1px solid rgba(239, 68, 68, 0.2);
  min-height: 420px;
}
.pose-canvas {
  width: 100%;
  height: 420px;
  display: block;
  cursor: crosshair;
}
.pose-placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  color: #94a3b8;
  padding: 24px;
  pointer-events: none;
}
.pose-placeholder p { margin: 0 0 6px; color: #e2e8f0; font-weight: 600; }
.pose-placeholder small { color: #64748b; }
.frame-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 12px 16px;
  background: rgba(8, 13, 26, 0.85);
  border-top: 1px solid rgba(59, 130, 246, 0.1);
  font-size: 12px;
  color: #94a3b8;
}
.score-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 700;
  color: #fff;
}
.score-bad { background: #dc2626; }
.score-warn { background: #d97706; }
.score-ok { background: #2563eb; }
.score-highlight { background: linear-gradient(135deg, #34d399, #10b981); color: #052e16; }
.error-hint { color: #f87171; }
.praise-hint { color: #fde047; font-weight: 600; }
.error-pose-viewer.highlight {
  border-color: rgba(52, 211, 153, 0.35);
  box-shadow: 0 0 24px rgba(52, 211, 153, 0.12);
}
.highlight-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 4;
  padding: 6px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(52, 211, 153, 0.95), rgba(16, 185, 129, 0.9));
  color: #052e16;
  font-size: 12px;
  font-weight: 700;
  pointer-events: none;
}
.heatmap-legend {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 4;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  pointer-events: none;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(8, 13, 26, 0.75);
  font-size: 11px;
  color: #cbd5e1;
}
.legend-item i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
}
.legend-item.error i { background: #f97316; box-shadow: 0 0 8px rgba(249,115,22,0.6); }
.legend-item.success i { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,0.6); }
.legend-item.normal i { background: #64748b; }
.error-pose-viewer.highlight .part-eval-popup {
  border-color: rgba(250, 204, 21, 0.45);
}
.error-pose-viewer.highlight .part-eval-popup strong {
  color: #fde047;
}
.part-eval-popup {
  position: absolute;
  z-index: 5;
  max-width: 240px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.96);
  border: 1px solid rgba(239, 68, 68, 0.35);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}
.part-eval-popup strong {
  display: block;
  color: #fecaca;
  margin-bottom: 6px;
  font-size: 13px;
}
.part-eval-popup p {
  margin: 0;
  color: #cbd5e1;
  font-size: 12px;
  line-height: 1.5;
}
.close-popup {
  position: absolute;
  top: 4px;
  right: 8px;
  border: none;
  background: none;
  color: #64748b;
  cursor: pointer;
  font-size: 16px;
}
</style>
