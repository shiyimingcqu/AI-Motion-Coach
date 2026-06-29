// vite.config.ts
import { defineConfig } from "file:///sessions/nifty-relaxed-feynman/mnt/%E8%BF%90%E5%8A%A8%E5%A7%BF%E6%80%81%E8%AF%84%E4%BC%B0%E4%B8%8E%E7%BA%A0%E9%94%99%E7%B3%BB%E7%BB%9F/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///sessions/nifty-relaxed-feynman/mnt/%E8%BF%90%E5%8A%A8%E5%A7%BF%E6%80%81%E8%AF%84%E4%BC%B0%E4%B8%8E%E7%BA%A0%E9%94%99%E7%B3%BB%E7%BB%9F/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import path from "path";
var __vite_injected_original_dirname = "/sessions/nifty-relaxed-feynman/mnt/\u8FD0\u52A8\u59FF\u6001\u8BC4\u4F30\u4E0E\u7EA0\u9519\u7CFB\u7EDF/frontend";
var vite_config_default = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "./src")
    }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvc2Vzc2lvbnMvbmlmdHktcmVsYXhlZC1mZXlubWFuL21udC9cdThGRDBcdTUyQThcdTU5RkZcdTYwMDFcdThCQzRcdTRGMzBcdTRFMEVcdTdFQTBcdTk1MTlcdTdDRkJcdTdFREYvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9zZXNzaW9ucy9uaWZ0eS1yZWxheGVkLWZleW5tYW4vbW50L1x1OEZEMFx1NTJBOFx1NTlGRlx1NjAwMVx1OEJDNFx1NEYzMFx1NEUwRVx1N0VBMFx1OTUxOVx1N0NGQlx1N0VERi9mcm9udGVuZC92aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vc2Vzc2lvbnMvbmlmdHktcmVsYXhlZC1mZXlubWFuL21udC8lRTglQkYlOTAlRTUlOEElQTglRTUlQTclQkYlRTYlODAlODElRTglQUYlODQlRTQlQkMlQjAlRTQlQjglOEUlRTclQkElQTAlRTklOTQlOTklRTclQjMlQkIlRTclQkIlOUYvZnJvbnRlbmQvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuaW1wb3J0IHZ1ZSBmcm9tIFwiQHZpdGVqcy9wbHVnaW4tdnVlXCI7XG5pbXBvcnQgcGF0aCBmcm9tIFwicGF0aFwiO1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xuICBwbHVnaW5zOiBbdnVlKCldLFxuICByZXNvbHZlOiB7XG4gICAgYWxpYXM6IHtcbiAgICAgIFwiQFwiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vc3JjXCIpLFxuICAgIH0sXG4gIH0sXG4gIHNlcnZlcjoge1xuICAgIHBvcnQ6IDUxNzMsXG4gICAgcHJveHk6IHtcbiAgICAgIFwiL2FwaVwiOiB7XG4gICAgICAgIHRhcmdldDogXCJodHRwOi8vbG9jYWxob3N0OjgwMDBcIixcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgICB3czogdHJ1ZVxuICAgICAgfVxuICAgIH1cbiAgfVxufSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWtiLFNBQVMsb0JBQW9CO0FBQy9jLE9BQU8sU0FBUztBQUNoQixPQUFPLFVBQVU7QUFGakIsSUFBTSxtQ0FBbUM7QUFJekMsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLElBQUksQ0FBQztBQUFBLEVBQ2YsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxLQUFLLFFBQVEsa0NBQVcsT0FBTztBQUFBLElBQ3RDO0FBQUEsRUFDRjtBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsUUFBUTtBQUFBLFFBQ04sUUFBUTtBQUFBLFFBQ1IsY0FBYztBQUFBLFFBQ2QsSUFBSTtBQUFBLE1BQ047QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
