import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import RealtimeDetectView from "../views/RealtimeDetectView.vue";
import VideoUploadView from "../views/VideoUploadView.vue";
import SessionsView from "../views/SessionsView.vue";
import ReportsView from "../views/ReportsView.vue";
import ExerciseRulesView from "../views/ExerciseRulesView.vue";
import ProfileView from "../views/ProfileView.vue";
import SettingsView from "../views/SettingsView.vue";

const STANDALONE_PATHS = ["/profile", "/settings"];

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DashboardView },
    { path: "/realtime", component: RealtimeDetectView },
    { path: "/upload", component: VideoUploadView },
    { path: "/sessions", component: SessionsView },
    { path: "/reports", component: ReportsView },
    { path: "/rules", component: ExerciseRulesView },
    { path: "/profile", component: ProfileView },
    { path: "/settings", component: SettingsView }
  ]
});

router.beforeEach((to, from, next) => {
  const toStandalone = STANDALONE_PATHS.includes(to.path);
  const fromStandalone = STANDALONE_PATHS.includes(from.path);

  if (toStandalone && !fromStandalone) {
    to.meta.layoutTransition = "page-soft-forward";
  } else if (!toStandalone && fromStandalone) {
    to.meta.layoutTransition = "page-soft-back";
  } else {
    to.meta.layoutTransition = undefined;
  }

  next();
});
