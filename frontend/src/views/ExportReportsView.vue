<template>
  <div class="export-page export-typography">
    <header class="section-page-header">
      <div>
        <h1>Export Reports / 报告导出</h1>
        <p>按时间范围导出综合报告，或勾选单次训练记录生成独立评估报告</p>
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

    <StateDisplay v-if="loading" type="loading" skeleton="cards" text="加载数据中..." />

    <template v-else>
      <section class="export-layout">
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
            <h2>综合报告筛选</h2>

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
                <input v-model="dateFrom" type="date" class="date-input" @change="refreshData" />
                <span>—</span>
                <input v-model="dateTo" type="date" class="date-input" @change="refreshData" />
              </div>
            </label>

            <label class="export-field">
              动作类型
              <select v-model="exerciseFilter" @change="refreshData">
                <option value="">全部动作</option>
                <option v-for="ex in EXERCISE_OPTIONS" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
              </select>
            </label>

            <button
              class="primary-button"
              type="button"
              :disabled="exporting || summary.total_sessions === 0"
              @click="handleBulkExport"
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
              综合 PDF 包含训练概览、图表分析、训练记录明细、分项评估与纠错建议。
              下方训练记录可单独勾选，生成每次训练的独立评估报告。
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

      <section class="records-section">
        <div class="records-header">
          <div>
            <h2>训练记录</h2>
            <p>勾选记录后可批量导出单次评估报告，也可查看详情或单独下载</p>
          </div>
          <div class="records-actions">
            <button class="ghost-button" type="button" :disabled="filteredReports.length === 0" @click="selectAllVisible">
              全选当前列表
            </button>
            <button class="ghost-button" type="button" :disabled="selectedIds.size === 0" @click="clearSelection">
              清空选择
            </button>
            <button
              class="primary-button compact"
              type="button"
              :disabled="selectedIds.size === 0 || exportingSelected"
              @click="exportSelectedSessions"
            >
              <Download :size="16" />
              {{ exportingSelected ? "导出中..." : `导出所选报告 (${selectedIds.size})` }}
            </button>
          </div>
        </div>

        <section class="filter-card report-filter-card">
          <label class="session-search">
            <Filter :size="18" />
            <input v-model="keyword" type="search" placeholder="搜索训练记录..." />
          </label>
          <select v-model="sortOrder">
            <option value="desc">最新优先</option>
            <option value="asc">最早优先</option>
          </select>
        </section>

        <section class="report-table-card">
          <StateDisplay v-if="recordsLoading" type="loading" skeleton="table" :skeleton-rows="5" text="正在加载训练记录..." />
          <StateDisplay v-else-if="filteredReports.length === 0" type="empty" title="暂无训练记录" text="完成训练后，系统将自动生成评估报告" />
          <table v-else class="report-table">
            <thead>
              <tr>
                <th class="col-check">
                  <input type="checkbox" :checked="allVisibleSelected" @change="toggleSelectAllVisible" />
                </th>
                <th>报告名称</th>
                <th>动作</th>
                <th>日期</th>
                <th>评分</th>
                <th>等级</th>
                <th>卡路里</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in filteredReports" :key="report.id" :class="{ selected: selectedIds.has(report.session_id) }">
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedIds.has(report.session_id)"
                    @change="toggleSelect(report.session_id)"
                  />
                </td>
                <td>
                  <div class="report-name-cell">
                    <span><FileText :size="18" /></span>
                    <div>
                      <strong>{{ report.title }}</strong>
                      <small>{{ report.subtitle }}</small>
                    </div>
                  </div>
                </td>
                <td>{{ report.exercise_name || report.exercise }}</td>
                <td>{{ report.date }}</td>
                <td>
                  <div class="score-progress">
                    <i :class="report.average_score >= 90 ? 'progress-green' : 'progress-blue'" :style="{ width: report.average_score + '%' }" />
                    <strong>{{ report.average_score }}</strong>
                  </div>
                </td>
                <td><span class="grade-pill" :class="gradeClass(report.grade)">{{ report.grade_label || '—' }}</span></td>
                <td>{{ report.calories?.toFixed(1) ?? 0 }} kcal</td>
                <td>
                  <div class="report-actions">
                    <button type="button" title="查看详情" @click="openDetail(report.session_id)">
                      <Eye :size="16" />
                    </button>
                    <button type="button" title="下载单次报告" @click="downloadSingle(report)">
                      <Download :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </section>
    </template>

    <div v-if="showDetail" class="modal-overlay" @click.self="closeDetail">
      <div class="modal-content report-detail-modal">
        <div class="modal-header">
          <div>
            <h3>{{ detail?.exercise_name }} 评估报告</h3>
            <p>{{ detail?.created_at?.slice(0, 10) }} · {{ detail?.calories_burned }} kcal</p>
          </div>
          <button class="close-button" type="button" @click="closeDetail"><X :size="20" /></button>
        </div>

        <StateDisplay v-if="detailLoading" type="loading" text="加载报告详情..." />

        <template v-else-if="detail">
          <div class="detail-score-row">
            <div class="score-circle">
              <strong>{{ detail.average_score }}</strong>
              <span>综合评分</span>
            </div>
            <div class="grade-badge" :class="gradeClass(detail.evaluation.grade)">
              {{ detail.evaluation.grade_label }}
            </div>
            <div class="detail-metrics">
              <div><span>有效次数</span><strong>{{ detail.valid_count }}/{{ detail.total_count }}</strong></div>
              <div><span>错误次数</span><strong>{{ detail.error_count }}</strong></div>
              <div><span>训练时长</span><strong>{{ detail.evaluation.duration_minutes }} min</strong></div>
              <div><span>卡路里</span><strong>{{ detail.calories_burned }} kcal</strong></div>
            </div>
          </div>

          <p class="eval-summary">{{ detail.evaluation.summary }}</p>

          <div class="detail-charts">
            <div ref="detailRadarRef" class="detail-chart" />
            <div ref="detailRepRef" class="detail-chart" />
          </div>

          <div class="eval-columns">
            <article>
              <h4>优势</h4>
              <ul><li v-for="item in detail.evaluation.strengths" :key="item">{{ item }}</li></ul>
            </article>
            <article>
              <h4>待改进</h4>
              <ul><li v-for="item in detail.evaluation.weaknesses" :key="item">{{ item }}</li></ul>
            </article>
            <article>
              <h4>训练建议</h4>
              <ul><li v-for="item in detail.evaluation.recommendations" :key="item">{{ item }}</li></ul>
            </article>
          </div>

          <button class="primary-button modal-export-btn" type="button" @click="downloadSingleFromDetail">
            <Download :size="16" /> 下载本次评估报告
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import * as echarts from "echarts";
import { Download, Eye, FileSpreadsheet, FileText, Filter, X } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import {
  getPersonalReport,
  getReportDetail,
  getReports,
  exportReport,
  exportSessionReport,
  downloadReport,
  downloadSessionReport,
  type ReportDetail,
  type ReportItem,
} from "@/api/reports";

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

