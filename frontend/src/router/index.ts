import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import DashboardView from "../views/DashboardView.vue";
import RealtimeDetectView from "../views/RealtimeDetectView.vue";
import VideoUploadView from "../views/VideoUploadView.vue";
import SessionsView from "../views/SessionsView.vue";
import ReportsView from "../views/ReportsView.vue";
import ExerciseRulesView from "../views/ExerciseRulesView.vue";
import LoginView from "../views/LoginView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView, meta: { public: true } },
    { path: "/", component: DashboardView },
    { path: "/realtime", component: RealtimeDetectView },
    { path: "/upload", component: VideoUploadView },
    { path: "/sessions", component: SessionsView },
    { path: "/reports", component: ReportsView },
    { path: "/rules", component: ExerciseRulesView, meta: { adminOnly: true } }
  ]
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // 如果有 token 但还没获取到用户信息，尝试获取
  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser();
  }

  const isAuthenticated = authStore.isAuthenticated;
  const isAdmin = authStore.isAdmin;

  // 访问公开页面
  if (to.meta.public) {
    if (isAuthenticated) {
      // 已登录用户访问登录页，根据角色重定向
      next(isAdmin ? "/rules" : "/");
    } else {
      next();
    }
    return;
  }

  // 未登录用户访问需要认证的页面
  if (!isAuthenticated) {
    next("/login");
    return;
  }

  // 普通用户访问管理员页面
  if (to.meta.adminOnly && !isAdmin) {
    next("/");
    return;
  }

  next();
});
