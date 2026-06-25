<template>
  <div class="export-page">
    <header class="section-page-header">
      <div>
        <h1>Export Reports / 报告导出</h1>
        <p>Generate and download customized reports</p>
      </div>
    </header>

    <section class="export-layout">
      <div class="export-main">
        <article class="export-card">
          <h2>Export Format / 导出格式</h2>
          <div class="format-grid">
            <button v-for="format in formats" :key="format.title" type="button" class="format-option">
              <span class="settings-icon tone-blue">
                <component :is="format.icon" :size="25" />
              </span>
              <div>
                <strong>{{ format.title }}</strong>
                <small>{{ format.desc }}</small>
              </div>
            </button>
          </div>
        </article>

        <article class="export-card">
          <h2>Report Configuration / 报告配置</h2>
          <label class="export-field">
            Date Range / 日期范围
            <select><option>Last 30 Days</option></select>
          </label>
          <div class="include-list">
            <span>Include Sections / 包含部分</span>
            <label v-for="item in sections" :key="item">
              <input type="checkbox" checked />
              {{ item }}
            </label>
          </div>
        </article>
      </div>

      <aside class="quick-export-card">
        <h2>Quick Export / 快速导出</h2>
        <button class="quick-button active" type="button">
          <FileDown :size="20" />
          Export Current View
        </button>
        <button class="quick-button" type="button">
          <ClipboardList :size="20" />
          Monthly Summary
        </button>
        <button class="quick-button" type="button">
          <FileSpreadsheet :size="20" />
          All Data (CSV)
        </button>

        <div class="recent-export-box">
          <h3>Recent Exports / 最近导出</h3>
          <div v-for="file in recentFiles" :key="file">
            <span>{{ file }}</span>
            <Download :size="16" />
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  ClipboardList,
  Download,
  FileDown,
  FileImage,
  FileSpreadsheet,
  FileText
} from "lucide-vue-next";

const formats = [
  { title: "PDF Document", desc: "Comprehensive report with charts", icon: FileText },
  { title: "Excel Spreadsheet", desc: "Raw data for analysis", icon: FileSpreadsheet },
  { title: "CSV File", desc: "Simple data export", icon: FileSpreadsheet },
  { title: "Image Bundle", desc: "Charts and visualizations", icon: FileImage }
];

const sections = ["Score Summary", "Exercise Breakdown", "Trend Charts", "Error Analysis", "Recommendations"];
const recentFiles = ["June_Report.pdf", "Weekly_Data.xlsx", "Score_Trends.png"];
</script>
