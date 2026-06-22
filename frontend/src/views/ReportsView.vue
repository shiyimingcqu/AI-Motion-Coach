<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Personal Report</p>
        <h1>个人训练报告</h1>
        <p class="subtle">汇总训练频次、平均分、有效动作率和主要错误。</p>
      </div>
      <button class="primary-button" type="button">
        <Download :size="18" />
        导出报告
      </button>
    </header>

    <section class="metrics-grid">
      <MetricTile label="本周训练次数" value="12" hint="较上周 +3" />
      <MetricTile label="平均分" value="86" hint="稳定提升" />
      <MetricTile label="有效动作率" value="88%" hint="目标 92%" />
      <MetricTile label="主要错误" value="下蹲深度不足" hint="32 次" />
    </section>

    <section class="dashboard-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Score Trend</p>
            <h2>平均分趋势</h2>
          </div>
        </div>
        <div class="line-chart">
          <span v-for="(score, index) in store.trend" :key="index" :style="{ '--point': `${100 - score}%` }">
            <b>{{ score }}</b>
          </span>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Errors</p>
            <h2>错误类型分布</h2>
          </div>
        </div>
        <div class="distribution-list">
          <div v-for="item in store.errorStats" :key="item.name">
            <span>{{ item.name }}</span>
            <strong>{{ item.value }} 次</strong>
            <i :style="{ width: `${item.value * 2}%` }"></i>
          </div>
        </div>
      </article>
    </section>

    <section class="dashboard-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Ability</p>
            <h2>动作能力雷达</h2>
          </div>
        </div>
        <div class="radar-card">
          <span style="--x: 50%; --y: 8%">下肢 88</span>
          <span style="--x: 86%; --y: 34%">上肢 78</span>
          <span style="--x: 72%; --y: 82%">心肺 92</span>
          <span style="--x: 22%; --y: 82%">核心 81</span>
          <span style="--x: 10%; --y: 34%">稳定 84</span>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Calendar</p>
            <h2>训练日历热力图</h2>
          </div>
        </div>
        <div class="heatmap">
          <span v-for="day in 35" :key="day" :class="`heat-${day % 5}`"></span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Download } from "lucide-vue-next";

import MetricTile from "../components/MetricTile.vue";
import { useTrainingStore } from "../stores/training";

const store = useTrainingStore();
</script>
