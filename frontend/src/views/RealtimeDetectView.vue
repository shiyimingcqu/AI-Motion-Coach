<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime</p>
        <h1>摄像头实时检测</h1>
      </div>
      <button class="primary-button">连接摄像头</button>
    </header>

    <section class="operations-grid">
      <SkeletonCanvas />
      <div class="panel">
        <h2>实时反馈</h2>
        <div class="feedback-list">
          <MetricTile label="当前动作" value="深蹲" hint="squat" />
          <MetricTile label="次数" :value="store.count" hint="total count" />
          <MetricTile label="有效次数" :value="store.validCount" hint="valid count" />
          <MetricTile label="评分" :value="store.score" hint="score" />
        </div>
        <div class="alert-line">{{ store.errors[0] }}</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";
import { useTrainingStore } from "../stores/training";

const store = useTrainingStore();
</script>
