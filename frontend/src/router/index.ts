import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import RealtimeDetectView from "../views/RealtimeDetectView.vue";
import VideoUploadView from "../views/VideoUploadView.vue";
import SessionsView from "../views/SessionsView.vue";
import ReportsView from "../views/ReportsView.vue";
import ExerciseRulesView from "../views/ExerciseRulesView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DashboardView },
    { path: "/realtime", component: RealtimeDetectView },
    { path: "/upload", component: VideoUploadView },
    { path: "/sessions", component: SessionsView },
    { path: "/reports", component: ReportsView },
    { path: "/rules", component: ExerciseRulesView }
  ]
});