const route = useRoute();
const reports = ref<ReportItem[]>([]);
const summary = ref({
  total_sessions: 0,
  average_score: 0,
  total_duration_minutes: 0,
  total_calories: 0,
});

const selectedFormat = ref("pdf");
const rangePreset = ref("7d");
const dateFrom = ref("");
const dateTo = ref("");
const exerciseFilter = ref("");
const loading = ref(true);
const recordsLoading = ref(false);
const exporting = ref(false);
const exportingSelected = ref(false);
const error = ref("");
const keyword = ref("");
const sortOrder = ref("desc");
const selectedIds = ref<Set<string>>(new Set());

const showDetail = ref(false);
const detailLoading = ref(false);
const detail = ref<ReportDetail | null>(null);
const detailRadarRef = ref<HTMLElement | null>(null);
const detailRepRef = ref<HTMLElement | null>(null);
let detailCharts: echarts.ECharts[] = [];

const queryParams = computed(() => ({
  date_from: dateFrom.value || undefined,
  date_to: dateTo.value || undefined,
  exercise: exerciseFilter.value || undefined,
}));

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

const filteredReports = computed(() => {
  let list = [...reports.value];
  const query = keyword.value.trim().toLowerCase();
  if (query) {
    list = list.filter(
      (r) =>
        r.title.toLowerCase().includes(query) ||
        r.subtitle.toLowerCase().includes(query) ||
        (r.exercise_name || r.exercise).toLowerCase().includes(query),
    );
  }
  list.sort((a, b) => {
    const diff = a.date.localeCompare(b.date);
    return sortOrder.value === "desc" ? -diff : diff;
  });
  return list;
});

