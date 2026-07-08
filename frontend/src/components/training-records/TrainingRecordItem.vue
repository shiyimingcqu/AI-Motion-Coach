<template>
  <article class="tr-item" @click="$emit('click', record)">
    <div class="tr-item-thumb" :style="{ background: meta.accent }">
      <img v-if="imgSrc" :src="imgSrc" :alt="meta.name" />
      <span v-else class="tr-item-emoji">{{ iconChar }}</span>
    </div>

    <div class="tr-item-main">
      <div class="tr-item-name-row">
        <h4>{{ meta.name }}</h4>
        <span class="tr-pill" :class="levelClass">{{ meta.level }}</span>
        <span class="tr-pill soft">{{ meta.equipment }}</span>
        <span class="tr-pill soft">{{ meta.camera_view }}拍摄</span>
      </div>
    </div>

    <div class="tr-item-meta">
      <Calendar :size="14" />
      <span>{{ dateTime }}</span>
    </div>

    <div class="tr-item-meta">
      <Clock :size="14" />
      <span>{{ duration }}</span>
    </div>

    <div class="tr-item-score">
      <strong>{{ record.average_score }}</strong>
      <span>分</span>
    </div>

    <div class="tr-item-grade">
      <span class="tr-grade-badge" :style="{ background: level.bgColor, color: level.textColor }">
        {{ level.label }}
      </span>
    </div>

    <button class="tr-detail-btn" type="button" @click.stop="$emit('click', record)">
      查看详情
      <ChevronRight :size="14" />
    </button>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Calendar, ChevronRight, Clock } from "lucide-vue-next";
import {
  EXERCISE_META,
  formatDateTime,
  formatDuration,
  getExerciseMeta,
  getScoreLevel,
} from "@/data/trainingRecords";

const props = defineProps<{
  record: {
    session_id: string;
    exercise: string;
    created_at: string;
    duration_seconds: number;
    average_score: number;
  };
}>();

defineEmits<{
  (e: "click", record: { session_id: string }): void;
}>();

const meta = computed(() => getExerciseMeta(props.record.exercise));
const level = computed(() => getScoreLevel(props.record.average_score));
const dateTime = computed(() => formatDateTime(props.record.created_at));
const duration = computed(() => formatDuration(props.record.duration_seconds));

const imgSrc = computed(() => `/exercises/${props.record.exercise}.png`);

const levelClass = computed(() => {
  const lvl = meta.value.level;
  if (lvl === "入门") return "level-easy";
  if (lvl === "中级") return "level-mid";
  return "level-hard";
});

const iconChar = computed(() => EXERCISE_META[props.record.exercise]?.name?.charAt(0) || "🏋");
</script>

<style scoped>
.tr-item {
  display: grid;
  grid-template-columns: 120px minmax(220px, 1.4fr) 1.2fr 0.7fr 0.8fr 0.7fr auto;
  align-items: center;
  gap: 18px;
  padding: 13px 22px;
  min-height: 90px;
  border-bottom: 1px solid #f1f3f9;
  cursor: pointer;
  transition: background 0.18s;
}

.tr-item:hover { background: #FAF9FF; }
.tr-item:last-child { border-bottom: 0; }

@media (max-width: 1100px) {
  .tr-item {
    grid-template-columns: 108px 1fr auto;
    grid-template-areas:
      "thumb main main"
      "thumb meta meta"
      "score score detail";
    gap: 8px 14px;
  }
  .tr-item-thumb { grid-area: thumb; }
  .tr-item-main { grid-area: main; }
  .tr-item-meta  { grid-area: meta; }
  .tr-item-score { grid-area: score; }
  .tr-item-grade { display: none; }
  .tr-detail-btn { grid-area: detail; }
}

.tr-item-thumb {
  width: 108px;
  height: 64px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: #f1f5f9;
  flex-shrink: 0;
}

.tr-item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.tr-item-emoji {
  font-size: 28px;
}

.tr-item-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tr-item-main h4 {
  font-size: 16px;
  font-weight: 700;
  color: #15172A;
  margin: 0;
}

.tr-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.tr-pill.level-easy { background: #dcfce7; color: #16a34a; }
.tr-pill.level-mid  { background: #dbeafe; color: #2563eb; }
.tr-pill.level-hard { background: #ffedd5; color: #ea580c; }
.tr-pill.soft { background: #f1f3f9; color: #475569; }

.tr-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #667085;
  font-size: 13px;
}

.tr-item-meta svg { color: #98a2b3; }

.tr-item-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: #15172A;
}

.tr-item-score strong {
  font-size: 22px;
  font-weight: 800;
}

.tr-item-score span {
  font-size: 13px;
  color: #667085;
}

.tr-grade-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

.tr-detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 34px;
  padding: 0 16px;
  background: #ffffff;
  color: #6C3BFF;
  border: 1px solid #d4c5ff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.tr-detail-btn:hover {
  background: #f1ecff;
  border-color: #6C3BFF;
}
</style>
