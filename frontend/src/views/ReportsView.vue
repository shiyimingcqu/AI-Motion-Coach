<template>
  <div class="evaluation-page">
    <header class="section-page-header">
      <div>
        <h1>Evaluation Reports / 评估报告</h1>
        <p>Comprehensive analysis and performance reports</p>
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
        <input v-model="keyword" type="search" placeholder="Search reports... / 搜索报告..." />
      </label>
      <select v-model="typeFilter">
        <option value="">All Types</option>
        <option value="Monthly">Monthly</option>
        <option value="Weekly">Weekly</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">Newest</option>
        <option value="asc">Oldest</option>
      </select>
    </section>

    <section class="report-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="5" text="正在加载报告..." />
      <StateDisplay v-else-if="filteredReports.length === 0" type="empty" title="暂无报告" text="完成训练后，报告将自动生成" />
      <table v-else class="report-table">
        <thead>
          <tr>
            <th>REPORT / 报告名称</th>
            <th>TYPE / 类型</th>
            <th>DATE / 日期</th>
            <th>COVERAGE / 覆盖范围</th>
            <th>AVG SCORE / 平均分</th>
            <th>SIZE / 大小</th>
            <th>ACTIONS / 操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="report in filteredReports" :key="report.id || report.title">
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
              <span>{{ report.exercises_count || 0 }} exercises</span>
              <small>{{ report.sessions_count || 0 }} sessions</small>
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
                <Eye :size="16" />
                <Download :size="16" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="automated-report-card">
      <span class="blue-solid"><ClipboardList :size="25" /></span>
      <div>
        <h2>Automated Report Generation / 自动报告生成</h2>
        <p>Reports are automatically generated weekly and monthly from training session data.</p>
        <button class="blue-action-button small-blue-button" type="button">Learn More</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ClipboardList, Download, Eye, FileText, Filter } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getPersonalReport } from "../api/reports";

interface ReportItem {
  id: string;
  title: string;
  subtitle: string;
  type: string;
  date: string;
  exercises_count: number;
  sessions_count: number;
  average_score: number;
  size: string;
}

const reports = ref<ReportItem[]>([]);
const loading = ref(true);
const keyword = ref("");
const typeFilter = ref("");
const sortOrder = ref("desc");

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
    { label: "Total Reports / 总报告数", value: total },
    { label: "Avg Score / 平均分", value: avgScore.toFixed(1) },
    { label: "Exercises / 动作数", value: reports.value.reduce((s, r) => s + (r.exercises_count || 0), 0) },
    { label: "Sessions / 训练次数", value: reports.value.reduce((s, r) => s + (r.sessions_count || 0), 0) },
  ];
});

onMounted(async () => {
  try {
    const data = await getPersonalReport();
    // Transform personal report data into ReportItem format
    const item: ReportItem = {
      id: "report-personal",
      title: "Personal Performance Report",
      subtitle: "个人训练表现报告",
      type: "Monthly",
      date: new Date().toISOString().slice(0, 10),
      exercises_count: data.recent_sessions?.length || 0,
      sessions_count: data.total_sessions || 0,
      average_score: data.average_score || 0,
      size: `${data.total_sessions || 0} sessions`,
    };
    reports.value = data.total_sessions > 0 ? [item] : [];
  } catch {
    reports.value = [];
  } finally {
    loading.value = false;
  }
});
</script>
