/// <reference types="vite/client" />

declare module "vue-router" {
  interface RouteMeta {
    layoutTransition?: "page-soft-forward" | "page-soft-back";
  }
}

export {};
