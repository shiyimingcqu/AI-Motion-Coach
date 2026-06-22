<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">P</span>
        <div>
          <strong>PoseOps</strong>
          <small>运动姿态工程台</small>
        </div>
      </div>

      <nav>
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import {
  Activity,
  BarChart3,
  ClipboardList,
  Gauge,
  Settings2,
  UploadCloud
} from "lucide-vue-next";

const navItems = [
  { path: "/", label: "运行概览", icon: Gauge },
  { path: "/realtime", label: "实时检测", icon: Activity },
  { path: "/upload", label: "视频分析", icon: UploadCloud },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/reports", label: "统计报表", icon: BarChart3 },
  { path: "/rules", label: "规则配置", icon: Settings2 }
];
</script>
