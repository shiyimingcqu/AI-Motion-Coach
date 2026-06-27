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

const reports = ref<AdminReport[]>([]);
const highlights = ref<string[]>([]);
const loading = ref(true);
const loadError = ref("");
const selectedReport = ref<AdminReport | null>(null);

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "-";
}

async function loadReports() {
  loading.value = true;
  loadError.value = "";

  try {
    const data = await apiGet<{ items: AdminReport[]; highlights: string[] }>("/admin/reports");
    reports.value = data.items ?? [];
    highlights.value = data.highlights ?? [];
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载报告失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadReports);
</script>
