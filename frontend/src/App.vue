<template>
  <div class="layout-stage">
    <Transition
      :name="layoutTransitionName"
      mode="out-in"
      @before-leave="lockPageScroll"
      @after-enter="unlockPageScroll"
    >
      <main v-if="!authStore.isAuthenticated || isStandalonePage" key="standalone" class="standalone-content">
        <RouterView />
      </main>

      <div v-else key="shell" class="shell">
        <aside class="sidebar">
          <div class="brand">
            <img class="brand-mark" src="@/assets/logo-poseprism.png" alt="姿态棱镜" />
            <div>
              <strong>姿态棱镜</strong>
              <small>运动姿态评估与纠错系统</small>
            </div>
          </div>

          <div class="sidebar-divider"></div>

          <!-- 导航项：超长时可滚动 -->
          <nav class="side-nav side-nav-scroll" aria-label="主导航">
            <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
              <component :is="item.icon" :size="18" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>

          <!-- 工具按钮：固定在侧边栏最下方 -->
          <div class="sidebar-utils">
<button
              v-if="!authStore.isAdmin"
              class="side-util-btn"
              type="button"
              @click="goToSettings"
            >
              <span class="side-icon-wrap"><Settings :size="14" /></span>
              <span>设置</span>
            </button>

            <button
              v-if="!authStore.isAdmin"
              class="side-util-btn"
              type="button"
              @click="goToProfile"
            >
              <UserAvatar size="sm" />
              <span>个人资料</span>
            </button>

            <div v-if="authStore.isAdmin" class="sidebar-user-info">
              <span class="avatar">{{ userInitial }}</span>
              <div class="sidebar-user-meta">
                <span class="username">{{ authStore.username }}</span>
                <span class="role">{{ roleText }}</span>
              </div>
              <button class="sidebar-logout-btn" type="button" @click="handleLogout">退出</button>
            </div>
          </div>
        </aside>

        <div class="workspace">
          <header class="topbar">
            <div>
              <strong>{{ pageTitle }}</strong>
              <span>今天 {{ todaySessions }} 次训练 · 平均分 {{ todayAvgScore }}</span>
            </div>
          </header>

          <main class="content">
            <RouterView />
          </main>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";
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
  Shield,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  TrendingUp,
  UploadCloud,
  Users
} from "lucide-vue-next";

import UserAvatar from "./components/UserAvatar.vue";
import { useAuthStore } from "./stores/auth";
import { getDashboardStats } from "./api/dashboard";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const standalonePaths: string[] = [];
const isStandalonePage = computed(() => standalonePaths.includes(route.path));
const layoutTransitionName = computed(() => route.meta.layoutTransition ?? "layout-instant");

function lockPageScroll() {
  if (layoutTransitionName.value !== "layout-instant") {
    document.documentElement.classList.add("page-transition-lock");
  }
}

function unlockPageScroll() {
  document.documentElement.classList.remove("page-transition-lock");
}

onUnmounted(unlockPageScroll);

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

const roleText = computed(() =>
  authStore.isAdmin ? "管理员" : "学生用户"
);

const userInitial = computed(() =>
  authStore.username ? authStore.username.charAt(0).toUpperCase() : "?"
);

const baseNavItems = [
  { path: "/", label: "首页总览", icon: Gauge },
  { path: "/realtime", label: "实时检测", icon: Activity },
  { path: "/upload", label: "视频分析", icon: UploadCloud },
  { path: "/feedback", label: "动作反馈", icon: Target },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/exercises", label: "动作库", icon: Dumbbell },
  { path: "/progress", label: "个人进步", icon: TrendingUp },
  { path: "/reports", label: "个人报告", icon: BarChart3 },
  { path: "/score-trends", label: "分数趋势", icon: BarChart3 },
  { path: "/motion-quality", label: "动作质量", icon: LineChart },
  { path: "/export", label: "报告导出", icon: FileDown },
];

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

const navItems = computed(() =>
  authStore.isAdmin ? adminNavItems : baseNavItems
);


// 从后端获取今日训练数据
const todaySessions = ref(0);
const todayAvgScore = ref(0);

async function fetchTodayStats() {
  try {
    const stats = await getDashboardStats();
    console.log("[App] dashboard stats:", stats);
    todaySessions.value = stats.today_sessions;
    todayAvgScore.value = stats.today_avg_score ?? stats.average_score;
  } catch (e) {
    console.error("[App] fetchTodayStats failed:", e);
  }
}

// 监听认证状态变化 + 组件挂载时立即执行
watch(
  () => authStore.isAuthenticated,
  (authenticated) => {
    if (authenticated) {
      fetchTodayStats();
    }
  },
  { immediate: true }
);


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