const allVisibleSelected = computed(() =>
  filteredReports.value.length > 0 &&
  filteredReports.value.every((r) => selectedIds.value.has(r.session_id)),
);

function gradeClass(grade?: string) {
  if (grade === "A") return "grade-a";
  if (grade === "B") return "grade-b";
  if (grade === "C") return "grade-c";
  return "grade-d";
}

async function applyRangePreset() {
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
  await refreshData();
}

async function refreshData() {
  recordsLoading.value = true;
  error.value = "";
  try {
    const [personalRes, reportListRes] = await Promise.all([
      getPersonalReport(queryParams.value),
      getReports(queryParams.value),
    ]);
    summary.value = personalRes;
    reports.value = reportListRes.items;
    const visibleIds = new Set(filteredReports.value.map((r) => r.session_id));
    selectedIds.value = new Set(
      [...selectedIds.value].filter((id) => visibleIds.has(id)),
    );
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "加载失败";
    summary.value.total_sessions = 0;
    reports.value = [];
  } finally {
    recordsLoading.value = false;
  }
}

function toggleSelect(sessionId: string) {
  const next = new Set(selectedIds.value);
  if (next.has(sessionId)) next.delete(sessionId);
  else next.add(sessionId);
  selectedIds.value = next;
}

function selectAllVisible() {
  selectedIds.value = new Set(filteredReports.value.map((r) => r.session_id));
}

function clearSelection() {
  selectedIds.value = new Set();
}

function toggleSelectAllVisible() {
  if (allVisibleSelected.value) clearSelection();
  else selectAllVisible();
}

