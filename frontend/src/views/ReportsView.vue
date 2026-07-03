<template>
  <div class="evaluation-page">
    <header class="section-page-header">
      <div>
        <h1>Evaluation Reports / 评估报告</h1>
        <p>面向健身爱好者与私人教练的专业姿态评估报告 · 单次训练详情与建议</p>
      </div>
      <button
        class="blue-action-button"
        type="button"
        :disabled="downloading || summary.total_sessions === 0"
        @click="downloadFullReport"
      >
        <Download :size="18" />
        {{ downloading ? "生成中..." : "下载完整 PDF 报告" }}
      </button>
    </header>

    <section class="coach-banner">
      <div class="coach-icon">🏋️</div>
      <div>
        <strong>学员 & 教练双视角报告</strong>
        <p>PDF 报告包含训练概览、图表分析、分项评估与个性化训练建议，可直接分享给您的健身教练。</p>
      </div>
    </section>

    <section class="summary-card-grid">
      <article v-for="item in stats" :key="item.label" class="summary-card compact-summary">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
      </article>
    </section>

    <p v-if="loadError" class="report-load-error">{{ loadError }}</p>

    <section class="filter-card report-filter-card">
      <label class="session-search">
        <Filter :size="18" />
        <input v-model="keyword" type="search" placeholder="搜索报告..." />
      </label>
      <select v-model="exerciseFilter">
        <option value="">全部动作</option>
        <option v-for="ex in exerciseOptions" :key="ex.key" :value="ex.key">{{ ex.name }}</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">最新优先</option>
        <option value="asc">最早优先</option>
      </select>
    </section>

    <section class="report-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="5" text="正在加载报告..." />
      <StateDisplay v-else-if="filteredReports.length === 0" type="empty" title="暂无报告" text="完成训练后，系统将自动生成评估报告" />
      <table v-else class="report-table">
        <thead>
          <tr>
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
          <tr v-for="report in filteredReports" :key="report.id">
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
                <button type="button" title="下载" @click="downloadSingle(report)">
                  <Download :size="16" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 报告详情弹窗 -->
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
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import * as echarts from "echarts";
import { Download, Eye, FileText, Filter, X } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import {
  getPersonalReport,
  getReportDetail,
  getReports,
  exportReport,
  exportSessionReport,
  downloadReport,
  downloadSessionReport,
  type PersonalReport,
  type ReportDetail,
  type ReportItem,
} from "../api/reports";

const route = useRoute();
const reports = ref<ReportItem[]>([]);
const summary = ref<PersonalReport>({
  average_score: 0,
  total_sessions: 0,
  total_duration_minutes: 0,
  total_count: 0,
  valid_count: 0,
  error_count: 0,
  total_calories: 0,
  trend: [],
  exercise_breakdown: [],
  recent_sessions: [],
  charts: {
    score_trend: [],
    calorie_by_exercise: [],
    exercise_distribution: [],
    quality_radar: { dimensions: [], values: [] },
    error_by_exercise: [],
  },
});

const loading = ref(true);
const loadError = ref("");
const downloading = ref(false);
const keyword = ref("");
const exerciseFilter = ref("");
const sortOrder = ref("desc");

const showDetail = ref(false);
const detailLoading = ref(false);
const detail = ref<ReportDetail | null>(null);
const detailRadarRef = ref<HTMLElement | null>(null);
const detailRepRef = ref<HTMLElement | null>(null);
let detailCharts: echarts.ECharts[] = [];

const EXERCISE_OPTIONS = [
  { key: "squat", name: "深蹲" },
  { key: "push_up", name: "俯卧撑" },
  { key: "jumping_jack", name: "开合跳" },
  { key: "plank", name: "平板支撑" },
];

const exerciseOptions = computed(() => {
  const fromData = reports.value.map((r) => ({
    key: r.exercise,
    name: r.exercise_name || r.exercise,
  }));
  const merged = new Map<string, { key: string; name: string }>();
  for (const item of [...EXERCISE_OPTIONS, ...fromData]) {
    merged.set(item.key, item);
  }
  return [...merged.values()];
});

const filteredReports = computed(() => {
  let list = [...reports.value];
  if (exerciseFilter.value) {
    list = list.filter((r) => r.exercise === exerciseFilter.value);
  }
  const query = keyword.value.trim().toLowerCase();
  if (query) {
    list = list.filter(
      (r) =>
        r.title.toLowerCase().includes(query) ||
        r.subtitle.toLowerCase().includes(query),
    );
  }
  list.sort((a, b) => {
    const diff = a.date.localeCompare(b.date);
    return sortOrder.value === "desc" ? -diff : diff;
  });
  return list;
});

