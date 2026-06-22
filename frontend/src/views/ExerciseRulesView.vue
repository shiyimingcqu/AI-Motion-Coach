<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Exercise Library</p>
        <h1>动作训练库与规则配置</h1>
        <p class="subtle">按动作类型、难度和支持方式筛选训练，并查看检测规则。</p>
      </div>
      <button class="primary-button" type="button">
        <Plus :size="18" />
        新增规则
      </button>
    </header>

    <section class="split-layout">
      <aside class="filter-panel">
        <h2>筛选栏</h2>
        <div class="filter-group">
          <strong>动作类型</strong>
          <button v-for="exercise in exercises" :key="exercise.key" type="button">{{ exercise.name }}</button>
        </div>
        <div class="filter-group">
          <strong>难度</strong>
          <button type="button">初级</button>
          <button type="button">中级</button>
          <button type="button">高级</button>
        </div>
        <div class="filter-group">
          <strong>支持方式</strong>
          <button type="button">摄像头实时检测</button>
          <button type="button">视频上传分析</button>
        </div>
      </aside>

      <section class="exercise-grid">
        <article v-for="exercise in exercises" :key="exercise.key" class="exercise-card">
          <div class="exercise-visual" :style="{ '--accent': exercise.accent }">
            <Dumbbell :size="34" />
          </div>
          <div>
            <span>{{ exercise.category }} · {{ exercise.level }}</span>
            <h2>{{ exercise.name }}</h2>
          </div>
          <p>推荐时长 {{ exercise.duration }}，支持 {{ exercise.modes.join(" / ") }}。</p>
          <div class="error-chips compact">
            <span v-for="error in exercise.errors" :key="error">{{ error }}</span>
          </div>
          <div class="card-actions">
            <button class="primary-button" type="button" @click="start(exercise.key)">开始训练</button>
            <button class="secondary-button" type="button">查看规则</button>
          </div>
        </article>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Dumbbell, Plus } from "lucide-vue-next";

import { exercises, useTrainingStore } from "../stores/training";

const router = useRouter();
const store = useTrainingStore();

function start(exercise: string) {
  store.setExercise(exercise);
  router.push("/realtime");
}
</script>