async function handleBulkExport() {
  exporting.value = true;
  error.value = "";
  try {
    const blob = await exportReport(selectedFormat.value as "pdf" | "csv", queryParams.value);
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
  await handleBulkExport();
}

async function downloadSingle(report: ReportItem) {
  try {
    const blob = await exportSessionReport(report.session_id);
    downloadSessionReport(blob, report.session_id, report.title);
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "下载失败";
  }
}

async function downloadSingleFromDetail() {
  if (!detail.value) return;
  try {
    const blob = await exportSessionReport(detail.value.session_id);
    downloadSessionReport(blob, detail.value.session_id, detail.value.exercise_name);
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "下载失败";
  }
}

async function exportSelectedSessions() {
  if (selectedIds.value.size === 0) return;
  exportingSelected.value = true;
  error.value = "";
  try {
    for (const sessionId of selectedIds.value) {
      const report = reports.value.find((r) => r.session_id === sessionId);
      const blob = await exportSessionReport(sessionId);
      downloadSessionReport(blob, sessionId, report?.title);
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "批量导出失败";
  } finally {
    exportingSelected.value = false;
  }
}

function disposeDetailCharts() {
  detailCharts.forEach((c) => c.dispose());
  detailCharts = [];
}

function renderDetailCharts(data: ReportDetail) {
  disposeDetailCharts();
  if (detailRadarRef.value) {
    const radar = echarts.init(detailRadarRef.value);
    radar.setOption({
      radar: {
        indicator: data.charts.quality_radar.dimensions.map((name) => ({ name, max: 100 })),
        axisName: { color: "#94a3b8", fontSize: 11 },
      },
      series: [{
        type: "radar",
        data: [{ value: data.charts.quality_radar.values, areaStyle: { color: "rgba(59,130,246,0.2)" } }],
      }],
    });
    detailCharts.push(radar);
  }
  if (detailRepRef.value) {
    const rep = echarts.init(detailRepRef.value);
    rep.setOption({
      tooltip: { trigger: "item" },
      series: [{
        type: "pie",
        radius: ["40%", "65%"],
        data: data.charts.rep_breakdown.labels.map((name, i) => ({
          name,
          value: data.charts.rep_breakdown.values[i],
        })),
        color: ["#22c55e", "#ef4444"],
      }],
    });
    detailCharts.push(rep);
  }
}

async function openDetail(sessionId: string) {
  showDetail.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    detail.value = await getReportDetail(sessionId);
    await nextTick();
    if (detail.value) renderDetailCharts(detail.value);
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "加载详情失败";
    showDetail.value = false;
  } finally {
    detailLoading.value = false;
  }
}

function closeDetail() {
  showDetail.value = false;
  detail.value = null;
  disposeDetailCharts();
}

onMounted(async () => {
  loading.value = true;
  try {
    await applyRangePreset();
    const sessionId = route.query.session;
    if (typeof sessionId === "string" && sessionId) {
      await openDetail(sessionId);
    }
  } finally {
    loading.value = false;
  }
});

onBeforeUnmount(disposeDetailCharts);
</script>

<style scoped>
.export-typography :is(h1, h2, h3, h4, strong, .report-name-cell strong) {
  font-weight: 800;
}
.export-typography .section-page-header h1 { font-size: 24px; font-weight: 800; }
.export-typography .section-page-header p { font-size: 14px; font-weight: 600; }
.export-typography .summary-card span { font-size: 13px; font-weight: 700; }
.export-typography .summary-card strong { font-size: 28px; font-weight: 900; }
.export-typography .export-card h2 { font-size: 17px; font-weight: 800; }
.export-typography .export-field { font-size: 14px; font-weight: 700; }
.export-typography .export-field select, .export-typography .date-input { font-size: 13px; font-weight: 600; }
.export-typography .primary-button { font-size: 14px; font-weight: 800; }
.export-typography .ghost-button { font-size: 13px; font-weight: 700; }
.export-typography .quick-button { font-size: 13px; font-weight: 700; }
.export-typography .preview-desc { font-size: 13px; font-weight: 600; }
.export-typography .preview-stats div { font-size: 13px; font-weight: 600; }
.export-typography .preview-stats strong { font-size: 15px; font-weight: 800; }
.export-typography .records-header h2 { font-size: 17px; font-weight: 800; }
.export-typography .records-header p { font-size: 13px; font-weight: 600; }
.export-typography .report-table th { font-size: 12px; font-weight: 800; }
.export-typography .report-table td { font-size: 13px; font-weight: 600; }
.export-typography .report-name-cell strong { font-size: 14px; }
.export-typography .report-name-cell small { font-size: 12px; font-weight: 600; }
.export-typography .grade-pill { font-size: 11px; font-weight: 800; }
.export-typography .modal-header h3 { font-size: 20px; font-weight: 800; }
.export-typography .modal-header p { font-size: 13px; font-weight: 600; }
.export-typography .eval-summary { font-size: 14px; font-weight: 600; }
.export-typography .eval-columns h4 { font-size: 14px; font-weight: 800; }
.export-typography .eval-columns ul { font-size: 13px; font-weight: 600; }
.export-typography .detail-metrics strong { font-size: 17px; font-weight: 800; }

.export-page { display: grid; gap: 24px; }
.section-page-header h1 { margin: 0 0 4px; color: #f8fafc; }
.section-page-header p { margin: 0; color: #64748b; font-size: 13px; }

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
.primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 24px; border: none; border-radius: 9px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; font-weight: 700; cursor: pointer; }
.primary-button.compact { padding: 10px 16px; font-size: 13px; }
.primary-button:disabled { opacity: 0.5; cursor: not-allowed; }
.ghost-button { padding: 10px 14px; border: 1px solid rgba(59,130,246,0.15); border-radius: 9px; background: transparent; color: #94a3b8; cursor: pointer; font-size: 13px; }
.ghost-button:disabled { opacity: 0.4; cursor: not-allowed; }
.error-message { color: #f87171; font-size: 13px; }

.quick-export-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 12px; align-content: start; }
.quick-button { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: 1px solid rgba(59,130,246,0.08); border-radius: 9px; background: rgba(8,13,26,0.4); color: #94a3b8; cursor: pointer; }
.preview-desc { color: #64748b; font-size: 12px; line-height: 1.6; margin: 0 0 12px; }
.preview-stats div { display: flex; justify-content: space-between; color: #94a3b8; font-size: 13px; margin-bottom: 6px; }
.preview-stats strong { color: #f8fafc; }

.records-section { display: grid; gap: 16px; padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); }
.records-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.records-header h2 { color: #f8fafc; margin: 0 0 4px; font-size: 16px; }
.records-header p { color: #64748b; margin: 0; font-size: 13px; }
.records-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

.filter-card { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.session-search { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 200px; padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.5); color: #94a3b8; }
.session-search input { flex: 1; border: none; background: transparent; color: #f8fafc; outline: none; }
.filter-card select { padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; }

.report-table-card { overflow: hidden; border-radius: 12px; border: 1px solid rgba(59,130,246,0.08); }
.report-table { width: 100%; border-collapse: collapse; }
.report-table th, .report-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(59,130,246,0.06); color: #cbd5e1; font-size: 13px; }
.report-table th { color: #64748b; font-size: 11px; text-transform: uppercase; background: rgba(8,13,26,0.5); }
.report-table tr.selected { background: rgba(59,130,246,0.05); }
.col-check { width: 40px; }
.report-name-cell { display: flex; align-items: center; gap: 10px; }
.report-name-cell strong { color: #f8fafc; display: block; }
.report-name-cell small { color: #64748b; }
.score-progress { display: flex; align-items: center; gap: 8px; position: relative; min-width: 80px; }
.score-progress i { position: absolute; left: 0; height: 4px; border-radius: 999px; opacity: 0.4; }
.progress-green { background: #22c55e; }
.progress-blue { background: #3b82f6; }
.grade-pill { padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.grade-a { background: rgba(34,197,94,0.15); color: #4ade80; }
.grade-b { background: rgba(59,130,246,0.15); color: #60a5fa; }
.grade-c { background: rgba(245,158,11,0.15); color: #fbbf24; }
.grade-d { background: rgba(239,68,68,0.15); color: #f87171; }
.report-actions { display: flex; gap: 8px; }
.report-actions button { background: none; border: none; color: #64748b; cursor: pointer; padding: 4px; border-radius: 6px; }
.report-actions button:hover { color: #93c5fd; background: rgba(59,130,246,0.08); }

.modal-overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.65); display: grid; place-items: center; padding: 24px; }
.report-detail-modal { width: 100%; max-width: 820px; max-height: 90vh; overflow-y: auto; background: #0f172a; border: 1px solid rgba(59,130,246,0.15); border-radius: 16px; padding: 28px; }
.modal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.modal-header h3 { color: #f8fafc; margin: 0 0 4px; }
.modal-header p { color: #64748b; margin: 0; font-size: 13px; }
.close-button { background: none; border: none; color: #64748b; cursor: pointer; }
.detail-score-row { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; margin-bottom: 16px; }
.score-circle { width: 90px; height: 90px; border-radius: 50%; border: 3px solid #3b82f6; display: grid; place-items: center; text-align: center; }
.score-circle strong { font-size: 28px; color: #f8fafc; line-height: 1; }
.score-circle span { font-size: 11px; color: #64748b; }
.grade-badge { padding: 8px 16px; border-radius: 10px; font-weight: 700; font-size: 16px; }
.detail-metrics { display: flex; gap: 20px; flex-wrap: wrap; }
.detail-metrics div { display: grid; gap: 2px; }
.detail-metrics span { color: #64748b; font-size: 11px; }
.detail-metrics strong { color: #f8fafc; font-size: 16px; }
.eval-summary { color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0 0 16px; padding: 12px 16px; background: rgba(59,130,246,0.06); border-radius: 8px; }
.detail-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.detail-chart { height: 220px; background: rgba(8,13,26,0.5); border-radius: 10px; }
.eval-columns { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.eval-columns article { padding: 14px; border-radius: 10px; background: rgba(8,13,26,0.5); border: 1px solid rgba(59,130,246,0.08); }
.eval-columns h4 { color: #f8fafc; margin: 0 0 8px; font-size: 13px; }
.eval-columns ul { margin: 0; padding-left: 16px; color: #94a3b8; font-size: 12px; line-height: 1.6; }
.modal-export-btn { width: 100%; }

@media (max-width: 1000px) {
  .export-layout, .summary-card-grid { grid-template-columns: 1fr; }
  .detail-charts, .eval-columns { grid-template-columns: 1fr; }
}
</style>
