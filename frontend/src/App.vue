<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">P</span>
        <div>
          <strong>PoseOps</strong>
          <small>运动姿态评估与纠错系统</small>
        </div>
      </div>

      <nav class="side-nav" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div>
          <strong>学生训练端</strong>
          <span>今天 3 次训练 · 平均分 86</span>
        </div>
        <label class="search-box">
          <Search :size="16" />
          <input type="search" placeholder="搜索动作、训练记录或报告" />
        </label>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="通知">
            <Bell :size="18" />
          </button>
          <span class="avatar">林</span>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Activity,
  BarChart3,
  Bell,
  ClipboardList,
  Dumbbell,
  Gauge,
  Search,
  UploadCloud
} from "lucide-vue-next";

const navItems = [
  { path: "/", label: "首页总览", icon: Gauge },
  { path: "/realtime", label: "实时检测", icon: Activity },
  { path: "/upload", label: "视频分析", icon: UploadCloud },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/reports", label: "个人报告", icon: BarChart3 },
  { path: "/rules", label: "动作规则", icon: Dumbbell }
];
</script>
