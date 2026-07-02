<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Template Management</p>
        <h1>模板管理</h1>
        <p class="subtle">管理标准动作模板、版本和启用状态。</p>
      </div>
      <button class="primary-button" type="button">上传模板</button>
    </header>

    <section class="admin-table panel">
      <div class="admin-table-head admin-templates-grid">
        <span>模板</span>
        <span>动作</span>
        <span>视角</span>
        <span>版本</span>
        <span>状态</span>
        <span>操作</span>
      </div>
      <div v-for="template in templates" :key="template.name" class="admin-table-row admin-templates-grid">
        <div>
          <strong>{{ template.name }}</strong>
          <small>{{ template.frames }} 有效帧</small>
        </div>
        <span>{{ template.exercise }}</span>
        <span>{{ template.view }}</span>
        <span>{{ template.version }}</span>
        <span class="status-pill" :class="template.active ? 'good' : 'idle'">
          {{ template.active ? "使用中" : "停用" }}
        </span>
        <div class="admin-row-actions">
          <button class="secondary-button" type="button">预览</button>
          <button class="text-button" type="button">{{ template.active ? "停用" : "启用" }}</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const templates = [
  { name: "标准侧面深蹲", exercise: "深蹲", view: "侧面", version: "v1", frames: 128, active: true },
  { name: "标准正面深蹲", exercise: "深蹲", view: "正面", version: "v1", frames: 96, active: false },
  { name: "俯卧撑基础模板", exercise: "俯卧撑", view: "侧面", version: "v0.8", frames: 84, active: false }
];
</script>