const stats = computed(() => [
  { label: "报告总数", value: reports.value.length, tone: "tone-blue" },
  { label: "平均评分", value: summary.value.average_score.toFixed(1), tone: "tone-green" },
  { label: "总消耗卡路里", value: `${summary.value.total_calories} kcal`, tone: "tone-orange" },
  { label: "训练时长", value: `${summary.value.total_duration_minutes} min`, tone: "tone-purple" },
]);

function gradeClass(grade?: string) {
  if (grade === "A") return "grade-a";
  if (grade === "B") return "grade-b";
  if (grade === "C") return "grade-c";
  return "grade-d";
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
  } finally {
    detailLoading.value = false;
  }
}

function closeDetail() {
  showDetail.value = false;
  detail.value = null;
  disposeDetailCharts();
}

async function downloadFullReport() {
  downloading.value = true;
  try {
    const blob = await exportReport("pdf");
    downloadReport(blob, "pdf");
  } catch (err: unknown) {
    alert(err instanceof Error ? err.message : "PDF 下载失败");
  } finally {
    downloading.value = false;
  }
}

async function downloadSingle(report: ReportItem) {
  try {
    const blob = await exportSessionReport(report.session_id);
    downloadSessionReport(blob, report.session_id);
  } catch (err: unknown) {
    alert(err instanceof Error ? err.message : "下载失败");
  }
}

onMounted(async () => {
  await loadReports();
});

onActivated(async () => {
  await loadReports();
});

async function loadReports() {
  loading.value = true;
  loadError.value = "";
  try {
    const [reportListRes, personalRes] = await Promise.allSettled([
      getReports(),
      getPersonalReport(),
    ]);

    if (reportListRes.status === "fulfilled") {
      reports.value = reportListRes.value.items;
    } else {
      reports.value = [];
      loadError.value = reportListRes.reason instanceof Error
        ? reportListRes.reason.message
        : "加载报告列表失败";
    }

    if (personalRes.status === "fulfilled") {
      summary.value = personalRes.value;
    } else if (reports.value.length > 0) {
      summary.value = {
        ...summary.value,
        total_sessions: reports.value.length,
        average_score: reports.value.reduce((s, r) => s + r.average_score, 0) / reports.value.length,
        total_calories: reports.value.reduce((s, r) => s + (r.calories || 0), 0),
      };
      loadError.value = "概览统计加载失败，已显示报告列表";
    } else if (!loadError.value) {
      loadError.value = personalRes.reason instanceof Error
        ? personalRes.reason.message
        : "加载报告失败，请重新登录后重试";
    }

    const sessionId = route.query.session;
    if (typeof sessionId === "string" && sessionId) {
      await openDetail(sessionId);
    }
  } finally {
    loading.value = false;
  }
}

onBeforeUnmount(disposeDetailCharts);
</script>

<style scoped>
.evaluation-page { display: grid; gap: 24px; }
.report-load-error { color: #f87171; font-size: 13px; margin: 0; }

.coach-banner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 22px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(139,92,246,0.08));
  border: 1px solid rgba(59,130,246,0.18);
}
.coach-icon { font-size: 32px; line-height: 1; }
.coach-banner strong { color: #f8fafc; font-size: 15px; display: block; margin-bottom: 4px; }
.coach-banner p { color: #94a3b8; font-size: 13px; margin: 0; line-height: 1.5; }

.section-page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }

.summary-card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.summary-card { background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); border-radius: 12px; padding: 18px; display: grid; gap: 6px; }
.summary-card span { color: #64748b; font-size: 12px; }
.summary-card strong { font-size: 24px; font-weight: 800; }
.tone-blue { color: #60a5fa; }
.tone-green { color: #34d399; }
.tone-orange { color: #fbbf24; }
.tone-purple { color: #a78bfa; }

.report-table-card { padding: 0; overflow: hidden; border-radius: 14px; border: 1px solid rgba(59,130,246,0.1); }
.report-table { width: 100%; border-collapse: collapse; }
.report-table th, .report-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(59,130,246,0.06); color: #cbd5e1; font-size: 13px; }
.report-table th { color: #64748b; font-size: 11px; text-transform: uppercase; background: rgba(8,13,26,0.5); }
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

.eval-columns { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.eval-columns article { padding: 14px; border-radius: 10px; background: rgba(8,13,26,0.5); border: 1px solid rgba(59,130,246,0.08); }
.eval-columns h4 { color: #f8fafc; margin: 0 0 8px; font-size: 13px; }
.eval-columns ul { margin: 0; padding-left: 16px; color: #94a3b8; font-size: 12px; line-height: 1.6; }

@media (max-width: 900px) {
  .summary-card-grid { grid-template-columns: repeat(2, 1fr); }
  .detail-charts, .eval-columns { grid-template-columns: 1fr; }
}
</style>
