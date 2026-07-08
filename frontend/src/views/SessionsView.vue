<template>
  <div class="tr-page">
    <!-- 顶部：标题 + 数据卡 -->
    <header class="tr-top">
      <div class="tr-top-text">
        <h1>训练记录</h1>
        <p>记录每一次的坚持，见证你的进步</p>
      </div>
      <div class="tr-top-stats">
        <div class="tr-top-stat">
          <div class="tr-top-icon"><CalendarDays :size="20" /></div>
          <div>
            <span class="tr-top-label">本月训练</span>
            <strong>{{ monthSessions }} <small>次</small></strong>
          </div>
        </div>
        <div class="tr-top-stat">
          <div class="tr-top-icon"><Star :size="20" /></div>
          <div>
            <span class="tr-top-label">平均得分</span>
            <strong>{{ avgScoreDisplay }} <small>分</small></strong>
          </div>
        </div>
        <div class="tr-top-stat">
          <div class="tr-top-icon"><Flame :size="20" /></div>
          <div>
            <span class="tr-top-label">累计训练</span>
            <strong>{{ totalDays }} <small>天</small></strong>
          </div>
        </div>
        <div class="tr-top-user">
          <UserAvatar size="sm" />
          <span>{{ authStore.username || "深蹲" }}</span>
          <ChevronDown :size="14" />
        </div>
      </div>
    </header>

    <!-- 筛选 tabs -->
    <TrainingFilterBar v-model="filterTab" />

    <!-- 下拉筛选条件（动作/时间） -->
    <div v-if="filterTab !== 'all'" class="tr-filter-extras">
      <template v-if="filterTab === 'exercise'">
        <label>
          <span>动作</span>
          <select v-model="exerciseFilter">
            <option value="">全部动作</option>
            <option v-for="(m, k) in EXERCISE_META" :key="k" :value="k">{{ m.name }}</option>
          </select>
        </label>
      </template>
      <template v-else>
        <label>
          <span>开始</span>
          <input type="date" v-model="dateFrom" />
        </label>
        <label>
          <span>结束</span>
          <input type="date" v-model="dateTo" />
        </label>
      </template>
      <button type="button" class="tr-reset" @click="resetFilter">重置</button>
    </div>

    <!-- 三栏：中间记录 + 右侧日历/趋势 -->
    <div class="tr-main">
      <div class="tr-center">
        <!-- 4 张统计卡 -->
        <TrainingSummaryCards
          :total-count="monthSessions"
          :total-hours="totalHours"
          :avg-score="avgScoreNumber"
          :completion-rate="completionRate"
        />

        <!-- 列表 -->
        <TrainingRecordList
          :records="displayedRecords"
          :loading="loading"
          :has-more="hasMore"
          @openDetail="openDetail"
          @loadMore="loadMore"
          @export="exportRecords"
        />
      </div>

      <aside class="tr-right">
        <TrainingCalendar
          :year="calYear"
          :month="calMonth"
          :selected-key="selectedDateKey"
          :record-map="calendarRecordMap"
          @prev="calPrev"
          @next="calNext"
          @select="selectDate"
        />
        <BodyTrendCard
          :hours="totalHours"
          :avg-score="avgScoreNumber"
          :completion="completionRate"
          :calories="caloriesBurned"
        />
        <TrainingEncouragementCard @goal="goToGoal" />
      </aside>
    </div>

    <!-- 详情弹窗（保留原功能） -->
    <div v-if="showDetail" class="tr-modal-mask" @click.self="closeDetail">
      <div class="tr-modal">
        <header class="tr-modal-head">
          <div>
            <h3>{{ detail?.exercise_name }} 评估报告</h3>
            <p>{{ detail?.created_at?.slice(0, 10) }} · {{ detail?.calories_burned }} kcal</p>
          </div>
          <button class="tr-modal-close" type="button" @click="closeDetail">
            <X :size="20" />
          </button>
        </header>

        <StateDisplay v-if="detailLoading" type="loading" text="加载报告详情..." />

        <template v-else-if="detail">
          <div class="tr-modal-score-row">
            <div class="tr-modal-circle">
              <strong>{{ detail.average_score }}</strong>
              <span>综合评分</span>
            </div>
            <div class="tr-modal-grade" :class="gradeClass(detail.evaluation.grade)">
              {{ detail.evaluation.grade_label }}
            </div>
            <div class="tr-modal-metrics">
              <div><span>有效次数</span><strong>{{ detail.valid_count }}/{{ detail.total_count }}</strong></div>
              <div><span>错误次数</span><strong>{{ detail.error_count }}</strong></div>
              <div><span>训练时长</span><strong>{{ detail.evaluation.duration_minutes }} min</strong></div>
              <div><span>卡路里</span><strong>{{ detail.calories_burned }} kcal</strong></div>
            </div>
          </div>

          <p class="tr-modal-summary">{{ detail.evaluation.summary }}</p>

          <div class="tr-modal-charts">
            <div ref="detailRadarRef" class="tr-modal-chart" />
            <div ref="detailRepRef" class="tr-modal-chart" />
          </div>

          <div class="tr-modal-cols">
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  CalendarDays,
  ChevronDown,
  Flame,
  Star,
  X,
} from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import UserAvatar from "@/components/UserAvatar.vue";
import TrainingSummaryCards from "@/components/training-records/TrainingSummaryCards.vue";
import TrainingFilterBar from "@/components/training-records/TrainingFilterBar.vue";
import TrainingRecordList from "@/components/training-records/TrainingRecordList.vue";
import TrainingCalendar from "@/components/training-records/TrainingCalendar.vue";
import BodyTrendCard from "@/components/training-records/BodyTrendCard.vue";
import TrainingEncouragementCard from "@/components/training-records/TrainingEncouragementCard.vue";
import { getSessions, type SessionRecord, type SessionsResponse } from "@/api/sessions";
import { getReportDetail, type ReportDetail } from "@/api/reports";
import { useAuthStore } from "@/stores/auth";
import { EXERCISE_META, MOCK_SESSIONS, formatHours, getDateKey } from "@/data/trainingRecords";

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

