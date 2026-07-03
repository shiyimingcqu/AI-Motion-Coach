<template>
  <div class="export-page">
    <StateDisplay
      v-if="loading"
      type="loading"
      skeleton="cards"
      :text="$t('exportReports.loading')"
    />

    <div v-else class="export-layout">
      <div class="export-main">
        <section class="export-card">
          <h2 class="section-title">{{ $t("exportReports.exportFormat") }}</h2>
          <div class="format-grid">
            <button
              v-for="fmt in formats"
              :key="fmt.value"
              type="button"
              class="format-option"
              :class="{ selected: selectedFormat === fmt.value }"
              @click="selectedFormat = fmt.value"
            >
              <span class="format-icon" :class="fmt.color">
                <component :is="fmt.icon" :size="24" />
              </span>
              <div class="format-info">
                <strong>{{ fmt.title }}</strong>
                <small>{{ fmt.desc }}</small>
              </div>
            </button>
          </div>
        </section>

        <section class="export-card">
          <h2 class="section-title">{{ $t("exportReports.filterConfig") }}</h2>

          <div class="filter-grid">
            <label class="filter-field">
              <span>{{ $t("exportReports.timeRange") }}</span>
              <div class="select-wrap">
                <select v-model="timeRange" class="dark-select">
                  <option value="last7">{{ $t("exportReports.last7Days") }}</option>
                  <option value="last30">{{ $t("exportReports.last30Days") }}</option>
                  <option value="all">{{ $t("exportReports.allTime") }}</option>
                </select>
                <ChevronDown :size="16" class="select-arrow" />
              </div>
            </label>

            <label class="filter-field">
              <span>{{ $t("exportReports.exerciseType") }}</span>
              <div class="select-wrap">
                <select v-model="selectedExercise" class="dark-select">
                  <option value="">{{ $t("exportReports.allExercises") }}</option>
                  <option v-for="ex in exercises" :key="ex.key" :value="ex.key">
                    {{ ex.name }}
                  </option>
                </select>
                <ChevronDown :size="16" class="select-arrow" />
              </div>
            </label>
          </div>

          <div class="include-section">
            <span class="include-title">{{ $t("exportReports.includeContent") }}</span>
            <div class="include-list">
              <label v-for="item in includeItems" :key="item.key">
                <input v-model="item.enabled" type="checkbox" />
                <span class="checkmark" />
                {{ item.label }}
              </label>
            </div>
          </div>

          <button
            class="download-button"
            type="button"
            :disabled="exporting || summary.total_sessions === 0"
            @click="handleExport"
          >
            <Download :size="18" />
            {{ exporting ? $t("exportReports.generating") : $t("exportReports.download") }}
          </button>
          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="summary.total_sessions === 0 && !error" class="no-data-hint">
            {{ $t("exportReports.noData") }}
          </div>
        </section>
      </div>

      <aside class="export-side">
        <section class="export-card">
          <h2 class="section-title">{{ $t("exportReports.quickExport") }}</h2>
          <div class="quick-list">
            <button
              class="quick-button"
              type="button"
              :disabled="summary.total_sessions === 0"
              @click="quickExport('pdf', 'last7')"
            >
              <FileText :size="18" />
              {{ $t("exportReports.quick7DaysPdf") }}
            </button>
            <button
              class="quick-button"
              type="button"
              :disabled="summary.total_sessions === 0"
              @click="quickExport('pdf', 'all')"
            >
              <FileText :size="18" />
              {{ $t("exportReports.quickAllPdf") }}
            </button>
            <button
              class="quick-button"
              type="button"
              :disabled="summary.total_sessions === 0"
              @click="quickExport('csv', 'all')"
            >
              <FileSpreadsheet :size="18" />
              {{ $t("exportReports.quickAllCsv") }}
            </button>
          </div>
        </section>

        <section class="export-card desc-card">
          <h2 class="section-title">{{ $t("exportReports.reportDesc") }}</h2>
          <p class="desc-text">{{ $t("exportReports.reportDescText") }}</p>

          <div class="preview-table-wrap">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>{{ $t("exportReports.previewHeaderScope") }}</th>
                  <th>{{ $t("exportReports.previewHeaderExercise") }}</th>
                  <th>{{ $t("exportReports.previewHeaderSessions") }}</th>
                  <th>{{ $t("exportReports.previewHeaderAvgScore") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in previewRows" :key="row.exercise">
                  <td>{{ row.scope }}</td>
                  <td>{{ row.exerciseName }}</td>
                  <td>{{ row.sessions }}</td>
                  <td>{{ row.avgScore }}</td>
                </tr>
                <tr v-if="previewRows.length === 0">
                  <td colspan="4" class="no-data">—</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/auth";
import {
  ChevronDown,
  Download,
  FileSpreadsheet,
  FileText,
} from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import { getPersonalReport } from "@/api/reports";
import { getSimpleExercises } from "@/api/exercises";

const { t } = useI18n();

interface ExerciseOption {
  key: string;
  name: string;
}

interface IncludeItem {
  key: string;
  label: string;
  enabled: boolean;
}

const formats = [
  {
    value: "pdf",
    title: computed(() => t("exportReports.pdfComprehensive")),
    desc: computed(() => t("exportReports.pdfComprehensiveDesc")),
    icon: FileText,
    color: "tone-red",
  },
  {
    value: "csv",
    title: computed(() => t("exportReports.csvData")),
    desc: computed(() => t("exportReports.csvDataDesc")),
    icon: FileSpreadsheet,
    color: "tone-green",
  },
];

const includeItems = ref<IncludeItem[]>([
  { key: "summary", label: t("exportReports.includeSummary"), enabled: true },
  { key: "charts", label: t("exportReports.includeCharts"), enabled: true },
  { key: "sessions", label: t("exportReports.includeSessions"), enabled: true },
  { key: "dimensions", label: t("exportReports.includeDimensions"), enabled: true },
  { key: "suggestions", label: t("exportReports.includeSuggestions"), enabled: true },
]);

const summary = ref({
  total_sessions: 0,
  average_score: 0,
  total_duration_minutes: 0,
  total_count: 0,
  valid_count: 0,
  error_count: 0,
  by_exercise: [] as {
    exercise: string;
    sessions: number;
    avg_score: number;
  }[],
});

const exercises = ref<ExerciseOption[]>([]);
const selectedFormat = ref("pdf");
const timeRange = ref("last7");
const selectedExercise = ref("");
const loading = ref(true);
const exporting = ref(false);
const error = ref("");

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const previewRows = computed(() => {
  const scopeMap: Record<string, string> = {
    last7: t("exportReports.last7Days"),
    last30: t("exportReports.last30Days"),
    all: t("exportReports.allTime"),
  };
  const scope = scopeMap[timeRange.value] || scopeMap.all;
  if (selectedExercise.value) {
    const item = summary.value.by_exercise.find(
      (it) => it.exercise === selectedExercise.value
    );
    if (!item) return [];
    return [
      {
        scope,
        exercise: item.exercise,
        exerciseName: t(`exercises.${item.exercise}`) || item.exercise,
        sessions: item.sessions,
        avgScore: Number(item.avg_score).toFixed(1),
      },
    ];
  }
  return summary.value.by_exercise.map((item) => ({
    scope,
    exercise: item.exercise,
    exerciseName: t(`exercises.${item.exercise}`) || item.exercise,
    sessions: item.sessions,
    avgScore: Number(item.avg_score).toFixed(1),
  }));
});

function computeDateRange(range: string): { dateFrom: string; dateTo: string } {
  const today = new Date();
  const toStr = today.toISOString().slice(0, 10);
  if (range === "all") return { dateFrom: "", dateTo: "" };
  const days = range === "last30" ? 30 : 7;
  const from = new Date(today);
  from.setDate(from.getDate() - days);
  return { dateFrom: from.toISOString().slice(0, 10), dateTo: toStr };
}

function buildExportUrl(format: string, range: string, exercise: string): string {
  const params = new URLSearchParams();
  params.set("format", format);
  const { dateFrom, dateTo } = computeDateRange(range);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  if (exercise) params.set("exercise", exercise);
  return `${API_BASE}/reports/export?${params.toString()}`;
}

async function downloadFile(url: string, filename: string) {
  const authStore = useAuthStore();
  if (!authStore.token) {
    throw new Error("未登录，请重新登录后再试");
  }
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${authStore.token}` },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`下载失败 (${response.status}): ${text || response.statusText}`);
  }
  const contentType = response.headers.get("Content-Type") || "";
  if (!contentType.includes("application/pdf") && !contentType.includes("text/csv")) {
    const text = await response.text();
    throw new Error(`服务器返回了非文件内容: ${text.slice(0, 200)}`);
  }
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  }, 1000);
}

async function handleExport() {
  exporting.value = true;
  error.value = "";
  try {
    const url = buildExportUrl(
      selectedFormat.value,
      timeRange.value,
      selectedExercise.value
    );
    const ext = selectedFormat.value;
    const dateStr = new Date().toISOString().slice(0, 10);
    await downloadFile(url, `training_report_${dateStr}.${ext}`);
  } catch (err: any) {
    error.value = err.message || t("exportReports.exportFailed");
  } finally {
    exporting.value = false;
  }
}

async function quickExport(format: string, range: string) {
  selectedFormat.value = format;
  timeRange.value = range;
  await handleExport();
}

function normalizeByExercise(data: Record<string, unknown>) {
  const legacy = data.by_exercise as { exercise: string; sessions: number; avg_score: number }[] | undefined;
  if (legacy?.length) return legacy;

  const breakdown = (data.exercise_breakdown || []) as {
    exercise: string;
    count?: number;
    sessions?: number;
    avg_score: number;
  }[];
  return breakdown.map((item) => ({
    exercise: item.exercise,
    sessions: item.sessions ?? item.count ?? 0,
    avg_score: item.avg_score,
  }));
}

onMounted(async () => {
  try {
    const [data, exRaw] = await Promise.all([
      getPersonalReport(),
      getSimpleExercises().catch(() => ({ items: [] })),
    ]);
    summary.value = {
      total_sessions: data.total_sessions || 0,
      average_score: data.average_score || 0,
      total_duration_minutes: data.total_duration_minutes || 0,
      total_count: (data as any).total_count || 0,
      valid_count: (data as any).valid_count || 0,
      error_count: (data as any).error_count || 0,
      by_exercise: normalizeByExercise(data as Record<string, unknown>),
    };
    // /exercises/simple 返回 { items: [...] }，兼容处理
    const rawList = Array.isArray(exRaw) ? exRaw : (exRaw as any).items ?? [];
    exercises.value = rawList.map((it: any) => ({
      key: it.key,
      name: it.name || t(`exercises.${it.key}`) || it.key,
    }));
  } catch (err: any) {
    error.value = err?.message || "加载数据失败";
    summary.value = {
      total_sessions: 0,
      average_score: 0,
      total_duration_minutes: 0,
      total_count: 0,
      valid_count: 0,
      error_count: 0,
      by_exercise: [],
    };
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.export-page {
  display: grid;
  gap: 24px;
}

.export-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 20px;
  align-items: start;
}

.export-main {
  display: grid;
  gap: 20px;
}

.export-side {
  display: grid;
  gap: 20px;
  align-content: start;
}

.export-card {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 16px;
  padding: 24px;
  display: grid;
  gap: 18px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
}

.format-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.format-option {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 12px;
  background: rgba(8, 13, 26, 0.5);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}

.format-option:hover {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.08);
}

.format-option.selected {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.12);
}

.format-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  flex-shrink: 0;
}

.tone-red {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
}

.tone-green {
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
}

.format-info {
  display: grid;
  gap: 4px;
}

.format-info strong {
  color: #f8fafc;
  font-size: 15px;
  font-weight: 600;
}

.format-info small {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.4;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.filter-field {
  display: grid;
  gap: 8px;
}

.filter-field > span {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}

.select-wrap {
  position: relative;
}

.dark-select {
  width: 100%;
  appearance: none;
  padding: 12px 36px 12px 14px;
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 10px;
  background: rgba(8, 13, 26, 0.6);
  color: #f8fafc;
  font-size: 14px;
  cursor: pointer;
  outline: none;
}

.dark-select:focus {
  border-color: #3b82f6;
}

.dark-select option {
  background: #0f172a;
  color: #f8fafc;
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.include-section {
  display: grid;
  gap: 12px;
}

.include-title {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}

.include-list {
  display: grid;
  gap: 10px;
}

.include-list label {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #cbd5e1;
  font-size: 13px;
  cursor: pointer;
}

.include-list input[type="checkbox"] {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  background: rgba(8, 13, 26, 0.5);
  position: relative;
  cursor: pointer;
}

.include-list input[type="checkbox"]:checked {
  background: #3b82f6;
  border-color: #3b82f6;
}

.include-list input[type="checkbox"]:checked::after {
  content: "";
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.download-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.download-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.download-button:hover:not(:disabled) {
  opacity: 0.92;
}

.no-data-hint {
  padding: 12px 16px;
  color: #94a3b8;
  font-size: 13px;
  background: rgba(239, 68, 68, 0.06);
  border-radius: 10px;
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.error-message {
  color: #f87171;
  background: rgba(239, 68, 68, 0.08);
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.quick-list {
  display: grid;
  gap: 10px;
}

.quick-button {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 10px;
  background: rgba(8, 13, 26, 0.4);
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-button:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.25);
}

.quick-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.desc-card {
  gap: 14px;
}

.desc-text {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.7;
}

.preview-table-wrap {
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th,
.preview-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.preview-table th {
  color: #64748b;
  font-weight: 500;
}

.preview-table td {
  color: #cbd5e1;
}

.preview-table .no-data {
  text-align: center;
  color: #64748b;
  padding: 20px 8px;
}

@media (max-width: 1000px) {
  .export-layout {
    grid-template-columns: 1fr;
  }
  .format-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
