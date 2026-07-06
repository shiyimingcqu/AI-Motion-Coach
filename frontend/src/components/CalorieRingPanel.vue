<template>
  <article class="calorie-ring-panel">
    <header>
      <h3>卡路里消耗 / Calories</h3>
      <span>{{ subtitle }}</span>
    </header>

    <div class="ring-stage">
      <div ref="ringRef" class="ring-canvas" />
      <div class="ring-center">
        <strong class="ring-value">{{ displayCalories }}</strong>
        <span class="ring-label">千卡 kcal</span>
      </div>
    </div>

    <div class="food-equiv">
      <span class="food-icon bounce">{{ equivalence.icon }}</span>
      <p>{{ equivalence.text }}</p>
    </div>

    <div v-if="breakdown.length" class="breakdown-rings">
      <div v-for="item in breakdown" :key="item.name" class="mini-ring-item">
        <div :ref="(el) => setMiniRef(item.name, el)" class="mini-ring-canvas" />
        <strong>{{ Math.round(item.value) }}</strong>
        <small>{{ item.name }}</small>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { getFoodEquivalence } from "@/utils/calorieEquivalence";

const props = withDefaults(defineProps<{
  totalCalories: number;
  goal?: number;
  subtitle?: string;
  breakdown?: { name: string; value: number }[];
}>(), {
  goal: 500,
  subtitle: "本期训练累计消耗",
  breakdown: () => [],
});

const ringRef = ref<HTMLElement | null>(null);
const miniRefs = new Map<string, HTMLElement>();
let mainChart: echarts.ECharts | null = null;
const miniCharts: echarts.ECharts[] = [];

const displayCalories = computed(() => Math.round(props.totalCalories * 10) / 10);
const equivalence = computed(() => getFoodEquivalence(props.totalCalories));
const ringPercent = computed(() =>
  Math.min(100, Math.round((props.totalCalories / Math.max(props.goal, 1)) * 100)),
);

function setMiniRef(name: string, el: unknown) {
  if (el instanceof HTMLElement) miniRefs.set(name, el);
  else miniRefs.delete(name);
}

function buildRingOption(value: number, color: string, radius = "88%") {
  return {
    backgroundColor: "transparent",
    series: [{
      type: "gauge",
      startAngle: 90,
      endAngle: -270,
      radius,
      pointer: { show: false },
      progress: {
        show: true,
        overlap: false,
        roundCap: true,
        clip: false,
        itemStyle: { color },
      },
      axisLine: { lineStyle: { width: 14, color: [[1, "rgba(59,130,246,0.12)"]] } },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      detail: { show: false },
      data: [{ value }],
    }],
  };
}

function renderMainRing() {
  if (!ringRef.value) return;
  mainChart?.dispose();
  mainChart = echarts.init(ringRef.value);
  mainChart.setOption(buildRingOption(ringPercent.value, "#f59e0b") as echarts.EChartsOption);
}

function renderMiniRings() {
  miniCharts.splice(0).forEach((c) => c.dispose());
  const max = Math.max(...props.breakdown.map((b) => b.value), 1);
  props.breakdown.forEach((item, index) => {
    const el = miniRefs.get(item.name);
    if (!el) return;
    const chart = echarts.init(el);
    const pct = Math.min(100, Math.round((item.value / max) * 100));
    const colors = ["#60a5fa", "#34d399", "#a78bfa", "#f87171"];
    chart.setOption(buildRingOption(pct, colors[index % colors.length], "90%") as echarts.EChartsOption);
    miniCharts.push(chart);
  });
}

function handleResize() {
  mainChart?.resize();
  miniCharts.forEach((c) => c.resize());
}

watch(
  () => [props.totalCalories, props.goal, props.breakdown],
  () => nextTick(() => {
    renderMainRing();
    renderMiniRings();
  }),
  { deep: true },
);

onMounted(() => {
  nextTick(() => {
    renderMainRing();
    renderMiniRings();
  });
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  mainChart?.dispose();
  miniCharts.forEach((c) => c.dispose());
});
</script>

<style scoped>
.calorie-ring-panel {
  padding: 24px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(8, 13, 26, 0.99));
  border: 1px solid rgba(59, 130, 246, 0.14);
  display: grid;
  gap: 18px;
}
.calorie-ring-panel header { display: grid; gap: 4px; }
.calorie-ring-panel h3 { margin: 0; color: #f8fafc; font-size: 16px; }
.calorie-ring-panel header span { color: #64748b; font-size: 12px; }
.ring-stage {
  position: relative;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
  aspect-ratio: 1;
}
.ring-canvas { width: 100%; height: 100%; }
.ring-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  pointer-events: none;
}
.ring-value {
  font-size: 52px;
  font-weight: 800;
  color: #f8fafc;
  line-height: 1;
}
.ring-label { color: #94a3b8; font-size: 13px; margin-top: 6px; }
.food-equiv {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
}
.food-icon { font-size: 36px; line-height: 1; }
.food-equiv p { margin: 0; color: #fde68a; font-size: 14px; font-weight: 600; }
.bounce { animation: food-bounce 2s ease-in-out infinite; }
@keyframes food-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.breakdown-rings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
}
.mini-ring-item {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(8, 13, 26, 0.5);
}
.mini-ring-canvas { width: 72px; height: 72px; }
.mini-ring-item strong { color: #f8fafc; font-size: 14px; }
.mini-ring-item small { color: #64748b; font-size: 11px; text-align: center; }
</style>