interface UISession extends SessionRecord {
  calories?: number;
}

const sessions = ref<UISession[]>([]);
const loading = ref(true);
const errorMsg = ref("");

// 筛选
const filterTab = ref<"all" | "exercise" | "date">("all");
const exerciseFilter = ref("");
const dateFrom = ref("");
const dateTo = ref("");

// 列表分页
const PAGE_SIZE = 5;
const page = ref(1);

// 日历
const calYear = ref(new Date().getFullYear());
const calMonth = ref(new Date().getMonth());
const selectedDateKey = ref<string | null>(null);

// 详情弹窗
const showDetail = ref(false);
const detailLoading = ref(false);
const detail = ref<ReportDetail | null>(null);
const detailRadarRef = ref<HTMLElement | null>(null);
const detailRepRef = ref<HTMLElement | null>(null);
let detailCharts: echarts.ECharts[] = [];

// 派生：当前 month count
const monthSessions = computed(() => {
  const now = new Date();
  return sessions.value.filter((s) => {
    const d = new Date(s.created_at);
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  }).length;
});

const totalDays = computed(() => {
  const set = new Set(sessions.value.map((s) => getDateKey(s.created_at)));
  return set.size;
});

const avgScoreNumber = computed(() => {
  if (sessions.value.length === 0) return 0;
  return Math.round(
    sessions.value.reduce((s, r) => s + r.average_score, 0) / sessions.value.length,
  );
});
const avgScoreDisplay = computed(() => avgScoreNumber.value.toString());

const totalMinutes = computed(() =>
  sessions.value.reduce((s, r) => s + (r.duration_seconds || 0) / 60, 0),
);
const totalHours = computed(() => Number(formatHours(totalMinutes.value)));

const completionRate = computed(() => {
  const total = sessions.value.reduce((s, r) => s + (r.total_count || 0), 0);
  const valid = sessions.value.reduce((s, r) => s + (r.valid_count || 0), 0);
  if (!total) return 0;
  return Math.round((valid / total) * 100);
});

const caloriesBurned = computed(() =>
  sessions.value.reduce((s, r) => s + (r.calories || 0), 0) || 3260,
);

