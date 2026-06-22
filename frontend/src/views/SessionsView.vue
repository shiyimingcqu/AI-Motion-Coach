<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Activity Feed</p>
        <h1>训练记录</h1>
        <p class="subtle">按时间、动作、分数和错误情况筛选历史训练。</p>
      </div>
    </header>

    <section class="split-layout">
      <aside class="filter-panel">
        <h2>筛选条件</h2>
        <label>
          时间范围
          <select>
            <option>最近 7 天</option>
            <option>最近 30 天</option>
            <option>本学期</option>
          </select>
        </label>
        <label>
          动作类型
          <select>
            <option>全部动作</option>
            <option v-for="exercise in exercises" :key="exercise.key">{{ exercise.name }}</option>
          </select>
        </label>
        <label>
          分数范围
          <select>
            <option>全部分数</option>
            <option>90 分以上</option>
            <option>80-89 分</option>
            <option>80 分以下</option>
          </select>
        </label>
        <label class="check-row">
          <input type="checkbox" />
          仅看有错误记录
        </label>
      </aside>

      <section class="table-panel">
        <div v-if="loading" class="loading-text">正在加载训练记录...</div>
        <div v-else class="activity-list">
          <article v-for="session in visibleSessions" :key="session.session_id" class="activity-row">
            <div>
              <span class="date-chip">{{ formatDate(sessionDate(session)) }}</span>
              <h3>{{ getExerciseName(session.exercise) }}</h3>
              <p>{{ formatDuration(session.duration_seconds) }} · {{ session.total_count }} 次 · {{ session.error_count }} 个错误</p>
            </div>
            <div class="activity-score">
              <strong>{{ session.average_score }}</strong>
              <span>平均分</span>
            </div>
            <div class="activity-valid">
              <span>{{ session.valid_count }}/{{ session.total_count }}</span>
              <small>有效次数</small>
            </div>
            <button class="secondary-button" type="button">详情</button>
          </article>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { demoSessions, exercises, type Session } from "../stores/training";

type ApiSession = Session & { created_at?: string };

const sessions = ref<ApiSession[]>([]);
const loading = ref(true);

const visibleSessions = computed(() => (sessions.value.length > 0 ? sessions.value : demoSessions));

async function loadSessions() {
  try {
    const response = await fetch("http://localhost:8000/sessions");
    const data = await response.json();
    sessions.value = data.items || [];
  } catch (error) {
    console.warn("加载训练记录失败，使用本地演示数据。", error);
    sessions.value = [];
  } finally {
    loading.value = false;
  }
}

function getExerciseName(exercise: string): string {
  return exercises.find((item) => item.key === exercise)?.name ?? exercise;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
}

function formatDate(date?: string): string {
  if (!date) return "未知日期";
  return date.slice(5, 10);
}

function sessionDate(session: Session | ApiSession): string {
  return session.date || ("created_at" in session ? session.created_at ?? "" : "");
}

onMounted(loadSessions);
</script>
