<template>
  <div class="evaluation-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("reports.title") }}</h1>
        <p>{{ $t("reports.subtitle") }}</p>
      </div>
    </header>

    <section class="summary-card-grid">
      <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="filter-card report-filter-card">
      <label class="session-search">
        <Filter :size="18" />
        <input v-model="keyword" type="search" :placeholder="$t('reports.search')" />
      </label>
      <select v-model="typeFilter">
        <option value="">{{ $t("common.all") }} Types</option>
        <option value="Monthly">Monthly</option>
        <option value="Weekly">Weekly</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">{{ $t("sessions.newest") }}</option>
        <option value="asc">{{ $t("sessions.oldest") }}</option>
      </select>
    </section>

    <section class="report-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="5" :text="$t('reports.loading')" />
      <StateDisplay v-else-if="filteredReports.length === 0" type="empty" :title="$t('reports.noReports')" :text="$t('reports.noReportsText')" />
      <table v-else class="report-table">
        <thead>
          <tr>
            <th>{{ $t("reports.tableHead_report") }}</th>
            <th>{{ $t("reports.tableHead_type") }}</th>
            <th>{{ $t("reports.tableHead_date") }}</th>
            <th>{{ $t("reports.tableHead_coverage") }}</th>
            <th>{{ $t("reports.tableHead_score") }}</th>
            <th>{{ $t("reports.tableHead_size") }}</th>
            <th>{{ $t("reports.tableHead_actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="report in filteredReports" :key="report.id || report.title" class="report-row">
            <td>
              <div class="report-name-cell">
                <span><FileText :size="18" /></span>
                <div>
                  <strong>{{ report.title }}</strong>
                  <small>{{ report.subtitle }}</small>
                </div>
              </div>
            </td>
            <td><span class="report-type-pill">{{ report.type }}</span></td>
            <td>{{ report.date }}</td>
            <td>
              <span>{{ $t("reports.exercises", { count: report.exercises_count || 0 }) }}</span>
              <small>{{ $t("reports.sessions", { count: report.sessions_count || 0 }) }}</small>
            </td>
            <td>
              <div class="score-progress">
                <i :class="report.average_score >= 90 ? 'progress-green' : 'progress-blue'" :style="{ width: report.average_score + '%' }" />
                <strong>{{ report.average_score }}</strong>
              </div>
            </td>
            <td>{{ report.size }}</td>
            <td>
              <div class="report-actions">
                <button class="icon-btn" :title="$t('reports.viewDetail')" @click="openDetail(report)">
                  <Eye :size="16" />
                </button>
                <button class="icon-btn" :title="$t('reports.downloadReport')" @click="onDownload(report)">
                  <Download :size="16" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="automated-report-card">
      <span class="blue-solid"><ClipboardList :size="25" /></span>
      <div>
        <h2>{{ $t("reports.autoGeneration") }}</h2>
        <p>{{ $t("reports.autoGenerationDesc") }}</p>
        <button class="blue-action-button small-blue-button" type="button">{{ $t("reports.learnMore") }}</button>
      </div>
    </section>

    <!-- Report Detail Modal -->
    <Teleport to="body">
      <div v-if="detailVisible" class="modal-overlay" @click.self="closeDetail">
        <div class="modal-container report-detail-modal">
          <div class="modal-header">
            <h2>{{ $t("reports.detailTitle", { exercise: detailData?.exercise_name }) }}</h2>
            <button class="modal-close" @click="closeDetail">&times;</button>
          </div>
          <div v-if="detailLoading" class="modal-body">
            <StateDisplay type="loading" skeleton="table" :skeleton-rows="6" :text="$t('reports.detailLoading')" />
          </div>
          <div v-else-if="detailError" class="modal-body">
            <StateDisplay type="error" :text="detailError" />
          </div>
          <div v-else-if="detailData" class="modal-body">
            <div class="summary-card-grid modal-cards">
              <article class="summary-card compact-summary">
                <span>{{ $t("reports.score") }}</span>
                <strong :class="detailData.average_score >= 90 ? 'text-green' : detailData.average_score >= 70 ? 'text-blue' : 'text-orange'">
                  {{ detailData.average_score }}
                </strong>
              </article>
              <article class="summary-card compact-summary">
                <span>{{ $t("reports.grade") }}</span>
                <strong>{{ detailData.evaluation?.grade_label || '-' }}</strong>
              </article>
              <article class="summary-card compact-summary">
                <span>{{ $t("reports.validCount") }}</span>
                <strong>{{ detailData.valid_count }} / {{ detailData.total_count }}</strong>
              </article>
              <article class="summary-card compact-summary">
                <span>{{ $t("reports.calories") }}</span>
                <strong>{{ detailData.calories_burned }} {{ $t("reports.kcal") }}</strong>
              </article>
            </div>

            <div v-if="dimensionEntries.length > 0" class="detail-section">
              <h4>{{ $t("reports.dimensionScores") }}</h4>
              <div class="dimension-bars">
                <div v-for="[label, value] in dimensionEntries" :key="label" class="dimension-bar-row">
                  <span class="dim-label">{{ label }}</span>
                  <div class="dim-bar-track">
                    <div class="dim-bar-fill" :style="{ width: Math.min(value, 100) + '%' }" />
                  </div>
                  <span class="dim-value">{{ value }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>{{ $t("reports.repBreakdown") }}</h4>
              <div class="rep-breakdown">
                <div v-for="(label, i) in detailData.charts?.rep_breakdown?.labels" :key="label" class="rep-item">
                  <span class="rep-label">{{ label }}</span>
                  <span class="rep-value">{{ detailData.charts?.rep_breakdown?.values?.[i] ?? 0 }}</span>
                </div>
              </div>
            </div>

            <div v-if="detailData.evaluation?.strengths?.length || detailData.evaluation?.weaknesses?.length" class="detail-section">
              <h4>{{ $t("reports.evaluationSuggestions") }}</h4>
              <div v-if="detailData.evaluation?.strengths?.length" class="eval-list">
                <p class="eval-label good">{{ $t("reports.strengths") }}</p>
                <ul>
                  <li v-for="s in detailData.evaluation.strengths" :key="s">{{ s }}</li>
                </ul>
              </div>
              <div v-if="detailData.evaluation?.weaknesses?.length" class="eval-list">
                <p class="eval-label warn">{{ $t("reports.weaknesses") }}</p>
                <ul>
                  <li v-for="w in detailData.evaluation.weaknesses" :key="w">{{ w }}</li>
                </ul>
              </div>
              <div v-if="detailData.evaluation?.recommendations?.length" class="eval-list">
                <p class="eval-label info">{{ $t("reports.recommendations") }}</p>
                <ul>
                  <li v-for="r in detailData.evaluation.recommendations" :key="r">{{ r }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-if="!detailLoading && detailData" class="modal-footer">
            <button class="blue-action-button small-blue-button" type="button" @click="onDownloadCurrent">{{ $t("reports.downloadPdf") }}</button>
            <button class="secondary-button small-blue-button" type="button" @click="closeDetail">{{ $t("common.close") }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { ClipboardList, Download, Eye, FileText, Filter } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getReports, getReportDetail, exportSessionReport, downloadSessionReport } from "../api/reports";

const { t } = useI18n();

interface ReportItem {
  id: string;
  session_id: string;
  title: string;
  subtitle: string;
  type: string;
  date: string;
  exercise: string;
  exercise_name: string;
  exercises_count: number;
  sessions_count: number;
  average_score: number;
  calories: number;
  size: string;
  grade?: string;
  grade_label?: string;
}

interface ReportDetailData {
  session_id: string;
  exercise: string;
  exercise_name: string;
  created_at: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  calories_burned: number;
  evaluation?: {
    grade: string;
    grade_label: string;
    strengths: string[];
    weaknesses: string[];
    recommendations: string[];
  };
  charts?: {
    rep_breakdown?: { labels: string[]; values: number[] };
  };
}

const reports = ref<ReportItem[]>([]);
const loading = ref(true);
const keyword = ref("");
const typeFilter = ref("");
const sortOrder = ref("desc");

const detailVisible = ref(false);
const detailLoading = ref(false);
const detailError = ref("");
const detailData = ref<ReportDetailData | null>(null);
const currentReport = ref<ReportItem | null>(null);

const filteredReports = computed(() => {
  let list = [...reports.value];

  if (typeFilter.value) {
    list = list.filter(r => r.type === typeFilter.value);
  }

  const query = keyword.value.trim().toLowerCase();
  if (query) {
    list = list.filter(r =>
      r.title.toLowerCase().includes(query) ||
      r.subtitle.toLowerCase().includes(query)
    );
  }

  list.sort((a, b) => {
    const diff = a.date.localeCompare(b.date);
    return sortOrder.value === "desc" ? -diff : diff;
  });

  return list;
});

const stats = computed(() => {
  const total = reports.value.length;
  const avgScore = total > 0
    ? reports.value.reduce((s, r) => s + r.average_score, 0) / total
    : 0;
  return [
    { label: t("reports.summary_total"), value: total },
    { label: t("reports.summary_avg"), value: avgScore.toFixed(1) },
    { label: t("reports.summary_exercises"), value: reports.value.reduce((s, r) => s + (r.exercises_count || 0), 0) },
    { label: t("reports.summary_sessions"), value: reports.value.reduce((s, r) => s + (r.sessions_count || 0), 0) },
  ];
});

const dimensionEntries = computed(() => {
  const evalData = detailData.value?.evaluation;
  if (!evalData?.dimension_scores) return [];
  return Object.entries(evalData.dimension_scores as Record<string, number>);
});

async function openDetail(report: ReportItem) {
  currentReport.value = report;
  detailVisible.value = true;
  detailLoading.value = true;
  detailError.value = "";
  detailData.value = null;
  try {
    const data = await getReportDetail(report.session_id || report.id);
    detailData.value = data as unknown as ReportDetailData;
  } catch (e: any) {
    detailError.value = e?.message || t("reports.loadDetailFailed");
  } finally {
    detailLoading.value = false;
  }
}

function closeDetail() {
  detailVisible.value = false;
  detailData.value = null;
  currentReport.value = null;
}

async function onDownload(report: ReportItem) {
  try {
    const blob = await exportSessionReport(report.session_id || report.id);
    downloadSessionReport(blob, report.session_id || report.id);
  } catch (e: any) {
    alert(e?.message || t("reports.downloadFailed"));
  }
}

async function onDownloadCurrent() {
  if (currentReport.value) {
    await onDownload(currentReport.value);
  }
}

onMounted(async () => {
  try {
    const data = await getReports();
    reports.value = data.items || [];
  } catch {
    reports.value = [];
  } finally {
    loading.value = false;
  }
});
</script>