// 列表：筛选 + 排序 + 分页
const filteredSessions = computed(() => {
  let list = [...sessions.value];
  if (exerciseFilter.value) {
    list = list.filter((s) => s.exercise === exerciseFilter.value);
  }
  if (dateFrom.value) {
    list = list.filter((s) => getDateKey(s.created_at) >= dateFrom.value);
  }
  if (dateTo.value) {
    list = list.filter((s) => getDateKey(s.created_at) <= dateTo.value);
  }
  if (selectedDateKey.value) {
    list = list.filter((s) => getDateKey(s.created_at) === selectedDateKey.value);
  }
  return list.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
});

const displayedRecords = computed(() => filteredSessions.value.slice(0, page.value * PAGE_SIZE));
const hasMore = computed(() => displayedRecords.value.length < filteredSessions.value.length);

function loadMore() {
  page.value += 1;
}

function resetFilter() {
  exerciseFilter.value = "";
  dateFrom.value = "";
  dateTo.value = "";
  selectedDateKey.value = null;
  page.value = 1;
}

watch([exerciseFilter, dateFrom, dateTo, selectedDateKey], () => {
  page.value = 1;
});

// 日历派生：date -> best score
const calendarRecordMap = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {};
  for (const s of sessions.value) {
    const k = getDateKey(s.created_at);
    if (!map[k] || s.average_score > map[k]) map[k] = s.average_score;
  }
  return map;
});

function calPrev() {
  if (calMonth.value === 0) {
    calMonth.value = 11;
    calYear.value -= 1;
  } else {
    calMonth.value -= 1;
  }
}
function calNext() {
  if (calMonth.value === 11) {
    calMonth.value = 0;
    calYear.value += 1;
  } else {
    calMonth.value += 1;
  }
}
function selectDate(key: string) {
  selectedDateKey.value = selectedDateKey.value === key ? null : key;
}

// 详情弹窗
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
      series: [
        {
          type: "radar",
          data: [{ value: data.charts.quality_radar.values, areaStyle: { color: "rgba(59,130,246,0.2)" } }],
        },
      ],
    });
    detailCharts.push(radar);
  }
  if (detailRepRef.value) {
    const rep = echarts.init(detailRepRef.value);
    rep.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["40%", "65%"],
          data: data.charts.rep_breakdown.labels.map((name, i) => ({
            name,
            value: data.charts.rep_breakdown.values[i],
          })),
          color: ["#22c55e", "#ef4444"],
        },
      ],
    });
    detailCharts.push(rep);
  }
}
async function openDetail(sessionId: string) {
  showDetail.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    const data = await getReportDetail(sessionId);
    detail.value = data;
    await nextTick();
    if (data) renderDetailCharts(data);
  } catch {
    detail.value = null;
  } finally {
    detailLoading.value = false;
  }
}
function closeDetail() {
  showDetail.value = false;
  detail.value = null;
  disposeDetailCharts();
}
function gradeClass(grade?: string) {
  if (grade === "A") return "grade-a";
  if (grade === "B") return "grade-b";
  if (grade === "C") return "grade-c";
  return "grade-d";
}

