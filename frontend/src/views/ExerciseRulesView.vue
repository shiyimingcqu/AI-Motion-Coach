<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Rules</p>
        <h1>动作规则配置</h1>
      </div>
      <button class="primary-button">新增规则</button>
    </header>

    <section class="rules-grid">
      <article v-for="rule in rules" :key="rule.key" class="rule-card">
        <strong>{{ rule.name }}</strong>
        <span>{{ rule.description }}</span>
        <small>{{ rule.metrics }}</small>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
const rules = [
  { key: "squat", name: "深蹲", description: "下蹲深度、膝盖方向、躯干稳定", metrics: "count / score / depth_ratio" },
  { key: "push_up", name: "俯卧撑", description: "屈臂幅度、手臂伸直、身体直线", metrics: "count / valid_count / score" },
  { key: "jumping_jack", name: "开合跳", description: "手脚开合幅度与节奏", metrics: "count / rhythm / score" },
  { key: "plank", name: "平板支撑", description: "髋部高度和支撑时长", metrics: "duration / error_count / score" }
];
</script>
