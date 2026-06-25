<template>
  <div class="score-trends-page">
    <header class="section-page-header">
      <div>
        <h1>Score Trends / 分数趋势</h1>
        <p>Analyze performance trends and patterns over time</p>
      </div>
    </header>

    <section class="summary-card-grid">
      <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="progress-card">
      <header class="chart-card-header">
        <h2>7-Day Score Trend / 7天分数趋势</h2>
        <select><option>Last 7 Days</option></select>
      </header>
      <div class="wide-line-chart score-line-chart">
        <svg viewBox="0 0 1000 240" preserveAspectRatio="none">
          <polyline points="0,142 165,126 330,132 500,98 665,82 830,90 1000,62" fill="none" stroke="#4f7df3" stroke-width="3" />
          <g fill="#4f7df3">
            <circle cx="0" cy="142" r="6" /><circle cx="165" cy="126" r="6" /><circle cx="330" cy="132" r="6" />
            <circle cx="500" cy="98" r="6" /><circle cx="665" cy="82" r="6" /><circle cx="830" cy="90" r="6" /><circle cx="1000" cy="62" r="6" />
          </g>
        </svg>
        <div class="chart-axis"><span>Jun 19</span><span>Jun 20</span><span>Jun 21</span><span>Jun 22</span><span>Jun 23</span><span>Jun 24</span><span>Jun 25</span></div>
      </div>
    </section>

    <section class="score-two-grid">
      <article class="progress-card">
        <h2>Exercise Comparison / 动作对比</h2>
        <div class="comparison-bars">
          <span v-for="item in comparisons" :key="item.name" :style="{ height: `${item.score * 2.4}px` }"><b>{{ item.name }}</b></span>
        </div>
      </article>
      <article class="progress-card">
        <h2>Performance Categories / 表现类别</h2>
        <div class="radar-visual">
          <div class="radar-polygon" />
          <span class="r-top">Form / 动作形态</span>
          <span class="r-right">Balance / 平衡性</span>
          <span class="r-bottom-right">Range / 幅度</span>
          <span class="r-bottom">Speed / 速度</span>
          <span class="r-left">Stability / 稳定性</span>
          <span class="r-top-left">Alignment / 对齐</span>
        </div>
      </article>
    </section>

    <section class="progress-card">
      <h2>Detailed Score Breakdown / 详细分数分析</h2>
      <div class="score-breakdown-list">
        <article v-for="item in breakdown" :key="item.name">
          <header><strong>{{ item.name }}</strong><span>Current <b>{{ item.current }}</b> Change <b>+{{ item.change }}</b></span></header>
          <div class="detail-score-bar"><i :style="{ width: `${item.current}%` }" /></div>
          <footer><small>Previous: {{ item.previous }}</small><small>Average: {{ item.average }}</small></footer>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const stats = [
  { label: "Current Avg / 当前平均分", value: 88, hint: "+6 vs last week", tone: "" },
  { label: "Peak Score / 最高分", value: 95, hint: "June 23, 2026", tone: "" },
  { label: "Improvement / 改进率", value: "+12%", hint: "Last 30 days", tone: "tone-text-green" },
  { label: "Consistency / 一致性", value: "94%", hint: "Score variance", tone: "" }
];

const comparisons = [
  { name: "Squat", score: 82 },
  { name: "Push-up", score: 78 },
  { name: "Plank", score: 82 },
  { name: "Lunge", score: 76 },
  { name: "Burpee", score: 75 }
];

const breakdown = [
  { name: "Squat", current: 90, change: 8, previous: 82, average: 85 },
  { name: "Push-up", current: 85, change: 7, previous: 78, average: 80 }
];
</script>
