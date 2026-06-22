<template>
  <div class="page">
    <header class="page-header hero-header">
      <div>
        <p class="eyebrow">Summary</p>
        <h1>今天练得怎么样</h1>
        <p class="subtle">综合评分稳定上升，主要问题集中在下肢动作控制。</p>
      </div>
      <button class="primary-button" type="button" @click="startDetection">
        <Activity :size="18" />
        开始实时检测
      </button>
    </header>

    <section class="score-band">
      <div class="score-ring">
        <span>86</span>
        <small>综合评分</small>
      </div>
      <MetricTile label="今日训练" value="3 次" hint="比昨日 +1" />
      <MetricTile label="有效动作" value="120" hint="有效率 88%" />
      <MetricTile label="错误动作" value="18" hint="待纠正 2 类" />
    </section>

    <section class="action-grid">
      <button class="action-card" type="button" @click="startDetection">
        <Activity :size="22" />
        <strong>实时检测</strong>
        <span>打开摄像头开始训练</span>
      </button>
      <button class="action-card" type="button" @click="router.push('/upload')">
        <UploadCloud :size="22" />
        <strong>上传视频分析</strong>
        <span>提交已有训练视频</span>
      </button>
      <button class="action-card" type="button" @click="router.push('/reports')">
        <BarChart3 :size="22" />
        <strong>查看个人报告</strong>
        <span>查看趋势和错误分布</span>
      </button>
    </section>

    <section class="dashboard-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Recent</p>
            <h2>最近训练记录</h2>
          </div>
          <button class="text-button" type="button" @click="router.push('/sessions')">全部记录</button>
        </div>
        <div class="session-list">
          <div v-for="session in latestSessions" :key="session.session_id" class="session-item">
            <span>{{ exerciseName(session.exercise) }}</span>
            <strong>{{ session.average_score }} 分</strong>
            <small>{{ session.date }} · {{ session.valid_count }}/{{ session.total_count }} 有效</small>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Trend</p>
            <h2>本周评分趋势</h2>
          </div>
          <span class="status-pill good">+6 分</span>
        </div>
        <div class="mini-chart" aria-label="最近 7 天平均分趋势">
          <span v-for="(score, index) in store.trend" :key="index" :style="{ height: `${score - 48}%` }">
            <b>{{ score }}</b>
          </span>
        </div>
      </article>
    </section>

    <section class="panel error-panel">
      <div>
        <p class="eyebrow">Correction Focus</p>
        <h2>常见错误 Top 5</h2>
      </div>
      <div class="error-chips">
        <span v-for="item in store.errorStats" :key="item.name">{{ item.name }} · {{ item.value }} 次</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Activity, BarChart3, UploadCloud } from "lucide-vue-next";

import MetricTile from "../components/MetricTile.vue";
import { demoSessions, exercises, useTrainingStore } from "../stores/training";

const router = useRouter();
const store = useTrainingStore();
const latestSessions = computed(() => demoSessions.slice(0, 3));

function startDetection() {
  router.push("/realtime");
}

function exerciseName(key: string) {
  return exercises.find((item) => item.key === key)?.name ?? key;
}
</script>
