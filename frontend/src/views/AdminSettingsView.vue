<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">System Settings</p>
        <h1>系统管理设置</h1>
        <p class="subtle">配置注册、上传、分析和通知等系统级策略。</p>
      </div>
    </header>

    <section class="settings-stack">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Account</p>
            <h2>账号策略</h2>
          </div>
        </div>
        <label class="setting-row">
          <span>
            <strong>开放用户注册</strong>
            <small>关闭后只能由管理员创建账号</small>
          </span>
          <input v-model="systemSettings.registrationOpen" type="checkbox" />
        </label>
        <label class="setting-row">
          <span>
            <strong>默认新用户角色</strong>
            <small>普通训练用户为默认推荐</small>
          </span>
          <select v-model="systemSettings.defaultRole">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
        </label>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Analysis</p>
            <h2>分析策略</h2>
          </div>
        </div>
        <label class="setting-row">
          <span>
            <strong>视频上传大小限制</strong>
            <small>限制单个分析视频的最大体积</small>
          </span>
          <select v-model="systemSettings.uploadLimit">
            <option>100 MB</option>
            <option>300 MB</option>
            <option>500 MB</option>
          </select>
        </label>
        <label class="setting-row">
          <span>
            <strong>自动生成报告</strong>
            <small>训练完成后自动生成评估报告</small>
          </span>
          <input v-model="systemSettings.autoReport" type="checkbox" />
        </label>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";

const systemSettings = reactive({
  registrationOpen: true,
  defaultRole: "user",
  uploadLimit: "300 MB",
  autoReport: true
});
</script>
