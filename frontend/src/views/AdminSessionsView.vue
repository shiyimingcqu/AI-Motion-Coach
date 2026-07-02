<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Training Records</p>
        <h1>训练记录管理</h1>
        <p class="subtle">查看后端记录的训练会话、动作次数、错误数量和评分。</p>
      </div>
    </header>

    <section class="metrics-grid">
      <MetricTile label="记录总数" :value="sessions.length" hint="来自后端训练记录" />
      <MetricTile label="低分记录" :value="lowScoreCount" hint="低于 70 分" />
      <MetricTile label="有效动作率" :value="validRate" hint="全部记录平均" />
      <MetricTile label="平均评分" :value="averageScore" hint="全部记录平均" />
    </section>

    <section class="admin-table panel">
      <div class="admin-table-head admin-sessions-grid">
        <span>用户</span>
        <span>动作</span>
        <span>时间</span>
        <span>次数</span>
        <span>错误</span>
        <span>评分</span>
        <span>操作</span>
      </div>
      <div v-if="loading" class="loading-text">正在加载训练记录...</div>
      <div v-else-if="loadError" class="settings-status-message danger">{{ loadError }}</div>
      <template v-else>
        <div v-if="sessions.length === 0" class="loading-text">暂无训练记录。</div>
        <div v-for="session in sessions" :key="session.session_id" class="admin-table-row admin-sessions-grid">
          <strong>系统记录</strong>
          <span>{{ getExerciseName(session.exercise) }}</span>
          <span>{{ formatDate(session.created_at) }}</span>
          <span>{{ session.total_count }} 次</span>
          <span>{{ session.error_count }} 个</span>
          <span class="score-text" :class="{ warning: session.average_score < 75 }">{{ session.average_score }}</span>
          <button class="secondary-button" type="button" @click="selectedSession = session">查看详情</button>
        </div>
      </template>
    </section>

    <div v-if="selectedSession" class="modal-overlay" @click.self="selectedSession = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>训练记录详情</h3>
          <button class="close-button" type="button" aria-label="关闭" @click="selectedSession = null">
            <X :size="20" />
          </button>
        </div>
        <dl class="info-list info-list-readonly">
          <div>
            <dt>记录 ID</dt>
            <dd>{{ selectedSession.session_id }}</dd>
          </div>
          <div>
            <dt>动作</dt>
            <dd>{{ getExerciseName(selectedSession.exercise) }}</dd>
          </div>
          <div>
            <dt>训练时长</dt>
            <dd>{{ formatDuration(selectedSession.duration_seconds) }}</dd>
          </div>
          <div>
            <dt>总次数</dt>
            <dd>{{ selectedSession.total_count }}</dd>
          </div>
          <div>
            <dt>有效次数</dt>
            <dd>{{ selectedSession.valid_count }}</dd>
          </div>
          <div>
            <dt>错误次数</dt>
            <dd>{{ selectedSession.error_count }}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { X } from "lucide-vue-next";

import MetricTile from "../components/MetricTile.vue";
import { apiGet } from "../api/client";
import { exercises } from "../stores/training";

interface AdminSession {
  session_id: string;
  exercise: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  created_at: string;
}

const sessions = ref<AdminSession[]>([]);
const loading = ref(true);
const loadError = ref("");
const selectedSession = ref<AdminSession | null>(null);

const lowScoreCount = computed(() => sessions.value.filter((session) => session.average_score < 70).length);

const averageScore = computed(() => {
  if (sessions.value.length === 0) return "-";
  const total = sessions.value.reduce((sum, session) => sum + session.average_score, 0);
  return Math.round(total / sessions.value.length);
});

const validRate = computed(() => {
  const totalCount = sessions.value.reduce((sum, session) => sum + session.total_count, 0);
  if (totalCount === 0) return "-";
  const validCount = sessions.value.reduce((sum, session) => sum + session.valid_count, 0);
  return `${Math.round((validCount / totalCount) * 100)}%`;
});

function getExerciseName(exercise: string) {
  return exercises.find((item) => item.key === exercise)?.name ?? exercise;
}

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "-";
}

function formatDuration(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
}

async function loadSessions() {
  loading.value = true;
  loadError.value = "";

  try {
    const data = await apiGet<{ items: AdminSession[] }>("/admin/sessions");
    sessions.value = data.items ?? [];
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载训练记录失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadSessions);
</script>
