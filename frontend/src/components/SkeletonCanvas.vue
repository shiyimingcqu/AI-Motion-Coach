<template>
  <div class="skeleton-canvas">
    <div class="camera-grid"></div>
    <svg viewBox="0 0 320 420" aria-label="姿态骨架预览">
      <circle cx="160" cy="56" r="22" />
      <path d="M160 82 L122 138 L112 214" />
      <path d="M160 82 L198 138 L208 214" />
      <path d="M154 116 L132 218 L122 328" />
      <path d="M166 116 L188 218 L198 328" />
      <path d="M132 218 L188 218" />
      <path d="M122 328 L96 382" />
      <path d="M198 328 L226 382" />
      <circle v-for="point in points" :key="point" :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="7" />
    </svg>
    <div class="feedback-strip">
      <b>实时评分 86</b>
      <span>检测到下蹲深度不足</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const points = ["160,56", "122,138", "198,138", "112,214", "208,214", "132,218", "188,218", "122,328", "198,328"];
</script>
