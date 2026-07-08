<template>
  <section class="tr-calendar">
    <header class="tr-cal-header">
      <h3>训练日历</h3>
      <div class="tr-cal-nav">
        <button type="button" @click="$emit('prev')" aria-label="上个月">
          <ChevronLeft :size="14" />
        </button>
        <span class="tr-cal-title">{{ year }}年{{ month + 1 }}月</span>
        <button type="button" @click="$emit('next')" aria-label="下个月">
          <ChevronRight :size="14" />
        </button>
      </div>
    </header>

    <div class="tr-cal-grid">
      <span v-for="w in WEEK_LABELS" :key="w" class="tr-cal-week">{{ w }}</span>
      <button
        v-for="(cell, idx) in cells"
        :key="idx"
        type="button"
        class="tr-cal-day"
        :class="{
          'is-empty': !cell.inMonth,
          'is-today': cell.dateKey === todayKey,
          'is-selected': cell.dateKey === selectedKey,
          'has-record': !!(cell.dateKey && recordMap[cell.dateKey]),
        }"
        :style="cell.dateKey ? (recordMap[cell.dateKey] ? { '--day-color': getLevelColor(recordMap[cell.dateKey]) } : {}) : {}"
        :disabled="!cell.inMonth"
        @click="cell.inMonth && cell.dateKey && $emit('select', cell.dateKey)"
      >
        <span v-if="cell.inMonth">{{ cell.day }}</span>
        <span v-else class="tr-cal-fade"></span>
        <span v-if="cell.inMonth && cell.dateKey && recordMap[cell.dateKey]" class="tr-cal-dot" />
      </button>
    </div>

    <div class="tr-cal-legend">
      <span v-for="lvl in SCORE_LEVELS" :key="lvl.key" class="tr-cal-legend-item">
        <span class="tr-cal-legend-dot" :style="{ background: lvl.color }" />
        <span>{{ lvl.label }} ({{ lvl.min === 0 ? '<50' : lvl.min }}-{{ lvl.max === 100 ? '100' : lvl.max }})</span>
      </span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import {
  SCORE_LEVELS,
  WEEK_LABELS,
  buildCalendarGrid,
  getScoreLevel,
} from "@/data/trainingRecords";
import { computed } from "vue";

const props = defineProps<{
  year: number;
  month: number;
  selectedKey: string | null;
  recordMap: Record<string, number>;
}>();

defineEmits<{
  (e: "prev"): void;
  (e: "next"): void;
  (e: "select", key: string): void;
}>();

const cells = computed(() => buildCalendarGrid(props.year, props.month));

const todayKey = (() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
})();

function getLevelColor(score: number) {
  return getScoreLevel(score).color;
}
</script>

<style scoped>
.tr-calendar {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 20px 22px;
}

.tr-cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.tr-cal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #15172A;
}

.tr-cal-nav {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tr-cal-nav button {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border: 0;
  background: transparent;
  color: #667085;
  cursor: pointer;
  border-radius: 6px;
}

.tr-cal-nav button:hover { background: #f1f3f9; color: #15172A; }

.tr-cal-title {
  min-width: 80px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #15172A;
}

.tr-cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.tr-cal-week {
  text-align: center;
  font-size: 11px;
  color: #98a2b3;
  font-weight: 600;
  padding: 4px 0;
}

.tr-cal-day {
  position: relative;
  aspect-ratio: 1 / 1;
  border: 0;
  background: transparent;
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 50%;
  display: grid;
  place-items: center;
  transition: all 0.15s;
}

.tr-cal-day.is-empty {
  visibility: hidden;
  cursor: default;
}

.tr-cal-day:not(.is-empty):hover {
  background: #f1ecff;
  color: #6C3BFF;
}

.tr-cal-day.is-today {
  background: #f1ecff;
  color: #6C3BFF;
  font-weight: 700;
}

.tr-cal-day.is-selected {
  background: #6C3BFF;
  color: #ffffff;
  font-weight: 700;
}

.tr-cal-day.has-record {
  --day-color: #6C3BFF;
  background: color-mix(in srgb, var(--day-color) 14%, transparent);
  color: #15172A;
  font-weight: 600;
}

.tr-cal-day.has-record.is-selected {
  background: #6C3BFF;
  color: #ffffff;
}

.tr-cal-fade { display: none; }

.tr-cal-dot {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--day-color, #6C3BFF);
}

.tr-cal-day.is-selected .tr-cal-dot { background: #ffffff; }

.tr-cal-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f1f3f9;
}

.tr-cal-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #667085;
}

.tr-cal-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
</style>
