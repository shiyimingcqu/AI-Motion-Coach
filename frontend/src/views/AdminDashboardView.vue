<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Admin Overview</p>
        <h1>管理首页</h1>
        <p class="subtle">查看用户、训练、报告和动作规则的整体运行情况。</p>
      </div>
    </header>

    <section class="metrics-grid">
      <MetricTile label="用户总数" value="128" hint="本周新增 12 人" />
      <MetricTile label="今日训练" value="46" hint="实时检测 31 次" />
      <MetricTile label="视频分析" value="18" hint="平均处理 2.4 分钟" />
      <MetricTile label="系统平均分" value="84" hint="较上周 +2" />
    </section>

    <section class="admin-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Recent Activity</p>
            <h2>最近系统活动</h2>
          </div>
        </div>
        <div class="admin-list">
          <div v-for="item in activities" :key="item.time" class="admin-list-row">
            <span class="status-pill" :class="item.level">{{ item.type }}</span>
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.time }}</small>
            </div>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Risk Focus</p>
            <h2>高频动作问题</h2>
          </div>
        </div>
        <div class="distribution-list">
          <div v-for="item in errorStats" :key="item.name">
            <span>{{ item.name }}</span>
            <strong>{{ item.count }} 次</strong>
            <i :style="{ width: `${item.rate}%` }"></i>
          </div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Work Queue</p>
          <h2>待处理事项</h2>
        </div>
      </div>
      <div class="admin-action-grid">
        <div v-for="item in tasks" :key="item.title" class="admin-action-card">
          <strong>{{ item.title }}</strong>
          <span>{{ item.desc }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import MetricTile from "../components/MetricTile.vue";

const activities = [
  { type: "用户", title: "林同学完成深蹲训练，平均分 91", time: "10 分钟前", level: "good" },
  { type: "报告", title: "系统生成 3 份训练评估报告", time: "32 分钟前", level: "idle" },
  { type: "规则", title: "深蹲模板 v1 进入使用中状态", time: "1 小时前", level: "good" },
  { type: "异常", title: "2 条视频分析任务耗时偏长", time: "2 小时前", level: "danger" }
];

const errorStats = [
  { name: "下蹲深度不足", count: 42, rate: 84 },
  { name: "膝盖内扣", count: 31, rate: 62 },
  { name: "身体塌腰", count: 24, rate: 48 },
  { name: "节奏过快", count: 18, rate: 36 }
];

const tasks = [
  { title: "审核新增模板", desc: "2 个标准动作模板等待确认启用。" },
  { title: "查看低分用户", desc: "5 名用户近 7 天平均分低于 70。" },
  { title: "维护动作规则", desc: "建议检查深蹲和俯卧撑阈值配置。" }
];
</script>
