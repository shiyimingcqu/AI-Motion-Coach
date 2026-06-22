<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Engineering Console</p>
        <h1>运动姿态评估与纠错系统</h1>
      </div>
      <button class="primary-button" @click="startDetection">启动检测</button>
    </header>

    <section class="metrics-grid">
      <MetricTile label="今日训练" value="42" hint="sessions" />
      <MetricTile label="平均得分" value="88" hint="+6 较上周" />
      <MetricTile label="有效动作" value="91%" hint="valid ratio" />
      <MetricTile label="任务队列" value="3" hint="pending jobs" />
    </section>

    <section class="operations-grid">
      <SkeletonCanvas />
      <div class="panel">
        <h2>系统链路</h2>
        <ul class="pipeline">
          <li>Vue3 Web 接入摄像头或视频上传</li>
          <li>FastAPI 网关处理鉴权、任务和报表</li>
          <li>Celery Worker 执行视频姿态分析</li>
          <li>MediaPipe 引擎输出关键点与骨架</li>
          <li>分析服务完成计数、评分和纠错</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";

const router = useRouter();

function startDetection() {
  router.push("/realtime");
}
</script>
