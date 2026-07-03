<template>
  <div class="export-page">
    <header class="section-page-header">
      <div>
        <h1>Export Reports / 报告导出</h1>
        <p>按时间范围与动作类型导出综合训练评估 PDF/CSV 报告</p>
      </div>
    </header>

    <section class="summary-card-grid">
      <article class="summary-card">
        <span>筛选训练次数</span>
        <strong class="tone-text-blue">{{ summary.total_sessions }}</strong>
      </article>
      <article class="summary-card">
        <span>平均分数</span>
        <strong class="tone-text-green">{{ summary.average_score }}</strong>
      </article>
      <article class="summary-card">
        <span>总时长</span>
        <strong class="tone-text-purple">{{ summary.total_duration_minutes }} min</strong>
      </article>
      <article class="summary-card">
        <span>总卡路里</span>
        <strong class="tone-text-orange">{{ summary.total_calories ?? 0 }} kcal</strong>
      </article>
    </section>

    <StateDisplay v-if="loading" type="loading" skeleton="card" text="加载数据中..." />

    <section v-else class="export-layout">
      <div class="export-main">
        <article class="export-card">
          <h2>导出格式</h2>
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
          <h2>报告筛选配置</h2>

          <label class="export-field">
            时间范围
            <select v-model="rangePreset" @change="applyRangePreset">
              <option value="today">今天</option>
              <option value="7d">近 7 天</option>
              <option value="all">全部记录</option>
              <option value="custom">自定义日期</option>
            </select>
          </label>

          <label v-if="rangePreset === 'custom'" class="export-field">
            自定义日期
            <div class="date-range-row">
              <input v-model="dateFrom" type="date" class="date-input" @change="refreshPreview" />
              <span>—</span>
              <input v-model="dateTo" type="date" class="date-input" @change="refreshPreview" />
            </div>
          </label>

          <label class="export-field">
            动作类型
            <select v-model="exerciseFilter" @change="refreshPreview">
              <option value="">全部动作</option>
              <option v-for="ex in EXERCISE_OPTIONS" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
            </select>
          </label>

          <div class="include-list">
            <span>PDF 报告包含内容</span>
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
            {{ exporting ? "生成中..." : "下载综合报告" }}
          </button>
          <div v-if="error" class="error-message">{{ error }}</div>
        </article>
      </div>

      <aside class="quick-export-card">
        <h2>快速导出</h2>
        <button class="quick-button" type="button" :disabled="summary.total_sessions === 0" @click="quickExport('pdf', '7d')">
          <FileText :size="20" /> 近7天 PDF
        </button>
        <button class="quick-button" type="button" :disabled="summary.total_sessions === 0" @click="quickExport('pdf', 'all')">
          <FileText :size="20" /> 全部 PDF
        </button>
        <button class="quick-button" type="button" :disabled="summary.total_sessions === 0" @click="quickExport('csv', 'all')">
          <FileSpreadsheet :size="20" /> 全部 CSV
        </button>

        <div class="recent-export-box">
          <h3>预览说明</h3>
          <p class="preview-desc">
            PDF 报告将综合包含：训练概览、图表分析、训练记录明细、分项评估、纠错建议与教练指导，内容来源于实时检测与视频分析的评估数据。
          </p>
          <div v-if="summary.total_sessions > 0" class="preview-stats">
            <div><span>范围</span><strong>{{ rangeLabel }}</strong></div>
            <div><span>动作</span><strong>{{ exerciseLabel }}</strong></div>
            <div><span>训练次数</span><strong>{{ summary.total_sessions }}</strong></div>
            <div><span>均分</span><strong>{{ summary.average_score }}</strong></div>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Download, FileSpreadsheet, FileText } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import { getPersonalReport, exportReport, downloadReport } from "@/api/reports";

const EXERCISE_OPTIONS = [
  { key: "squat", name: "深蹲" },
  { key: "push_up", name: "俯卧撑" },
  { key: "jumping_jack", name: "开合跳" },
  { key: "plank", name: "平板支撑" },
];

const formats = [
  { value: "pdf", title: "PDF 综合报告", desc: "含图表、评估、纠错建议的完整报告", icon: FileText, color: "tone-red" },
  { value: "csv", title: "CSV 数据", desc: "训练记录原始数据表格", icon: FileSpreadsheet, color: "tone-green" },
];

