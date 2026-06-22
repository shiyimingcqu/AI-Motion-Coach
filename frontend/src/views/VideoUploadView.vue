<template>
  <div class="page narrow">
    <header class="page-header">
      <div>
        <p class="eyebrow">Async Analysis</p>
        <h1>视频上传分析</h1>
      </div>
    </header>

    <section class="upload-zone">
      <UploadCloud :size="42" />
      <strong>拖入训练视频或点击选择</strong>
      <span>上传后进入 Celery 队列，Worker 后台分析并生成结果视频。</span>
      <button class="primary-button">选择视频</button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { UploadCloud } from "lucide-vue-next";
</script>