// 导出 CSV
function exportRecords() {
  if (filteredSessions.value.length === 0) {
    window.alert("暂无记录可导出");
    return;
  }
  const header = ["动作", "得分", "时长(秒)", "有效次数", "总次数", "错误次数", "日期"];
  const rows = filteredSessions.value.map((s) => [
    EXERCISE_META[s.exercise]?.name || s.exercise,
    s.average_score,
    s.duration_seconds,
    s.valid_count,
    s.total_count,
    s.error_count,
    s.created_at,
  ]);
  const csv = [header, ...rows]
    .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `training-records-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function goToGoal() {
  router.push("/profile");
}

async function loadSessions() {
  loading.value = true;
  errorMsg.value = "";
  try {
    const data: SessionsResponse = await getSessions({ limit: 100, offset: 0 });
    if (data.items && data.items.length > 0) {
      sessions.value = data.items as UISession[];
    } else {
      // 接口无数据，使用 mock
      sessions.value = MOCK_SESSIONS as UISession[];
    }
  } catch {
    // 接口失败，使用 mock
    sessions.value = MOCK_SESSIONS as UISession[];
  } finally {
    loading.value = false;
  }
}

onMounted(loadSessions);
onBeforeUnmount(disposeDetailCharts);
</script>

<style scoped>
.tr-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 0 24px;
}

/* ===== 顶部 ===== */
.tr-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.tr-top-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #15172A;
  letter-spacing: -0.4px;
}

.tr-top-text p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #667085;
}

.tr-top-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tr-top-stat,
.tr-top-user {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 68px;
  padding: 0 16px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(45, 35, 90, 0.04);
  flex-shrink: 0;
}

.tr-top-stat > div:last-child {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.tr-top-label {
  font-size: 11px;
  color: #98a2b3;
}

.tr-top-stat strong {
  font-size: 16px;
  color: #15172A;
  font-weight: 800;
}

.tr-top-stat strong small {
  font-size: 11px;
  color: #667085;
  font-weight: 500;
  margin-left: 1px;
}

.tr-top-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #f1ecff;
  color: #6C3BFF;
  flex-shrink: 0;
}

.tr-top-user {
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #15172A;
  cursor: pointer;
}

.tr-top-user svg { color: #98a2b3; }

/* ===== 筛选 tabs ===== */
.tr-filter-extras {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 12px;
  flex-wrap: wrap;
}

.tr-filter-extras label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #667085;
}

.tr-filter-extras input,
.tr-filter-extras select {
  height: 32px;
  padding: 0 10px;
  border: 1px solid #eef0f6;
  border-radius: 8px;
  background: #ffffff;
  font-size: 13px;
  color: #15172A;
}

.tr-reset {
  margin-left: auto;
  height: 32px;
  padding: 0 14px;
  background: #f1ecff;
  color: #6C3BFF;
  border: 0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

/* ===== 主体三栏 ===== */
.tr-main {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
  align-items: start;
}

.tr-center {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.tr-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 16px;
}

@media (max-width: 1280px) {
  .tr-main { grid-template-columns: 1fr 320px; }
}

@media (max-width: 1000px) {
  .tr-main { grid-template-columns: 1fr; }
  .tr-right { position: static; }
}

/* ===== 详情弹窗 ===== */
.tr-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.5);
  display: grid;
  place-items: center;
  padding: 24px;
}

.tr-modal {
  width: 100%;
  max-width: 820px;
  max-height: 90vh;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 12px 48px rgba(15, 23, 42, 0.18);
}

.tr-modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.tr-modal-head h3 {
  color: #15172A;
  margin: 0 0 4px;
  font-size: 18px;
}

.tr-modal-head p {
  color: #667085;
  margin: 0;
  font-size: 13px;
}

.tr-modal-close {
  background: none;
  border: 0;
  color: #98a2b3;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.tr-modal-close:hover { background: #f1f3f9; color: #475569; }

.tr-modal-score-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tr-modal-circle {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  border: 3px solid #6C3BFF;
  display: grid;
  place-items: center;
  text-align: center;
}

.tr-modal-circle strong {
  font-size: 28px;
  color: #15172A;
  line-height: 1;
}

.tr-modal-circle span {
  font-size: 11px;
  color: #667085;
}

.tr-modal-grade {
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 16px;
}

.tr-modal-grade.grade-a { background: rgba(16,185,129,0.12); color: #16a34a; }
.tr-modal-grade.grade-b { background: rgba(59,130,246,0.12); color: #2563eb; }
.tr-modal-grade.grade-c { background: rgba(245,158,11,0.12); color: #d97706; }
.tr-modal-grade.grade-d { background: rgba(239,68,68,0.12); color: #dc2626; }

.tr-modal-metrics {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.tr-modal-metrics div {
  display: grid;
  gap: 2px;
}

.tr-modal-metrics span {
  color: #667085;
  font-size: 11px;
}

.tr-modal-metrics strong {
  color: #15172A;
  font-size: 16px;
}

.tr-modal-summary {
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px;
  padding: 12px 16px;
  background: #f7f8fc;
  border-radius: 8px;
}

.tr-modal-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.tr-modal-chart {
  height: 220px;
  background: #f7f8fc;
  border-radius: 10px;
}

.tr-modal-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tr-modal-cols article {
  padding: 14px;
  border-radius: 10px;
  background: #f7f8fc;
  border: 1px solid #eef0f6;
}

.tr-modal-cols h4 {
  color: #15172A;
  margin: 0 0 8px;
  font-size: 13px;
}

.tr-modal-cols ul {
  margin: 0;
  padding-left: 16px;
  color: #475569;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .tr-modal-charts,
  .tr-modal-cols { grid-template-columns: 1fr; }
}
</style>
