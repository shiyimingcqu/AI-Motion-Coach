<template>
  <div class="state-display" :class="[type, size]">
    <!-- ===== Loading ===== -->
    <div v-if="type === 'loading'" class="sd-loading">
      <div v-if="skeleton" class="sd-skeleton" :class="skeleton">
        <!-- Table skeleton -->
        <div v-if="skeleton === 'table'" class="skeleton-table">
          <div class="skeleton-row" v-for="i in (skeletonRows || 5)" :key="i">
            <div class="skeleton-cell" style="width: 30%"><div class="skeleton-pulse" /></div>
            <div class="skeleton-cell" style="width: 20%"><div class="skeleton-pulse" /></div>
            <div class="skeleton-cell" style="width: 20%"><div class="skeleton-pulse" /></div>
            <div class="skeleton-cell" style="width: 15%"><div class="skeleton-pulse" /></div>
            <div class="skeleton-cell" style="width: 15%"><div class="skeleton-pulse" /></div>
          </div>
        </div>
        <!-- Card skeleton (dashboard grid) -->
        <div v-else-if="skeleton === 'cards'" class="skeleton-cards">
          <div v-for="i in (skeletonRows || 4)" :key="i" class="skeleton-card">
            <div style="height: 14px; width: 60%; margin-bottom: 12px"><div class="skeleton-pulse" /></div>
            <div style="height: 28px; width: 40%; margin-bottom: 8px"><div class="skeleton-pulse" /></div>
            <div style="height: 12px; width: 80%"><div class="skeleton-pulse" /></div>
          </div>
        </div>
        <!-- Chart skeleton -->
        <div v-else-if="skeleton === 'chart'" class="skeleton-chart">
          <div class="skeleton-chart-area">
            <div class="skeleton-chart-line" v-for="i in 4" :key="i" :style="{ width: `${60 + i * 10}%`, animationDelay: `${i * 0.15}s` }" />
          </div>
        </div>
        <!-- List skeleton -->
        <div v-else-if="skeleton === 'list'" class="skeleton-list">
          <div v-for="i in (skeletonRows || 4)" :key="i" class="skeleton-list-item">
            <div class="skeleton-avatar"><div class="skeleton-pulse round" /></div>
            <div style="flex: 1">
              <div style="height: 14px; width: 45%; margin-bottom: 8px"><div class="skeleton-pulse" /></div>
              <div style="height: 11px; width: 70%"><div class="skeleton-pulse" /></div>
            </div>
          </div>
        </div>
        <!-- Default spinner -->
        <template v-else>
          <div class="sd-spinner"><div class="spinner-ring" /><div class="spinner-ring spinner-ring-inner" /></div>
        </template>
      </div>
      <p v-if="text || $slots.default" class="sd-text"><slot>{{ text || '加载中...' }}</slot></p>
    </div>

    <!-- ===== Empty ===== -->
    <div v-else-if="type === 'empty'" class="sd-empty">
      <div class="sd-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
          <polyline points="13 2 13 9 20 9"/>
          <line x1="9" y1="13" x2="15" y2="13"/>
          <line x1="12" y1="10" x2="12" y2="16"/>
        </svg>
      </div>
      <p class="sd-title"><slot name="title">{{ title || '暂无数据' }}</slot></p>
      <p v-if="text" class="sd-text">{{ text }}</p>
      <button v-if="actionLabel" class="sd-action" @click="$emit('action')">
        <slot name="action">{{ actionLabel }}</slot>
      </button>
    </div>

    <!-- ===== Error ===== -->
    <div v-else-if="type === 'error'" class="sd-error">
      <div class="sd-icon error">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <p class="sd-title"><slot name="title">{{ title || '加载失败' }}</slot></p>
      <p v-if="text" class="sd-text">{{ text }}</p>
      <button v-if="retryLabel" class="sd-action" @click="$emit('retry')">
        <slot name="retry">{{ retryLabel }}</slot>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  type: "loading" | "empty" | "error";
  skeleton?: "table" | "cards" | "chart" | "list";
  skeletonRows?: number;
  title?: string;
  text?: string;
  actionLabel?: string;
  retryLabel?: string;
  size?: "sm" | "md" | "lg";
}>(), {
  retryLabel: "重试",
  size: "md",
});

defineEmits<{
  (e: "action"): void;
  (e: "retry"): void;
}>();
</script>

<style scoped>
/* ===== Root ===== */
.state-display {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px;
  min-height: 200px;
  padding: 32px 24px;
  text-align: center;
  color: #64748b;
}
.state-display.sm { min-height: 120px; padding: 20px 16px; gap: 10px; }
.state-display.lg { min-height: 320px; padding: 48px 32px; gap: 20px; }

/* ===== Spinner ===== */
.sd-spinner { position: relative; width: 40px; height: 40px; }
.spinner-ring {
  position: absolute; inset: 0;
  border: 3px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.spinner-ring-inner {
  inset: 6px;
  border-top-color: #60a5fa;
  animation-duration: 0.7s;
  animation-direction: reverse;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== Icon ===== */
.sd-icon {
  display: grid; place-items: center;
  width: 72px; height: 72px;
  border-radius: 50%;
  background: rgba(59,130,246,0.06);
  color: #64748b;
}
.sd-icon.error {
  background: rgba(239,68,68,0.08);
  color: #f87171;
}

/* ===== Text ===== */
.sd-title { color: #94a3b8; font-size: 16px; font-weight: 700; margin: 0; }
.sd-text { color: #64748b; font-size: 14px; margin: 0; line-height: 1.5; max-width: 320px; }

/* ===== Actions ===== */
.sd-action {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 20px;
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 8px;
  background: rgba(59,130,246,0.06);
  color: #93c5fd;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
}
.sd-action:hover { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.3); }

/* ===== Skeleton ===== */
.sd-skeleton { width: 100%; max-width: 800px; }
.skeleton-pulse {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, rgba(30,41,59,0.4) 25%, rgba(59,130,246,0.08) 50%, rgba(30,41,59,0.4) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.skeleton-pulse.round { border-radius: 50%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Table skeleton */
.skeleton-table { display: grid; gap: 8px; }
.skeleton-row { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(59,130,246,0.04); }
.skeleton-cell { height: 14px; }

/* Cards skeleton */
.skeleton-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.skeleton-card {
  padding: 20px; border-radius: 10px;
  background: rgba(15,23,42,0.5); border: 1px solid rgba(59,130,246,0.06);
}

/* Chart skeleton */
.skeleton-chart {
  height: 180px; border-radius: 10px;
  background: rgba(15,23,42,0.4);
  border: 1px solid rgba(59,130,246,0.06);
  padding: 24px;
  display: flex; flex-direction: column; justify-content: flex-end;
  gap: 8px;
}
.skeleton-chart-area { display: flex; flex-direction: column; justify-content: flex-end; gap: 10px; }
.skeleton-chart-line { height: 16px; border-radius: 4px; background: rgba(59,130,246,0.1); animation: shimmer 2s infinite; }

/* List skeleton */
.skeleton-list { display: grid; gap: 8px; }
.skeleton-list-item { display: flex; gap: 12px; align-items: center; padding: 12px; border-radius: 8px; background: rgba(15,23,42,0.3); }
.skeleton-avatar { width: 36px; height: 36px; flex-shrink: 0; }
</style>
