<template>
  <div v-if="totalPages > 1" class="pagination">
    <button class="pagination-btn" :disabled="current <= 1" @click="go(current - 1)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
    </button>

    <template v-for="page in visiblePages" :key="page">
      <span v-if="page === '...'" class="pagination-ellipsis">...</span>
      <button v-else :class="['pagination-btn', { active: page === current }]" @click="go(page)">
        {{ page }}
      </button>
    </template>

    <button class="pagination-btn" :disabled="current >= totalPages" @click="go(current + 1)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
    </button>

    <span class="pagination-info">Page {{ current }} / {{ totalPages }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  current: number;
  total: number;
  pageSize?: number;
}>(), { pageSize: 20 });

const emit = defineEmits<{ (e: "update:current", page: number): void }>();

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));

const visiblePages = computed<(number | "...")[]>(() => {
  const pages: (number | "...")[] = [];
  const total = totalPages.value;
  const cur = props.current;

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
    return pages;
  }

  pages.push(1);
  if (cur > 3) pages.push("...");

  const start = Math.max(2, cur - 1);
  const end = Math.min(total - 1, cur + 1);
  for (let i = start; i <= end; i++) pages.push(i);

  if (cur < total - 2) pages.push("...");
  pages.push(total);

  return pages;
});

function go(page: number) {
  if (page < 1 || page > totalPages.value || page === props.current) return;
  emit("update:current", page);
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px 0;
}

.pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.pagination-btn:hover:not(:disabled):not(.active) {
  border-color: #5b8cff;
  color: #5b8cff;
}

.pagination-btn.active {
  background: rgba(91, 140, 255, 0.1);
  border-color: #5b8cff;
  color: #5b8cff;
}

.pagination-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.pagination-ellipsis {
  color: #94a3b8;
  font-size: 13px;
  padding: 0 4px;
}

.pagination-info {
  margin-left: 12px;
  color: #94a3b8;
  font-size: 12px;
}
</style>
