<template>
  <section class="tr-trend">
    <header class="tr-trend-header">
      <h3>身体数据趋势</h3>
      <select v-model="rangeKey" class="tr-trend-range">
        <option v-for="r in ranges" :key="r.key" :value="r.key">{{ r.label }}</option>
      </select>
    </header>

    <ul class="tr-trend-list">
      <li v-for="(m, idx) in metrics" :key="idx" class="tr-trend-item">
        <div class="tr-trend-icon" :style="{ background: m.bg, color: m.fg }">
          <component :is="m.icon" :size="16" />
        </div>
        <div class="tr-trend-body">
          <div class="tr-trend-row">
            <span class="tr-trend-name">{{ m.name }}</span>
            <span class="tr-trend-delta">↑{{ m.delta }}%</span>
          </div>
          <div class="tr-trend-row">
            <span class="tr-trend-value">{{ m.value }}<span class="tr-trend-unit">{{ m.unit }}</span></span>
            <span ref="chartRefs" class="tr-trend-spark" :data-key="idx" />
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, nextTick } from "vue";
import * as echarts from "echarts";
import { Clock, Flame, Trophy, Zap } from "lucide-vue-next";

const props = defineProps<{
  hours: number;
  avgScore: number;
  completion: number;
  calories: number;
}>();

const ranges = [
  { key: "7d",  label: "最近7天" },
  { key: "30d", label: "最近30天" },
  { key: "90d", label: "最近90天" },
];

const rangeKey = ref<"7d" | "30d" | "90d">("30d");

// 根据 props 派生指标，附带计算 sparkline 数据
const metrics = ref([
  { name: "训练时长",   value: props.hours.toFixed(1), unit: "小时", delta: 12, bg: "#dcfce7", fg: "#16a34a", icon: Clock,  data: [] as number[] },
  { name: "平均得分",   value: String(props.avgScore), unit: "分",   delta: 8,  bg: "#dbeafe", fg: "#3b82f6", icon: Trophy, data: [] as number[] },
  { name: "动作完成率", value: String(props.completion), unit: "%",  delta: 10, bg: "#ffedd5", fg: "#f97316", icon: Zap,    data: [] as number[] },
  { name: "消耗热量",   value: "3260",                unit: "千卡", delta: 15, bg: "#fee2e2", fg: "#ef4444", icon: Flame,  data: [] as number[] },
]);

watch(() => [props.hours, props.avgScore, props.completion, props.calories], () => {
  metrics.value[0].value = props.hours.toFixed(1);
  metrics.value[1].value = String(props.avgScore);
  metrics.value[2].value = String(props.completion);
  metrics.value[3].value = String(props.calories);
});

watch(rangeKey, () => {
  seedSpark();
  nextTick(renderCharts);
});

const chartRefs = ref<HTMLElement[]>([]);
let charts: echarts.ECharts[] = [];

function seedSpark() {
  const len = rangeKey.value === "7d" ? 7 : rangeKey.value === "30d" ? 14 : 24;
  const base: number[] = [12, 18, 14, 22, 19, 26, 24, 30, 28, 32, 29, 35];
  metrics.value.forEach((m) => {
    m.data = Array.from({ length: len }, (_, i) => Math.max(0, base[i % base.length] + Math.sin(i) * 5 + (Math.random() * 6 - 3)));
  });
}

function renderCharts() {
  charts.forEach((c) => c.dispose());
  charts = [];
  const palette = ["#10b981", "#3b82f6", "#f97316", "#ef4444"];
  chartRefs.value.forEach((el, i) => {
    if (!el) return;
    const inst = echarts.init(el);
    inst.setOption({
      grid: { left: 0, right: 0, top: 2, bottom: 2 },
      xAxis: { type: "category", show: false, data: metrics.value[i].data.map((_, j) => j) },
      yAxis: { type: "value", show: false, scale: true },
      tooltip: { show: false },
      series: [
        {
          type: "line",
          smooth: true,
          symbol: "none",
          data: metrics.value[i].data,
          lineStyle: { color: palette[i % palette.length], width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: palette[i % palette.length] + "55" },
              { offset: 1, color: palette[i % palette.length] + "00" },
            ]),
          },
        },
      ],
    });
    charts.push(inst);
  });
}

function handleResize() {
  charts.forEach((c) => c.resize());
}

onMounted(() => {
  seedSpark();
  nextTick(renderCharts);
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  charts.forEach((c) => c.dispose());
  charts = [];
});
</script>

<style scoped>
.tr-trend {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  padding: 20px 22px;
}

.tr-trend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.tr-trend-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #15172A;
}

.tr-trend-range {
  height: 28px;
  padding: 0 26px 0 10px;
  border: 1px solid #eef0f6;
  border-radius: 6px;
  background: #ffffff
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2398A2B3' stroke-width='2'><polyline points='6 9 12 15 18 9'/></svg>")
    no-repeat right 8px center;
  color: #475569;
  font-size: 12px;
  cursor: pointer;
  appearance: none;
}

.tr-trend-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tr-trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f5f6fa;
}

.tr-trend-item:last-child { border-bottom: 0; padding-bottom: 0; }

.tr-trend-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.tr-trend-body { flex: 1; min-width: 0; }

.tr-trend-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.tr-trend-row + .tr-trend-row { margin-top: 4px; }

.tr-trend-name {
  font-size: 13px;
  color: #475569;
}

.tr-trend-delta {
  font-size: 11px;
  color: #16a34a;
  font-weight: 700;
}

.tr-trend-value {
  font-size: 16px;
  font-weight: 800;
  color: #15172A;
}

.tr-trend-unit {
  font-size: 11px;
  color: #667085;
  font-weight: 500;
  margin-left: 2px;
}

.tr-trend-spark {
  width: 100px;
  height: 28px;
  flex-shrink: 0;
}
</style>
