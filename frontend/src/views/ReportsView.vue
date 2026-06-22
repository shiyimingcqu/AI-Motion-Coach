<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Analytics</p>
        <h1>统计报表</h1>
      </div>
    </header>

    <section class="metrics-grid">
      <MetricTile label="班级均分" value="88" hint="avg score" />
      <MetricTile label="训练人数" value="36" hint="students" />
      <MetricTile label="高频错误" value="下蹲深度不足" hint="top error" />
      <MetricTile label="导出报告" value="PDF" hint="ready" />
    </section>

    <section class="panel">
      <h2>趋势数据</h2>
      <pre>{{ scoreTrend }}</pre>
    </section>
  </div>
</template>

<script setup lang="ts">
import MetricTile from "../components/MetricTile.vue";
import { scoreTrend } from "../charts/reportData";
</script>
