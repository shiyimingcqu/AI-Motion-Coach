<template>
  <section class="tr-filter">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      class="tr-filter-tab"
      :class="{ active: modelValue === tab.key }"
      @click="$emit('update:modelValue', tab.key)"
    >
      <span>{{ tab.label }}</span>
      <span v-if="tab.hasDropdown" class="tr-filter-caret">▾</span>
    </button>
  </section>
</template>

<script setup lang="ts">
type TabKey = "all" | "exercise" | "date";

defineProps<{
  modelValue: TabKey;
}>();

defineEmits<{
  (e: "update:modelValue", value: TabKey): void;
}>();

const tabs: { key: TabKey; label: string; hasDropdown: boolean }[] = [
  { key: "all",      label: "全部记录",   hasDropdown: false },
  { key: "exercise", label: "按动作筛选", hasDropdown: true  },
  { key: "date",     label: "按时间筛选", hasDropdown: true  },
];
</script>

<style scoped>
.tr-filter {
  display: flex;
  align-items: center;
  gap: 36px;
  border-bottom: 1px solid #eef0f6;
}

.tr-filter-tab {
  background: transparent;
  border: 0;
  padding: 10px 0;
  margin: 0;
  position: relative;
  color: #667085;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}

.tr-filter-tab:hover { color: #6C3BFF; }

.tr-filter-tab.active { color: #6C3BFF; }

.tr-filter-tab.active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: #6C3BFF;
  border-radius: 2px 2px 0 0;
}

.tr-filter-caret {
  font-size: 12px;
  color: inherit;
}
</style>
