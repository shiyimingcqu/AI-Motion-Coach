<template>
  <RouterView v-if="!authStore.isAuthenticated" />

  <div v-else class="shell app-dashboard-shell">
    <aside class="sidebar app-sidebar">
      <div class="app-brand">
        <strong>Pose Training AI</strong>
      </div>

      <nav class="app-nav" aria-label="Main navigation">
        <section v-for="group in navGroups" :key="group.title" class="app-nav-group">
          <button class="app-nav-title" type="button">
            <span>{{ group.title }}</span>
            <ChevronUp :size="15" />
          </button>

          <div class="app-nav-items">
            <RouterLink
              v-for="item in group.items"
              :key="item.label"
              :to="item.path"
              class="app-nav-link"
            >
              <component :is="item.icon" :size="16" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </div>
        </section>
      </nav>
    </aside>

    <div class="workspace app-workspace">
      <header class="topbar app-topbar">
        <div class="app-topbar-title">
          <strong>{{ pageTitle }}</strong>
          <span>{{ pageSubtitle }}</span>
        </div>

        <div class="app-topbar-actions">
          <span class="system-pill">
            <i />
            System Online
          </span>
          <button class="logout-button" type="button" @click="handleLogout">
            退出
          </button>
        </div>
      </header>

      <main class="content app-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import {
  Activity,
  BarChart3,
  ClipboardList,
  Dumbbell,
  FileDown,
  FileText,
  Gauge,
  LineChart,
  ListChecks,
  Settings,
  SlidersHorizontal,
  Target,
  TrendingUp,
  UploadCloud,
  UsersRound,
  Video,
  ChevronUp
} from "lucide-vue-next";

type NavItem = {
  label: string;
  path: string;
  icon: unknown;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const pageTitleMap: Record<string, string> = {
  "/": "Overview / 总览",
  "/realtime": "Realtime Detection / 实时姿态检测",
  "/upload": "Video Upload / 视频上传分析",
  "/feedback": "Error Feedback / 动作错误反馈",
  "/sessions": "Training Sessions / 训练记录",
  "/exercises": "Exercise Library / 动作库",
  "/progress": "Personal Progress / 个人进步趋势",
  "/reports": "Evaluation Reports / 评估报告",
  "/score-trends": "Score Trends / 分数趋势",
  "/motion-quality": "Motion Quality Metrics / 动作质量指标",
  "/export": "Export Reports / 报告导出",
  "/rules": "Exercise Rules / 动作规则配置",
  "/users": "User Management / 用户管理",
  "/settings": "Settings / 系统设置"
};

const pageTitle = computed(() => pageTitleMap[route.path] ?? "Pose Training AI");
const pageSubtitle = computed(() =>
  authStore.isAdmin
    ? "System Management / 管理后台"
    : "Student Training Workspace / 学生训练工作台"
);

const navGroups = computed<NavGroup[]>(() => [
  {
    title: "Dashboard / 控制台",
    items: [
      { path: "/", label: "Overview / 总览", icon: Gauge }
    ]
  },
  {
    title: "Pose Analysis / 姿态分析",
    items: [
      { path: "/realtime", label: "Realtime Detection / 实时姿态检测", icon: Video },
      { path: "/upload", label: "Video Upload / 视频上传分析", icon: UploadCloud },
      { path: "/feedback", label: "Error Feedback / 动作错误反馈", icon: Target }
    ]
  },
  {
    title: "Training Center / 训练中心",
    items: [
      { path: "/sessions", label: "Training Sessions / 训练记录", icon: ListChecks },
      { path: "/exercises", label: "Exercise Library / 动作库", icon: Dumbbell },
      { path: "/progress", label: "Personal Progress / 个人进步", icon: TrendingUp }
    ]
  },
  {
    title: "Reports & Insights / 报告分析",
    items: [
      { path: "/reports", label: "Evaluation Reports / 评估报告", icon: FileText },
      { path: "/score-trends", label: "Score Trends / 分数趋势", icon: BarChart3 },
      { path: "/motion-quality", label: "Motion Quality / 动作质量指标", icon: LineChart },
      { path: "/export", label: "Export Reports / 报告导出", icon: FileDown }
    ]
  },
  {
    title: "System Management / 系统管理",
    items: [
      { path: "/rules", label: "Exercise Rules / 动作规则配置", icon: SlidersHorizontal },
      { path: "/users", label: "User Management / 用户管理", icon: UsersRound },
      { path: "/settings", label: "Settings / 系统设置", icon: Settings },
      // { path: "/realtime", label: "Skeleton Tracking / 骨架关键点", icon: Activity }
    ]
  }
]);

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>
