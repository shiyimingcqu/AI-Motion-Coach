<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Reports</p>
        <h1>评估报告管理</h1>
        <p class="subtle">查看后端根据训练记录生成的评估报告和重点风险。</p>
      </div>
      <button class="primary-button" type="button">
        <Download :size="18" />
        批量导出
      </button>
    </header>

    <!-- 用户筛选 -->
    <section class="panel filter-bar">
      <label class="filter-label">
        <span>筛选用户</span>
        <select v-model="selectedUserId" class="filter-select" @change="loadReports">
          <option :value="null">全部用户</option>
          <option v-for="u in userList" :key="u.id" :value="u.id">{{ u.username }}</option>
        </select>
      </label>
    </section>

    <section class="admin-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Report Queue</p>
            <h2>报告列表</h2>
          </div>
        </div>
        <div v-if="loading" class="loading-text">正在加载报告...</div>
        <div v-else-if="loadError" class="settings-status-message danger">{{ loadError }}</div>
        <div v-else class="admin-list">
          <div v-if="reports.length === 0" class="loading-text">暂无报告。</div>
          <div v-for="report in reports" :key="report.id" class="admin-list-row">
            <span class="status-pill" :class="report.status === '需关注' ? 'danger' : 'good'">{{ report.status }}</span>
            <div>
              <strong>{{ report.title }}</strong>
              <small>{{ report.user }} · {{ formatDate(report.created_at) }} · 平均分 {{ report.average_score }}</small>
            </div>
            <button class="secondary-button" type="button" @click="selectedReport = report">查看</button>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Highlights</p>
            <h2>重点关注</h2>
          </div>
        </div>
        <div class="admin-note-list">
          <p v-for="item in highlights" :key="item">{{ item }}</p>
        </div>
      </article>
    </section>

    <div v-if="selectedReport" class="modal-overlay" @click.self="selectedReport = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>报告详情</h3>
          <button class="close-button" type="button" aria-label="关闭" @click="selectedReport = null">
            <X :size="20" />
          </button>
        </div>
        <dl class="info-list info-list-readonly">
          <div>
            <dt>用户</dt>
            <dd>{{ selectedReport.user }}</dd>
          </div>
          <div>
            <dt>报告标题</dt>
            <dd>{{ selectedReport.title }}</dd>
          </div>
          <div>
            <dt>关联训练</dt>
            <dd>{{ selectedReport.session_id }}</dd>
          </div>
          <div>
            <dt>平均分</dt>
            <dd>{{ selectedReport.average_score }}</dd>
          </div>
          <div>
            <dt>错误次数</dt>
            <dd>{{ selectedReport.error_count }}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>{{ selectedReport.status }}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Download, X } from "lucide-vue-next";
import { apiGet } from "../api/client";

interface AdminReport {
  id: string;
  session_id: string;
  title: string;
  user: string;
  created_at: string;
  average_score: number;
  status: "已生成" | "需关注";
  error_count: number;
}

interface UserItem {
  id: number;
  username: string;
}

const reports = ref<AdminReport[]>([]);
const highlights = ref<string[]>([]);
const loading = ref(true);
const loadError = ref("");
const selectedReport = ref<AdminReport | null>(null);
const selectedUserId = ref<number | null>(null);
const userList = ref<UserItem[]>([]);

function formatDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("zh-CN");
}

async function loadUsers() {
  try {
    const data = await apiGet<{ items: UserItem[] }>("/admin/users");
    userList.value = data.items ?? [];
  } catch {
    // ignore
  }
}

async function loadReports() {
  loading.value = true;
  loadError.value = "";
  try {
    const query = selectedUserId.value !== null ? `?user_id=${selectedUserId.value}` : "";
    const data = await apiGet<{ items: AdminReport[]; highlights: string[] }>(`/admin/reports${query}`);
    reports.value = data.items ?? [];
    highlights.value = data.highlights ?? [];
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载报告失败";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadUsers();
  await loadReports();
});
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  margin-bottom: 0.5rem;
}
.filter-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff !important;
}
.filter-select {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  border: 2px solid #3b82f6;
  background: #fff;
  color: #16211b !important;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  min-width: 140px;
}
.filter-select option {
  color: #16211b;
  background: #fff;
}
</style>
