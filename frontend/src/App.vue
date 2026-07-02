<template>
  <RouterView v-if="!authStore.isAuthenticated" />

  <!-- 管理员后台布局 -->
  <div v-else-if="authStore.isAdmin" class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">P</span>
        <div>
          <strong>PoseOps</strong>
          <small>运动姿态评估与纠错系统</small>
        </div>
      </div>

      <nav class="side-nav" aria-label="主导航">
        <RouterLink v-for="item in adminNavItems" :key="item.path" :to="item.path">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
    </nav>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div>
          <strong>{{ adminPageTitle }}</strong>
          <span>用户、训练、报告与规则管理</span>
        </div>
        <div class="topbar-actions">
          <div class="user-info">
            <span class="avatar">{{ userInitial }}</span>
            <div class="user-meta">
              <span class="username">{{ authStore.username }}</span>
              <span class="role">管理员</span>
            </div>
            <button class="logout-button" type="button" @click="handleLogout">退出</button>
          </div>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>

  <!-- 普通用户工作台布局 -->
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
          <span>Student Training Workspace / 学生训练工作台</span>
        </div>

        <div class="app-topbar-actions">
          <span class="system-pill">
            <i />
            System Online
          </span>
          <button class="icon-button" type="button" aria-label="系统设置" @click="goToSettings">
            <Settings :size="18" />
          </button>
          <button class="avatar avatar-button" type="button" aria-label="个人资料" @click="goToProfile">
            <UserAvatar size="sm" />
          </button>
          <button class="logout-button" type="button" @click="handleLogout">退出</button>
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
  Layers,
  LineChart,
  ListChecks,
  Settings,
  Shield,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  TrendingUp,
  UploadCloud,
  Users,
  Video,
  ChevronUp
} from "lucide-vue-next";

import UserAvatar from "./components/UserAvatar.vue";

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
  "/profile": "Profile / 个人资料",
  "/settings": "Settings / 系统设置"
};

const adminPageTitleMap: Record<string, string> = {
  "/admin": "管理首页",
  "/admin/users": "用户管理",
  "/admin/admins": "管理员管理",
  "/admin/sessions": "训练记录",
  "/admin/reports": "评估报告",
  "/admin/rules": "动作规则",
  "/admin/templates": "模板管理",
  "/admin/settings": "系统设置"
};

const pageTitle = computed(() => pageTitleMap[route.path] ?? "Pose Training AI");
const adminPageTitle = computed(() => adminPageTitleMap[route.path] ?? "管理后台");

const userInitial = computed(() =>
  authStore.username ? authStore.username.charAt(0).toUpperCase() : "?"
);

const adminNavItems = [
  { path: "/admin", label: "管理首页", icon: ShieldCheck },
  { path: "/admin/users", label: "用户管理", icon: Users },
  { path: "/admin/admins", label: "管理员管理", icon: Shield },
  { path: "/admin/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/admin/reports", label: "评估报告", icon: FileText },
  { path: "/admin/rules", label: "动作规则", icon: Dumbbell },
  { path: "/admin/templates", label: "模板管理", icon: Layers },
  { path: "/admin/settings", label: "系统设置", icon: SlidersHorizontal }
];

const navGroups = computed<NavGroup[]>(() => [
  {
    title: "Dashboard / 控制台",
    items: [{ path: "/", label: "Overview / 总览", icon: Gauge }]
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
  }
]);

function goToProfile() {
  router.push("/profile");
}

function goToSettings() {
  router.push("/settings");
}

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 8px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.user-meta .username {
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
}

.user-meta .role {
  font-size: 11px;
  color: #64748b;
}

.logout-button {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  border-color: #ef4444;
  color: #ef4444;
}
</style>
