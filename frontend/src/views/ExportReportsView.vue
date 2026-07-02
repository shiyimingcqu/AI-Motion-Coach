<template>
  <div class="export-page">
    <header class="section-page-header">
      <div>
        <h1>Export Reports / 报告导出</h1>
        <p>Generate and download customized reports from your training data</p>
      </div>
    </header>

    <section class="summary-card-grid">
      <article class="summary-card">
        <span>Total Sessions / 总训练次数</span>
        <strong class="tone-text-blue">{{ summary.total_sessions }}</strong>
      </article>
      <article class="summary-card">
        <span>Avg Score / 平均分数</span>
        <strong class="tone-text-green">{{ summary.average_score }}</strong>
      </article>
      <article class="summary-card">
        <span>Total Duration / 总时长</span>
        <strong class="tone-text-purple">{{ summary.total_duration_minutes }} min</strong>
      </article>
      <article class="summary-card">
        <span>Valid Rate / 有效率</span>
        <strong class="tone-text-orange">{{ validRate }}</strong>
      </article>
    </section>

    <StateDisplay
      v-if="loading"
      type="loading"
      skeleton="cards"
      text="加载数据中..."
    />

    <section v-else class="export-layout">
      <div class="export-main">
        <article class="export-card">
          <h2>Export Format / 导出格式</h2>
          <div class="format-grid">
            <button
              v-for="fmt in formats"
              :key="fmt.value"
              type="button"
              class="format-option"
              :class="{ selected: selectedFormat === fmt.value }"
              @click="selectedFormat = fmt.value"
            >
              <span class="settings-icon" :class="fmt.color">
                <component :is="fmt.icon" :size="25" />
              </span>
              <div>
                <strong>{{ fmt.title }}</strong>
                <small>{{ fmt.desc }}</small>
              </div>
            </button>
          </div>
        </article>

        <article class="export-card">
          <h2>Report Configuration / 报告配置</h2>
          <label class="export-field">
            Date Range / 日期范围
            <div class="date-range-row">
              <input v-model="dateFrom" type="date" class="date-input" />
              <span>—</span>
              <input v-model="dateTo" type="date" class="date-input" />
            </div>
          </label>
          <div class="include-list">
            <span>Include Sections / 包含部分</span>
            <label v-for="item in sections" :key="item.key">
              <input v-model="item.enabled" type="checkbox" />
              {{ item.label }}
            </label>
          </div>
          <button
            class="primary-button"
            type="button"
            :disabled="exporting || summary.total_sessions === 0"
            @click="handleExport"
          >
            <Download :size="18" />
            {{ exporting ? '生成中...' : '下载报告' }}
          </button>
          <div v-if="error" class="error-message">{{ error }}</div>
        </article>
      </div>

      <aside class="quick-export-card">
        <h2>Quick Export / 快速导出</h2>
        <button class="quick-button" :class="{ active: selectedFormat === 'pdf' }" type="button" :disabled="summary.total_sessions === 0" @click="quickExport('pdf')">
          <FileText :size="20" />
          PDF 报告
        </button>
        <button class="quick-button" :class="{ active: selectedFormat === 'csv' }" type="button" :disabled="summary.total_sessions === 0" @click="quickExport('csv')">
          <FileSpreadsheet :size="20" />
          CSV 数据
        </button>

        <div class="recent-export-box">
          <h3>Summary Preview / 概览预览</h3>
          <div v-if="summary.total_sessions > 0" class="preview-stats">
            <div><span>Sessions</span><strong>{{ summary.total_sessions }}</strong></div>
            <div><span>Avg Score</span><strong>{{ summary.average_score }}</strong></div>
            <div><span>Duration</span><strong>{{ summary.total_duration_minutes }}m</strong></div>
            <div><span>Trend</span><strong>{{ trendDir }}</strong></div>
          </div>
          <div v-else class="preview-empty">
            <p>暂无训练数据，完成训练后可导出报告。</p>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Download, FileDown, FileSpreadsheet, FileText } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import { getPersonalReport } from "@/api/reports";

interface SectionItem {
  key: string;
  label: string;
  enabled: boolean;
}

const formats = [
  { value: "pdf", title: "PDF Document", desc: "Printable report with charts & stats", icon: FileText, color: "tone-red" },
  { value: "csv", title: "CSV File", desc: "Raw session data in spreadsheet format", icon: FileSpreadsheet, color: "tone-green" },
];

const sections = ref<SectionItem[]>([
  { key: "summary", label: "Score Summary / 评分摘要", enabled: true },
  { key: "sessions", label: "Session List / 训练记录列表", enabled: true },
  { key: "trend", label: "Score Trend / 评分趋势", enabled: true },
]);

const summary = ref({
  total_sessions: 0,
  average_score: 0,
  total_duration_minutes: 0,
  total_count: 0,
  valid_count: 0,
  error_count: 0,
  trend: [] as { date: string; score: number }[],
  recent_sessions: [] as { session_id: string; exercise: string; score: number; created_at: string }[],
});

const selectedFormat = ref("pdf");
const dateFrom = ref("");
const dateTo = ref("");
const loading = ref(true);
const exporting = ref(false);
const error = ref("");

const validRate = computed(() => {
  const t = summary.value.total_count;
  const v = summary.value.valid_count;
  if (t === 0) return "0%";
  return `${Math.round((v / t) * 100)}%`;
});

