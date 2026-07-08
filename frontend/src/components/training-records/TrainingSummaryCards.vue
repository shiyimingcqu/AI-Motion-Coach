<template>
  <section class="tr-summary">
    <article v-for="card in cards" :key="card.key" class="tr-stat-card">
      <div class="tr-stat-icon" :style="{ background: card.iconBg, color: card.iconColor }">
        <component :is="card.icon" :size="22" />
      </div>
      <div class="tr-stat-body">
        <span class="tr-stat-label">{{ card.label }}</span>
        <div class="tr-stat-value">
          <strong>{{ card.value }}</strong>
          <span class="tr-stat-unit">{{ card.unit }}</span>
          <span v-if="card.delta != null" class="tr-stat-delta">
            <TrendingUp :size="12" />
            ↑{{ card.delta }}%
          </span>
        </div>
        <span class="tr-stat-compare">较上月 ↑{{ card.delta }}%</span>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { Box, Clock, TrendingUp, Trophy } from "lucide-vue-next";

defineProps<{
  totalCount: number;
  totalHours: number;
  avgScore: number;
  completionRate: number;
}>();

const cards = [
  { key: "count",   label: "训练次数",     value: "48",      unit: "次",   delta: 20, icon: Box,    iconBg: "#f1ecff", iconColor: "#6C3BFF" },
  { key: "hours",   label: "总训练时长",   value: "18.6",    unit: "小时", delta: 15, icon: Clock,  iconBg: "#dcfce7", iconColor: "#16a34a" },
  { key: "score",   label: "平均得分",     value: "78",      unit: "分",   delta: 8,  icon: Trophy, iconBg: "#dbeafe", iconColor: "#3b82f6" },
  { key: "rate",    label: "动作完成率",   value: "92",      unit: "%",    delta: 12, icon: TrendingUp, iconBg: "#ffedd5", iconColor: "#f97316" },
];
</script>

<style scoped>
.tr-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 1100px) {
  .tr-summary { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 560px) {
  .tr-summary { grid-template-columns: 1fr; }
}

.tr-stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.tr-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(45, 35, 90, 0.10);
}

.tr-stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.tr-stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.tr-stat-label {
  color: #667085;
  font-size: 13px;
  font-weight: 500;
}

.tr-stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-wrap: wrap;
}

.tr-stat-value strong {
  color: #15172A;
  font-size: 26px;
  font-weight: 800;
  line-height: 1.1;
}

.tr-stat-unit {
  color: #667085;
  font-size: 14px;
  font-weight: 500;
}

.tr-stat-delta {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
  color: #16a34a;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  background: #dcfce7;
  border-radius: 6px;
}

.tr-stat-compare {
  color: #98a2b3;
  font-size: 11px;
}
</style>
