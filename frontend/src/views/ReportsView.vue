<template>
  <div class="evaluation-page">
    <header class="section-page-header">
      <div>
        <h1>Evaluation Reports / 评估报告</h1>
        <p>Comprehensive analysis and performance reports</p>
      </div>
      <button class="blue-action-button" type="button">Generate Report</button>
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
        <input type="search" placeholder="Search reports... / 搜索报告..." />
      </label>
      <select><option>All Types</option></select>
      <select><option>All Status</option></select>
    </section>

    <section class="report-table-card">
      <table class="report-table">
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
          <tr v-for="report in reports" :key="report.title">
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
              <span>{{ report.exercises }} exercises</span>
              <small>{{ report.sessions }} sessions</small>
            </td>
            <td>
              <div class="score-progress">
                <i :class="report.score >= 90 ? 'progress-green' : 'progress-blue'" :style="{ width: `${report.score}%` }" />
                <strong>{{ report.score }}</strong>
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
        <p>Reports are automatically generated weekly and monthly. You can also create custom reports for specific exercises or time periods.</p>
        <button class="blue-action-button small-blue-button" type="button">Learn More</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ClipboardList, Download, Eye, FileText, Filter } from "lucide-vue-next";

const stats = [
  { label: "Total Reports / 总报告数", value: 47 },
  { label: "This Month / 本月", value: 5 },
  { label: "Published / 已发布", value: 45 },
  { label: "Drafts / 草稿", value: 2 }
];

const reports = [
  { title: "Monthly Performance Report - June 2026", subtitle: "6月月度表现报告", type: "Monthly", date: "2026-06-25", exercises: 8, sessions: 22, score: 88, size: "2.4 MB" },
  { title: "Squat Technique Analysis", subtitle: "深蹲技术分析", type: "Exercise-Specific", date: "2026-06-20", exercises: 1, sessions: 15, score: 90, size: "1.8 MB" },
  { title: "Weekly Progress Summary - Week 25", subtitle: "第25周进度总结", type: "Weekly", date: "2026-06-18", exercises: 6, sessions: 5, score: 87, size: "1.2 MB" },
  { title: "Core Strength Assessment", subtitle: "核心力量评估", type: "Assessment", date: "2026-06-15", exercises: 4, sessions: 8, score: 85, size: "1.5 MB" },
  { title: "Upper Body Performance Q2 2026", subtitle: "上肢表现Q2 2026", type: "Quarterly", date: "2026-06-10", exercises: 12, sessions: 45, score: 86, size: "3.2 MB" }
];
</script>
