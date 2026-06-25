<template>
  <div class="sports-dashboard">
    <!-- ===== 顶部精简概览 ===== -->
    <section class="top-header">
      <div class="th-left">
        <div class="th-avatar">张</div>
        <div class="th-info">
          <strong>张三</strong>
          <p>深蹲动作评估 · 2024-05-24 10:30</p>
        </div>
      </div>

      <div class="th-score">
        <span class="th-score-label">综合评分</span>
        <div class="th-score-value">
          <span class="th-score-num">86</span>
          <span class="th-score-unit">/100</span>
        </div>
        <span class="th-score-badge good">良好</span>
      </div>

      <div class="th-compare">
        <span class="th-compare-label">对比上次</span>
        <strong class="th-compare-value up">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>
          8.3%
        </strong>
      </div>

      <div class="th-actions">
        <button class="btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
          开始评估
        </button>
      </div>
    </section>

    <!-- ===== 核心区域：58% / 42% ===== -->
    <section class="core-row">
      <!-- 左侧主面板（58%） -->
      <div class="main-panel">
        <header class="panel-header">
          <div class="panel-left">
            <div class="panel-title-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
              <h2>深蹲动作评估</h2>
            </div>
            <div class="phase-badge">
              <span class="phase-dot pulse-blue" />
              当前阶段：<strong>下蹲阶段</strong>
            </div>
            <span class="status-pill warn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              检测到 2 项问题
            </span>
          </div>
        </header>

        <!-- 横向指标条 -->
        <div class="metric-strip">
          <div v-for="m in sideMetrics" :key="m.label" class="ms-item" :title="m.tip">
            <span class="ms-label">{{ m.label }}</span>
            <strong :class="m.cls">{{ m.value }}</strong>
            <div class="ms-track">
              <i :style="{ width: m.value + '%' }" :class="m.cls" />
            </div>
          </div>
        </div>

        <!-- 骨骼区域 -->
        <div class="skel-area">
          <div class="skel-grid" />
          <div class="skel-stage-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            下蹲阶段 · 膝关节角度 73°
          </div>

          <div class="skel-layout">
            <svg viewBox="0 0 300 520" class="pose-skeleton">
              <circle cx="150" cy="42" r="20" fill="none" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="150" y1="62" x2="150" y2="90" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="150" y1="90" x2="150" y2="210" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="110" y1="210" x2="190" y2="210" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="150" y1="110" x2="90" y2="172" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="90" y1="172" x2="72" y2="230" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="150" y1="110" x2="210" y2="172" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="210" y1="172" x2="228" y2="230" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="130" y1="210" x2="70" y2="350" stroke="#f59e0b" stroke-width="3" />
              <line x1="70" y1="350" x2="55" y2="470" stroke="#f59e0b" stroke-width="2.5" />
              <line x1="170" y1="210" x2="230" y2="350" stroke="#3b82f6" stroke-width="2.5" />
              <line x1="230" y1="350" x2="245" y2="470" stroke="#3b82f6" stroke-width="2.5" />
              <g fill="#3b82f6">
                <circle cx="150" cy="90" r="5" /><circle cx="150" cy="130" r="5" />
                <circle cx="90" cy="172" r="5" /><circle cx="72" cy="230" r="4.5" />
                <circle cx="210" cy="172" r="5" /><circle cx="228" cy="230" r="4.5" />
                <circle cx="130" cy="210" r="5" /><circle cx="170" cy="210" r="5" />
              </g>
              <g fill="#f59e0b"><circle cx="70" cy="350" r="5" /><circle cx="55" cy="470" r="4.5" /></g>
              <circle cx="230" cy="350" r="5" fill="#3b82f6" />
              <circle cx="245" cy="470" r="4.5" fill="#3b82f6" />
              <g class="warning-anim">
                <circle cx="70" cy="350" r="24" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.7" />
                <text x="70" y="390" text-anchor="middle" fill="#ef4444" font-size="10" font-weight="700">膝内扣</text>
              </g>
            </svg>
          </div>

          <!-- 评分浮层 -->
          <div class="score-card-overlay">
            <div class="score-ring-big">
              <span class="score-ring-num">86</span>
              <span class="score-ring-label">综合评分</span>
            </div>
            <div class="score-ring-meta">
              <span class="score-ring-grade good">良好</span>
              <div class="score-ring-issues">
                <span>主要问题：</span>
                <strong>膝内扣</strong><span class="sep">·</span><strong>骨盆前倾</strong>
              </div>
            </div>
          </div>

          <!-- 视角切换 -->
          <div class="view-strip">
            <button class="view-angle active">正面</button>
            <button class="view-angle">侧面</button>
            <button class="view-angle">后面</button>
            <button class="view-angle disabled">3D</button>
          </div>
        </div>

        <!-- 阶段流程 + 播放控制 -->
        <div class="phase-flow-bar">
          <div class="phase-flow">
            <div v-for="(p, i) in phases" :key="p" class="phase-step" :class="{ active: i === 1, done: i < 1 }">
              <div class="phase-circle">
                <svg v-if="i < 1" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polyline points="20 6 9 17 4 12"/></svg>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <span class="phase-label">{{ p }}</span>
              <span v-if="i === 1" class="phase-now">当前</span>
            </div>
            <div class="phase-connector"><div class="phase-connector-fill" style="width: 30%" /></div>
          </div>

          <div class="play-controls">
            <button class="play-btn-small">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="8,5 19,12 8,19"/></svg>
            </button>
            <div class="timeline-mini">
              <div class="tl-track">
                <div class="tl-fill" style="width: 38%" />
                <div class="tl-thumb" style="left: 38%" />
              </div>
              <div class="tl-labels"><span>00:12</span><span>03:45</span></div>
            </div>
            <div class="speed-mini">
              <button v-for="s in speeds" :key="s" :class="{ active: s === '1.0x' }">{{ s }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 右侧面板（42%） ===== -->
      <aside class="right-col">
        <!-- Tab 切换 -->
        <div class="tab-bar">
          <button :class="['tab-btn', { active: activeTab === 'problems' }]" @click="activeTab = 'problems'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            问题识别 <span class="tab-count">4</span>
          </button>
          <button :class="['tab-btn', { active: activeTab === 'advice' }]" @click="activeTab = 'advice'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            纠正建议 <span class="tab-count">5</span>
          </button>
        </div>

        <!-- 问题识别 -->
        <div v-show="activeTab === 'problems'" class="section-card">
          <header class="sc-header">
            <div class="sc-header-icon danger">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <div>
              <h3>问题识别</h3>
              <p>发现 <strong>4</strong> 个动作问题，共扣 <strong class="score-deduct">-23</strong> 分</p>
            </div>
          </header>

          <div class="problem-list">
            <div v-for="(item, i) in problems" :key="i"
              :class="['problem-item', item.level, { selected: selectedProblem === i }]"
              @click="selectedProblem = i">
              <div class="pi-top">
                <div class="pi-num" :class="item.level">{{ i + 1 }}</div>
                <div class="pi-info">
                  <div class="pi-title-row">
                    <strong>{{ item.title }}</strong>
                    <span class="pi-badge" :class="item.level">{{ item.badge }}</span>
                  </div>
                  <p>{{ item.desc }}</p>
                </div>
              </div>
              <div class="pi-meta">
                <span class="pi-time">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  {{ item.time }}
                </span>
                <span class="pi-deduct">扣分：<strong>-{{ item.deduct }}</strong></span>
              </div>
            </div>
          </div>

          <!-- 当前选中问题的建议 -->
          <div v-if="selectedProblem !== null" class="quick-advice">
            <div class="qa-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <strong>当前建议</strong>
            <p>{{ problems[selectedProblem].recommend }}</p>
          </div>
        </div>

        <!-- 纠正建议（折叠面板） -->
        <div v-show="activeTab === 'advice'" class="section-card">
          <header class="sc-header">
            <div class="sc-header-icon success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div>
              <h3>纠正建议</h3>
              <p>针对 <strong>4</strong> 个问题，共 <strong>5</strong> 项训练</p>
            </div>
          </header>

          <div class="advice-accordion">
            <div v-for="(grp, gi) in adviceGroups" :key="gi" class="accordion-item">
              <button class="accordion-header" :class="{ open: openAccordion === gi }" @click="toggleAccordion(gi)">
                <span class="accordion-dot" :style="{ background: grp.color }" />
                <span class="accordion-title">{{ grp.label }}</span>
                <span class="accordion-count">{{ grp.items.length }} 项</span>
                <svg :class="['accordion-chevron', { open: openAccordion === gi }]" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              <div v-if="openAccordion === gi" class="accordion-body">
                <div v-for="(item, ii) in grp.items" :key="ii" class="advice-item">
                  <div class="ai-num">{{ ii + 1 }}</div>
                  <div class="ai-body">
                    <strong>{{ item.title }}</strong>
                    <p>{{ item.desc }}</p>
                    <div class="ai-prescription">
                      <span>{{ item.sets }}</span>
                      <span>{{ item.freq }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button class="btn-full-plan">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            查看完整纠正方案
          </button>
        </div>
      </aside>
    </section>

    <!-- ===== 底部三图 ===== -->
    <section class="charts-row">
      <div class="chart-card">
        <header class="chart-card-header">
          <h3>评分趋势</h3>
          <span class="chart-pill up">近 7 天 · 86</span>
        </header>
        <div ref="trendChartRef" class="chart-body" />
      </div>
      <div class="chart-card">
        <header class="chart-card-header">
          <h3>能力雷达图</h3>
          <span class="chart-pill">短板：关节活动度</span>
        </header>
        <div ref="radarChartRef" class="chart-body" />
        <div class="chart-footer">
          <span class="cf-badge good">优势：动作流畅度 88</span>
          <span class="cf-badge warn">短板：关节活动度 72</span>
        </div>
      </div>
      <div class="chart-card">
        <header class="chart-card-header">
          <h3>左右对称性</h3>
          <span class="chart-pill">左右对比</span>
        </header>
        <div ref="symmetryChartRef" class="chart-body" />
      </div>
    </section>

    <!-- ===== 底部操作 ===== -->
    <section class="bottom-actions">
      <button class="ba-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16"/></svg>
        重新评估
      </button>
      <button class="ba-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
        生成纠正计划
      </button>
      <button class="ba-btn" @click="router.push('/export')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        导出 PDF
      </button>
      <button class="ba-btn primary" @click="router.push('/reports')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        查看完整报告
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts/core";
import { BarChart, LineChart, RadarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent, RadarComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart, LineChart, RadarChart,
  GridComponent, LegendComponent, TooltipComponent, RadarComponent,
  CanvasRenderer
]);

const router = useRouter();

const trendChartRef = ref<HTMLDivElement | null>(null);
const radarChartRef = ref<HTMLDivElement | null>(null);
const symmetryChartRef = ref<HTMLDivElement | null>(null);
const chartInstances: echarts.ECharts[] = [];

const activeTab = ref<"problems" | "advice">("problems");
const selectedProblem = ref<number | null>(0);
const openAccordion = ref<number | null>(0);

const speeds = ["0.5x", "0.75x", "1.0x", "1.5x", "2.0x"];
const phases = ["准备阶段", "下蹲阶段", "底部停顿", "起身阶段", "结束阶段"];

const sideMetrics = [
  { label: "动作流畅度", value: 88, level: "良好", cls: "good", tip: "根据动作连贯性和停顿时间计算" },
  { label: "动作稳定性", value: 85, level: "良好", cls: "good", tip: "根据身体重心偏移幅度计算" },
  { label: "关节活动度", value: 72, level: "中等", cls: "warn", tip: "根据膝关节、髋关节和踝关节角度范围计算" },
  { label: "左右对称性", value: 78, level: "中等", cls: "warn", tip: "根据左右侧关节角度差异计算" },
  { label: "姿态控制力", value: 82, level: "良好", cls: "good", tip: "综合评估各关键点空间位置稳定性" },
];

const problems = [
  { title: "膝内扣", desc: "下蹲阶段双膝向内偏移，左膝偏移量 15°", level: "high", badge: "高风险", time: "00:12 - 00:18", deduct: 8, recommend: "弹力带侧向行走、臀中肌激活训练" },
  { title: "骨盆前倾", desc: "骨盆前倾角度 22°，超过正常范围", level: "medium", badge: "中风险", time: "00:08 - 00:15", deduct: 6, recommend: "骨盆后倾训练、核心强化" },
  { title: "重心偏移", desc: "重心偏向左侧 8%，左右受力不均衡", level: "low", badge: "低风险", time: "00:10 - 00:20", deduct: 5, recommend: "单腿平衡训练、重心控制练习" },
  { title: "肩部不对称", desc: "左右肩高度差 12mm，肩胛骨控制不足", level: "low", badge: "低风险", time: "00:05 - 00:22", deduct: 4, recommend: "肩部激活训练、肩胛稳定性练习" },
];

const adviceGroups = ref([
  { label: "膝内扣相关训练", color: "#ef4444", items: [
    { title: "弹力带侧向行走", desc: "强化髋外展肌群，改善膝内扣问题", sets: "3组 × 15次", freq: "每周3次" },
    { title: "臀中肌激活训练", desc: "激活臀中肌，增强髋关节外展力量", sets: "3组 × 12次", freq: "每周4次" },
  ]},
  { label: "骨盆前倾相关训练", color: "#f59e0b", items: [
    { title: "骨盆后倾训练", desc: "改善骨盆前倾，增强核心控制能力", sets: "3组 × 12次", freq: "每周3次" },
  ]},
  { label: "重心偏移相关训练", color: "#3b82f6", items: [
    { title: "单腿平衡训练", desc: "改善重心控制，增强下肢稳定性", sets: "3组 × 30秒", freq: "每周4次" },
  ]},
  { label: "肩部不对称相关训练", color: "#3b82f6", items: [
    { title: "肩部激活训练", desc: "改善肩部对称性，增强肩胛控制", sets: "3组 × 15次", freq: "每周3次" },
  ]},
]);

function toggleAccordion(gi: number) {
  openAccordion.value = openAccordion.value === gi ? null : gi;
}

function createChart(el: HTMLDivElement, option: echarts.EChartsCoreOption) {
  const chart = echarts.init(el);
  chart.setOption(option);
  chartInstances.push(chart);
}

function resizeCharts() {
  chartInstances.forEach((c) => c.resize());
}

onMounted(() => {
  if (trendChartRef.value) {
    createChart(trendChartRef.value, {
      color: ["#60a5fa"],
      grid: { left: 40, right: 14, top: 12, bottom: 28 },
      tooltip: { trigger: "axis", backgroundColor: "rgba(8,13,26,0.94)", borderColor: "#253047", textStyle: { color: "#e2e8f0" } },
      xAxis: { type: "category", boundaryGap: false, data: ["5/18", "5/19", "5/20", "5/21", "5/22", "5/23", "5/24"], axisLine: { lineStyle: { color: "#1e293b" } }, axisTick: { show: false }, axisLabel: { color: "#64748b", fontSize: 11 } },
      yAxis: { type: "value", min: 60, max: 100, interval: 10, splitLine: { lineStyle: { color: "rgba(30,41,59,0.6)", type: "dashed" } }, axisLabel: { color: "#64748b", fontSize: 11 } },
      series: [{ type: "line", smooth: true, symbolSize: 7, lineStyle: { width: 2.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(59,130,246,0.25)" }, { offset: 1, color: "rgba(59,130,246,0.02)" }]) }, data: [74, 78, 81, 79, 83, 84, 86] }]
    });
  }

  if (radarChartRef.value) {
    createChart(radarChartRef.value, {
      color: ["#60a5fa"],
      tooltip: { backgroundColor: "rgba(8,13,26,0.94)", borderColor: "#253047", textStyle: { color: "#e2e8f0" } },
      radar: { center: ["50%", "52%"], radius: "68%", indicator: [
        { name: "动作流畅度", max: 100 }, { name: "动作稳定性", max: 100 }, { name: "关节活动度", max: 100 }, { name: "左右对称性", max: 100 }, { name: "姿态控制力", max: 100 },
      ], axisName: { color: "#94a3b8", fontSize: 11 }, splitArea: { areaStyle: { color: ["rgba(15,23,42,0.5)", "rgba(8,13,26,0.8)"] } }, splitLine: { lineStyle: { color: "#1e293b" } }, axisLine: { lineStyle: { color: "#1e293b" } } },
      series: [{ type: "radar", data: [{ value: [88, 85, 72, 78, 82], name: "当前" }], areaStyle: { color: "rgba(59,130,246,0.2)" }, lineStyle: { color: "#60a5fa", width: 2 }, itemStyle: { color: "#3b82f6" }, symbolSize: 4 }]
    });
  }

  if (symmetryChartRef.value) {
    createChart(symmetryChartRef.value, {
      tooltip: { trigger: "axis", backgroundColor: "rgba(8,13,26,0.94)", borderColor: "#253047", textStyle: { color: "#e2e8f0" } },
      legend: { data: ["左侧", "右侧"], textStyle: { color: "#64748b", fontSize: 10 }, top: 0 },
      grid: { left: 40, right: 14, top: 26, bottom: 28 },
      xAxis: { type: "category", data: ["肩部", "腿部", "膝关节", "踝关节"], axisLine: { lineStyle: { color: "#1e293b" } }, axisTick: { show: false }, axisLabel: { color: "#64748b", fontSize: 11 } },
      yAxis: { type: "value", min: 0, max: 100, splitLine: { lineStyle: { color: "rgba(30,41,59,0.6)", type: "dashed" } }, axisLabel: { color: "#64748b", fontSize: 11 } },
      series: [
        { type: "bar", name: "左侧", data: [88, 82, 68, 75], color: "#3b82f6", barWidth: 14, itemStyle: { borderRadius: [3, 3, 0, 0] } },
        { type: "bar", name: "右侧", data: [92, 85, 60, 78], color: "#10b981", barWidth: 14, itemStyle: { borderRadius: [3, 3, 0, 0] } }
      ]
    });
  }

  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  chartInstances.forEach((c) => c.dispose());
});
</script>

<style scoped>
.sports-dashboard { display: grid; gap: 18px; max-width: 1560px; margin: 0 auto; }

/* ===== 顶部精简 ===== */
.top-header {
  display: grid; grid-template-columns: auto auto 1fr auto; align-items: center;
  gap: 28px; padding: 14px 24px;
  background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(30,41,59,0.92));
  border: 1px solid rgba(59,130,246,0.12); border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.th-left { display: flex; align-items: center; gap: 14px; }
.th-avatar {
  width: 46px; height: 46px; display: grid; place-items: center;
  border-radius: 11px; background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff; font-size: 18px; font-weight: 800;
}
.th-info strong { display: block; color: #f8fafc; font-size: 16px; }
.th-info p { margin: 3px 0 0; color: #64748b; font-size: 12px; }

.th-score { display: flex; align-items: center; gap: 10px; }
.th-score-label { color: #64748b; font-size: 11px; font-weight: 600; }
.th-score-value { display: flex; align-items: baseline; gap: 2px; }
.th-score-num { font-size: 30px; font-weight: 900; line-height: 1; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.th-score-unit { color: #64748b; font-size: 13px; }
.th-score-badge { padding: 2px 10px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.th-score-badge.good { background: rgba(16,185,129,0.15); color: #34d399; }

.th-compare { display: flex; align-items: center; gap: 8px; }
.th-compare-label { color: #64748b; font-size: 11px; }
.th-compare-value { display: inline-flex; align-items: center; gap: 3px; font-size: 20px; font-weight: 800; }
.th-compare-value.up { color: #34d399; }

.th-actions { justify-self: end; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 24px;
  border: none; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff; font-size: 14px; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 16px rgba(59,130,246,0.3);
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(59,130,246,0.4); transform: translateY(-1px); }

/* ===== 核心区域 58% / 42% ===== */
.core-row { display: grid; grid-template-columns: 1.38fr 1fr; gap: 18px; align-items: start; }

.main-panel {
  border-radius: 14px; overflow: hidden;
  background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98));
  border: 1px solid rgba(59,130,246,0.1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.panel-header {
  display: flex; align-items: center; padding: 12px 18px;
  border-bottom: 1px solid rgba(59,130,246,0.06);
  background: rgba(8,13,26,0.7);
}
.panel-left { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.panel-title-icon { display: flex; align-items: center; gap: 8px; }
.panel-title-icon svg { color: #60a5fa; }
.panel-title-icon h2 { margin: 0; font-size: 16px; color: #f8fafc; }
.phase-badge {
  display: inline-flex; align-items: center; gap: 6px; padding: 3px 12px;
  border-radius: 999px; background: rgba(59,130,246,0.1); color: #93c5fd; font-size: 12px;
}
.phase-badge strong { color: #f8fafc; }
.phase-dot { width: 7px; height: 7px; border-radius: 50%; }
.pulse-blue { background: #3b82f6; box-shadow: 0 0 10px rgba(59,130,246,0.5); }
.status-pill {
  display: inline-flex; align-items: center; gap: 5px; padding: 3px 12px;
  border-radius: 999px; font-size: 12px; font-weight: 600;
}
.status-pill.warn { background: rgba(245,158,11,0.12); color: #fbbf24; }

/* 横向指标条 */
.metric-strip {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(59,130,246,0.04);
  background: rgba(8,13,26,0.35);
}
.ms-item { cursor: help; display: grid; gap: 3px; }
.ms-label { color: #64748b; font-size: 11px; }
.ms-item strong { font-size: 15px; line-height: 1; }
.ms-item .good { color: #34d399; }
.ms-item .warn { color: #fbbf24; }
.ms-track { height: 3px; border-radius: 999px; background: rgba(30,41,59,0.6); overflow: hidden; }
.ms-track i { display: block; height: 100%; border-radius: inherit; }
.ms-track .good { background: linear-gradient(90deg, #10b981, #34d399); }
.ms-track .warn { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

/* 骨骼 */
.skel-area {
  position: relative; min-height: 400px;
  display: grid; place-items: center;
  overflow: hidden;
}
.skel-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(59,130,246,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.035) 1px, transparent 1px);
  background-size: 28px 28px;
}
.skel-stage-label {
  position: absolute; top: 10px; left: 14px; z-index: 5;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 8px;
  background: rgba(8,13,26,0.8); color: #93c5fd; font-size: 12px; font-weight: 600;
  border: 1px solid rgba(59,130,246,0.1);
}
.skel-layout { position: relative; z-index: 2; width: 100%; max-width: 220px; }
.pose-skeleton { width: 100%; height: auto; display: block; }

.score-card-overlay {
  position: absolute; bottom: 14px; left: 14px; z-index: 5;
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-radius: 10px;
  background: rgba(8,13,26,0.85);
  border: 1px solid rgba(59,130,246,0.1);
  backdrop-filter: blur(8px);
}
.score-ring-big {
  width: 56px; height: 56px; display: grid; place-items: center; align-content: center; gap: 1px;
  border-radius: 50%; flex-shrink: 0;
  background: radial-gradient(circle, rgba(8,13,26,0.9) 38%, transparent 39%), conic-gradient(#34d399 0 86%, rgba(255,255,255,0.04) 86% 100%);
  border: 2px solid rgba(52,211,153,0.2);
}
.score-ring-num { font-size: 18px; font-weight: 900; color: #34d399; line-height: 1; }
.score-ring-label { font-size: 7px; color: #64748b; }
.score-ring-meta { display: grid; gap: 5px; }
.score-ring-grade { display: inline-flex; width: fit-content; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.score-ring-grade.good { background: rgba(16,185,129,0.12); color: #34d399; }
.score-ring-issues { color: #94a3b8; font-size: 11px; line-height: 1.3; }
.score-ring-issues strong { color: #f87171; font-weight: 700; }
.score-ring-issues .sep { color: #475569; }

/* 视角切换横向 */
.view-strip {
  position: absolute; top: 10px; right: 14px; z-index: 5;
  display: flex; gap: 4px;
  padding: 4px; border-radius: 8px;
  background: rgba(8,13,26,0.75);
  border: 1px solid rgba(59,130,246,0.08);
}
.view-angle {
  padding: 4px 12px; border: none; border-radius: 6px;
  background: transparent; color: #475569;
  font-size: 11px; font-weight: 600; cursor: pointer;
}
.view-angle.active { background: rgba(59,130,246,0.15); color: #93c5fd; }
.view-angle:hover { color: #94a3b8; }
.view-angle.disabled { opacity: 0.35; cursor: not-allowed; }

/* 阶段流程 */
.phase-flow-bar {
  display: grid; gap: 12px; padding: 14px 18px;
  border-top: 1px solid rgba(59,130,246,0.06);
  background: rgba(8,13,26,0.7);
}
.phase-flow { display: flex; align-items: center; position: relative; }
.phase-step { display: flex; flex-direction: column; align-items: center; gap: 5px; flex: 1; text-align: center; position: relative; z-index: 2; }
.phase-circle {
  width: 24px; height: 24px; display: grid; place-items: center;
  border-radius: 50%; background: rgba(30,41,59,0.8); color: #64748b;
  font-size: 10px; font-weight: 700; border: 2px solid #334155;
}
.phase-step.done .phase-circle { background: rgba(16,185,129,0.2); border-color: #10b981; color: #34d399; }
.phase-step.active .phase-circle { background: rgba(59,130,246,0.2); border-color: #3b82f6; color: #93c5fd; box-shadow: 0 0 10px rgba(59,130,246,0.2); }
.phase-label { font-size: 10px; color: #64748b; font-weight: 500; }
.phase-step.active .phase-label { color: #93c5fd; }
.phase-now { padding: 1px 7px; border-radius: 999px; background: rgba(59,130,246,0.15); color: #60a5fa; font-size: 8px; font-weight: 700; }
.phase-connector { position: absolute; left: 0; right: 0; top: 12px; z-index: 1; height: 2px; margin: 0 calc(50% + 12px); background: #1e293b; border-radius: 999px; }
.phase-connector-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #3b82f6, #60a5fa); }

.play-controls { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 12px; }
.play-btn-small { width: 34px; height: 34px; display: grid; place-items: center; border: none; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; cursor: pointer; flex-shrink: 0; }
.timeline-mini { display: grid; gap: 3px; }
.tl-track { height: 4px; position: relative; border-radius: 999px; background: rgba(30,41,59,0.7); cursor: pointer; }
.tl-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #60a5fa, #a78bfa); }
.tl-thumb { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 11px; height: 11px; border-radius: 50%; background: #f8fafc; box-shadow: 0 2px 6px rgba(0,0,0,0.4), 0 0 0 3px rgba(59,130,246,0.15); }
.tl-labels { display: flex; justify-content: space-between; color: #475569; font-size: 10px; }
.speed-mini { display: flex; gap: 2px; }
.speed-mini button { padding: 3px 7px; border: 1px solid rgba(59,130,246,0.08); border-radius: 4px; background: transparent; color: #475569; font-size: 10px; font-weight: 600; cursor: pointer; }
.speed-mini button.active { border-color: rgba(59,130,246,0.25); background: rgba(59,130,246,0.08); color: #93c5fd; }

/* ===== 右侧 ===== */
.right-col { display: grid; gap: 14px; align-content: start; }

/* Tab */
.tab-bar { display: flex; gap: 6px; background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); border-radius: 12px; padding: 4px; }
.tab-btn {
  flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 16px; border: none; border-radius: 9px;
  background: transparent; color: #64748b; font-size: 13px; font-weight: 600; cursor: pointer;
}
.tab-btn.active { background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; box-shadow: 0 4px 12px rgba(59,130,246,0.25); }
.tab-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px;
  font-size: 10px; font-weight: 700;
  background: rgba(255,255,255,0.15); color: inherit;
}

/* 卡片 */
.section-card {
  padding: 18px; border-radius: 14px;
  background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98));
  border: 1px solid rgba(59,130,246,0.1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.sc-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid rgba(59,130,246,0.06); }
.sc-header-icon { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 8px; flex-shrink: 0; }
.sc-header-icon.danger { background: rgba(239,68,68,0.12); color: #f87171; }
.sc-header-icon.success { background: rgba(16,185,129,0.12); color: #34d399; }
.sc-header h3 { margin: 0; color: #f8fafc; font-size: 14px; }
.sc-header p { margin: 3px 0 0; color: #64748b; font-size: 12px; }
.sc-header p strong { color: #f1f5f9; }
.score-deduct { color: #f87171 !important; }

/* 问题列表 */
.problem-list { display: grid; gap: 8px; }
.problem-item { padding: 12px; border-radius: 9px; border: 1px solid transparent; cursor: pointer; }
.problem-item.high { background: rgba(239,68,68,0.05); border-color: rgba(239,68,68,0.12); }
.problem-item.medium { background: rgba(245,158,11,0.04); border-color: rgba(245,158,11,0.12); }
.problem-item.low { background: rgba(59,130,246,0.03); border-color: rgba(59,130,246,0.08); }
.problem-item.selected { outline: 1px solid rgba(59,130,246,0.3); }
.pi-top { display: flex; gap: 10px; align-items: flex-start; }
.pi-num { width: 22px; height: 22px; display: grid; place-items: center; border-radius: 50%; font-size: 10px; font-weight: 800; flex-shrink: 0; }
.pi-num.high { background: rgba(239,68,68,0.18); color: #f87171; }
.pi-num.medium { background: rgba(245,158,11,0.18); color: #fbbf24; }
.pi-num.low { background: rgba(59,130,246,0.12); color: #93c5fd; }
.pi-info { min-width: 0; }
.pi-title-row { display: flex; align-items: center; gap: 6px; }
.pi-title-row strong { color: #f8fafc; font-size: 13px; }
.pi-badge { padding: 1px 8px; border-radius: 999px; font-size: 9px; font-weight: 700; }
.pi-badge.high { background: rgba(239,68,68,0.14); color: #f87171; }
.pi-badge.medium { background: rgba(245,158,11,0.14); color: #fbbf24; }
.pi-badge.low { background: rgba(59,130,246,0.1); color: #93c5fd; }
.pi-info p { color: #64748b; font-size: 11px; margin: 4px 0 0; }
.pi-meta { display: flex; justify-content: space-between; gap: 10px; margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(59,130,246,0.04); }
.pi-meta span { display: inline-flex; align-items: center; gap: 3px; color: #64748b; font-size: 10px; }
.pi-meta strong { color: #f1f5f9; }
.pi-deduct strong { color: #f87171; }

/* 快捷建议 */
.quick-advice {
  display: flex; align-items: flex-start; gap: 10px;
  margin-top: 14px; padding: 12px;
  border-radius: 9px;
  background: rgba(16,185,129,0.04);
  border: 1px solid rgba(16,185,129,0.1);
}
.qa-icon {
  width: 28px; height: 28px; display: grid; place-items: center; flex-shrink: 0;
  border-radius: 7px; background: rgba(16,185,129,0.1); color: #34d399;
}
.quick-advice strong { color: #f8fafc; font-size: 12px; display: block; margin-bottom: 3px; }
.quick-advice p { color: #94a3b8; font-size: 11px; margin: 0; line-height: 1.4; }

/* 纠正建议折叠 */
.advice-accordion { display: grid; gap: 8px; }
.accordion-header {
  width: 100%; display: flex; align-items: center; gap: 10px;
  padding: 12px; border: 1px solid rgba(59,130,246,0.06); border-radius: 9px;
  background: rgba(8,13,26,0.4); color: #f8fafc;
  font-size: 13px; font-weight: 600; cursor: pointer; text-align: left;
}
.accordion-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.accordion-title { flex: 1; }
.accordion-count { color: #64748b; font-size: 11px; font-weight: 500; }
.accordion-chevron { transition: transform 0.2s; color: #64748b; }
.accordion-chevron.open { transform: rotate(180deg); }
.accordion-body { display: grid; gap: 8px; padding: 8px 0 0 14px; }

.advice-item { display: flex; gap: 10px; padding: 10px; border-radius: 8px; background: rgba(8,13,26,0.3); }
.ai-num { width: 22px; height: 22px; display: grid; place-items: center; border-radius: 6px; background: rgba(16,185,129,0.1); color: #34d399; font-size: 11px; font-weight: 800; flex-shrink: 0; }
.ai-body { display: grid; gap: 2px; }
.ai-body strong { color: #f8fafc; font-size: 12px; }
.ai-body p { color: #64748b; font-size: 11px; margin: 0; }
.ai-prescription { display: flex; gap: 14px; font-size: 11px; color: #94a3b8; margin-top: 4px; }

.btn-full-plan {
  width: 100%; margin-top: 12px;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px; border: 1px solid rgba(59,130,246,0.15); border-radius: 9px;
  background: rgba(59,130,246,0.06); color: #93c5fd;
  font-size: 12px; font-weight: 600; cursor: pointer;
}
.btn-full-plan:hover { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.3); }

/* ===== 底部三图 ===== */
.charts-row {
  display: grid; grid-template-columns: 1.6fr 1fr 1fr; gap: 18px;
}
.chart-card {
  padding: 16px; border-radius: 12px;
  background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98));
  border: 1px solid rgba(59,130,246,0.1);
  box-shadow: 0 6px 24px rgba(0,0,0,0.25);
}
.chart-card-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 6px; }
.chart-card-header h3 { color: #f8fafc; font-size: 13px; margin: 0; }
.chart-pill { padding: 2px 10px; border-radius: 999px; font-size: 10px; font-weight: 600; white-space: nowrap; }
.chart-pill.up { background: rgba(16,185,129,0.1); color: #34d399; }
.chart-pill { background: rgba(59,130,246,0.08); color: #93c5fd; }
.chart-body { width: 100%; height: 155px; }

.chart-footer { display: flex; gap: 10px; margin-top: 8px; }
.cf-badge { padding: 2px 10px; border-radius: 999px; font-size: 10px; font-weight: 600; }
.cf-badge.good { background: rgba(16,185,129,0.1); color: #34d399; }
.cf-badge.warn { background: rgba(245,158,11,0.1); color: #fbbf24; }

/* ===== 底部操作 ===== */
.bottom-actions {
  display: flex; justify-content: flex-end; gap: 12px; flex-wrap: wrap;
}
.ba-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 20px; border: 1px solid rgba(59,130,246,0.1);
  border-radius: 9px; background: rgba(15,23,42,0.8); color: #cbd5e1;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.ba-btn.primary {
  border: none; background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff; box-shadow: 0 4px 14px rgba(59,130,246,0.25);
}
.ba-btn:not(.primary):hover { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.2); color: #93c5fd; }

@media (max-width: 1380px) {
  .top-header { grid-template-columns: 1fr 1fr; gap: 14px; }
  .th-actions { justify-self: start; }
  .core-row { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 900px) {
  .top-header { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
  .metric-strip { grid-template-columns: repeat(3, 1fr); }
}
</style>