const trendDir = computed(() => {
  const t = summary.value.trend;
  if (t.length < 2) return "—";
  const last = t[t.length - 1].score;
  const first = t[0].score;
  return last >= first ? "↑ Improving" : "↓ Declining";
});

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function buildExportUrl(format: string): string {
  const params = new URLSearchParams();
  params.set("format", format);
  if (dateFrom.value) params.set("date_from", dateFrom.value);
  if (dateTo.value) params.set("date_to", dateTo.value);
  return `${API_BASE}/reports/export?${params.toString()}`;
}

function downloadFile(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.target = "_blank";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function handleExport() {
  exporting.value = true;
  error.value = "";
  try {
    const url = buildExportUrl(selectedFormat.value);
    const ext = selectedFormat.value;
    const dateStr = new Date().toISOString().slice(0, 10);
    downloadFile(url, `training_report_${dateStr}.${ext}`);
  } catch (err: any) {
    error.value = err.message || "导出失败";
  } finally {
    exporting.value = false;
  }
}

async function quickExport(format: string) {
  selectedFormat.value = format;
  await handleExport();
}

onMounted(async () => {
  try {
    const data = await getPersonalReport();
    summary.value = {
      total_sessions: data.total_sessions || 0,
      average_score: data.average_score || 0,
      total_duration_minutes: data.total_duration_minutes || 0,
      total_count: (data as any).total_count || 0,
      valid_count: (data as any).valid_count || 0,
      error_count: (data as any).error_count || 0,
      trend: (data as any).trend || (data as any).recent_trend || [],
      recent_sessions: (data as any).recent_sessions || [],
    };
  } catch {
    summary.value = {
      total_sessions: 0, average_score: 0, total_duration_minutes: 0,
      total_count: 0, valid_count: 0, error_count: 0,
      trend: [], recent_sessions: [],
    };
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.export-page { display: grid; gap: 24px; }

.summary-card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.summary-card { background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); border-radius: 12px; padding: 18px; display: grid; gap: 6px; }
.summary-card span { color: #64748b; font-size: 12px; }
.summary-card strong { font-size: 26px; font-weight: 900; }
.tone-text-blue { color: #60a5fa; }
.tone-text-green { color: #34d399; }
.tone-text-purple { color: #a78bfa; }
.tone-text-orange { color: #fbbf24; }

.export-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; align-items: start; }
.export-main { display: grid; gap: 20px; }

.export-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 18px; }
.export-card h2 { color: #f8fafc; font-size: 16px; margin: 0; }

.format-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.format-option { display: flex; align-items: flex-start; gap: 12px; padding: 16px; border: 1px solid rgba(59,130,246,0.08); border-radius: 10px; background: rgba(8,13,26,0.4); cursor: pointer; text-align: left; color: #94a3b8; }
.format-option:hover { border-color: rgba(59,130,246,0.2); background: rgba(59,130,246,0.04); }
.format-option.selected { border-color: rgba(59,130,246,0.3); background: rgba(59,130,246,0.06); }
.format-option strong { display: block; color: #f8fafc; font-size: 14px; margin-bottom: 2px; }
.format-option small { font-size: 11px; color: #64748b; }
.settings-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 10px; flex-shrink: 0; }
.tone-red { background: rgba(239,68,68,0.1); color: #f87171; }
.tone-green { background: rgba(16,185,129,0.1); color: #34d399; }

.export-field { display: grid; gap: 8px; color: #cbd5e1; font-size: 13px; font-weight: 600; }
.date-range-row { display: flex; align-items: center; gap: 8px; }
.date-input { flex: 1; padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; font-size: 14px; }

.include-list { display: grid; gap: 8px; }
.include-list > span { color: #cbd5e1; font-size: 13px; font-weight: 600; }
.include-list label { display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 13px; cursor: pointer; }
.include-list input { accent-color: #3b82f6; }

.primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 24px; border: none; border-radius: 9px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.primary-button:disabled { opacity: 0.5; cursor: not-allowed; }
.error-message { color: #f87171; background: rgba(239,68,68,0.08); padding: 10px 14px; border-radius: 8px; font-size: 13px; }

.quick-export-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 12px; align-content: start; }
.quick-export-card h2 { color: #f8fafc; font-size: 16px; margin: 0; }
.quick-button { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: 1px solid rgba(59,130,246,0.08); border-radius: 9px; background: rgba(8,13,26,0.4); color: #94a3b8; font-size: 13px; font-weight: 600; cursor: pointer; }
.quick-button.active { border-color: rgba(59,130,246,0.2); background: rgba(59,130,246,0.06); color: #93c5fd; }
.quick-button:disabled { opacity: 0.4; cursor: not-allowed; }
.quick-button:hover:not(:disabled) { background: rgba(59,130,246,0.04); border-color: rgba(59,130,246,0.2); }

.recent-export-box { margin-top: 12px; padding-top: 16px; border-top: 1px solid rgba(59,130,246,0.06); }
.recent-export-box h3 { color: #64748b; font-size: 12px; margin: 0 0 10px; }
.preview-stats { display: grid; gap: 8px; }
.preview-stats div { display: flex; justify-content: space-between; color: #94a3b8; font-size: 13px; }
.preview-stats strong { color: #f8fafc; }
.preview-empty p { color: #64748b; font-size: 13px; margin: 0; }

@media (max-width: 1000px) {
  .export-layout { grid-template-columns: 1fr; }
  .summary-card-grid { grid-template-columns: repeat(2, 1fr); }
  .format-grid { grid-template-columns: 1fr; }
}
</style>
