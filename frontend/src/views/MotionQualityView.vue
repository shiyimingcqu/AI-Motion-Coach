<template>
  <div class="quality-page">
    <header class="section-page-header">
      <div>
        <h1>Motion Quality Metrics / 动作质量指标</h1>
        <p>Detailed biomechanical analysis and quality indicators</p>
      </div>
    </header>

    <section class="quality-hero-grid">
      <article class="quality-hero green-gradient"><Activity :size="34" /><span>Overall Quality</span><strong>91%</strong></article>
      <article class="quality-hero blue-gradient"><TrendingUp :size="34" /><span>Improvement</span><strong>+8%</strong></article>
      <article class="quality-hero orange-gradient"><AlertTriangle :size="34" /><span>Issues Found</span><strong>2</strong></article>
    </section>

    <section class="progress-card quality-metrics-card">
      <h2>Quality Metrics Overview / 质量指标概览</h2>
      <div class="quality-list">
        <article v-for="metric in metrics" :key="metric.name">
          <header>
            <div>
              <strong>{{ metric.name }}</strong>
              <p>{{ metric.desc }}</p>
            </div>
            <span :class="metric.status">{{ metric.status }}</span>
          </header>
          <div class="quality-meta">
            <small>Current: {{ metric.current }}%</small>
            <small>Target: {{ metric.target }}%</small>
          </div>
          <div class="quality-bar">
            <i :class="{ green: metric.current >= metric.target }" :style="{ width: `${metric.current}%` }" />
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Activity, AlertTriangle, TrendingUp } from "lucide-vue-next";

const metrics = [
  { name: "Joint Angles / 关节角度", desc: "Knee and elbow angles within optimal range", current: 94, target: 95, status: "good" },
  { name: "Movement Speed / 运动速度", desc: "Slightly slower than recommended tempo", current: 88, target: 90, status: "fair" },
  { name: "Range of Motion / 运动幅度", desc: "Excellent full range achievement", current: 92, target: 90, status: "excellent" },
  { name: "Stability Index / 稳定性指数", desc: "Minor balance fluctuations detected", current: 85, target: 88, status: "fair" },
  { name: "Symmetry / 对称性", desc: "Good left-right balance", current: 91, target: 92, status: "good" },
  { name: "Posture Alignment / 姿态对齐", desc: "Excellent spine and shoulder alignment", current: 96, target: 95, status: "excellent" }
];
</script>