const sections = ref([
  { key: "summary", label: "训练概览与统计", enabled: true },
  { key: "charts", label: "图表分析（趋势/卡路里/雷达）", enabled: true },
  { key: "sessions", label: "训练记录明细", enabled: true },
  { key: "evaluation", label: "分项评估与维度评分", enabled: true },
  { key: "feedback", label: "纠错建议与训练指导", enabled: true },
]);

const summary = ref({
  total_sessions: 0,
  average_score: 0,
  total_duration_minutes: 0,
  total_calories: 0,
  total_count: 0,
  valid_count: 0,
  error_count: 0,
  trend: [] as { date: string; score: number }[],
});

const selectedFormat = ref("pdf");
const rangePreset = ref("7d");
const dateFrom = ref("");
const dateTo = ref("");
const exerciseFilter = ref("");
const loading = ref(true);
const exporting = ref(false);
const error = ref("");

const rangeLabel = computed(() => {
  if (rangePreset.value === "today") return "今天";
  if (rangePreset.value === "7d") return "近 7 天";
  if (rangePreset.value === "all") return "全部";
  return `${dateFrom.value || "—"} ~ ${dateTo.value || "—"}`;
});

const exerciseLabel = computed(() =>
  exerciseFilter.value
    ? EXERCISE_OPTIONS.find((e) => e.key === exerciseFilter.value)?.name ?? exerciseFilter.value
    : "全部动作",
);

function applyRangePreset() {
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  if (rangePreset.value === "today") {
    dateFrom.value = todayStr;
    dateTo.value = todayStr;
  } else if (rangePreset.value === "7d") {
    const from = new Date(today);
    from.setDate(from.getDate() - 6);
    dateFrom.value = from.toISOString().slice(0, 10);
    dateTo.value = todayStr;
  } else if (rangePreset.value === "all") {
    dateFrom.value = "";
    dateTo.value = "";
  }
  refreshPreview();
}

async function refreshPreview() {
  try {
    summary.value = await getPersonalReport({
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      exercise: exerciseFilter.value || undefined,
    });
  } catch {
    summary.value.total_sessions = 0;
  }
}

async function handleExport() {
  exporting.value = true;
  error.value = "";
  try {
    const blob = await exportReport(selectedFormat.value as "pdf" | "csv", {
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      exercise: exerciseFilter.value || undefined,
    });
    downloadReport(blob, selectedFormat.value as "pdf" | "csv");
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "导出失败";
  } finally {
    exporting.value = false;
  }
}

async function quickExport(format: "pdf" | "csv", range: "7d" | "all") {
  rangePreset.value = range;
  applyRangePreset();
  selectedFormat.value = format;
  await handleExport();
}

onMounted(async () => {
  applyRangePreset();
  loading.value = false;
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
.export-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; }
.export-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 18px; }
.export-card h2 { color: #f8fafc; font-size: 16px; margin: 0; }
.format-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.format-option { display: flex; gap: 12px; padding: 16px; border: 1px solid rgba(59,130,246,0.08); border-radius: 10px; background: rgba(8,13,26,0.4); cursor: pointer; text-align: left; color: #94a3b8; }
.format-option.selected { border-color: rgba(59,130,246,0.3); background: rgba(59,130,246,0.06); }
.export-field { display: grid; gap: 8px; color: #cbd5e1; font-size: 13px; font-weight: 600; }
.export-field select, .date-input { padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; }
.date-range-row { display: flex; align-items: center; gap: 8px; }
.include-list { display: grid; gap: 8px; }
.include-list label { display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 13px; }
.primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 24px; border: none; border-radius: 9px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; font-weight: 700; cursor: pointer; }
.primary-button:disabled { opacity: 0.5; cursor: not-allowed; }
.error-message { color: #f87171; font-size: 13px; }
.quick-export-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 12px; }
.quick-button { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: 1px solid rgba(59,130,246,0.08); border-radius: 9px; background: rgba(8,13,26,0.4); color: #94a3b8; cursor: pointer; }
.preview-desc { color: #64748b; font-size: 12px; line-height: 1.6; margin: 0 0 12px; }
.preview-stats div { display: flex; justify-content: space-between; color: #94a3b8; font-size: 13px; margin-bottom: 6px; }
.preview-stats strong { color: #f8fafc; }
@media (max-width: 1000px) { .export-layout, .summary-card-grid { grid-template-columns: 1fr; } }
</style>
