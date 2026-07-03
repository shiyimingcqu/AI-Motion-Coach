import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import { router } from "./router";
import i18n from "./i18n";
import { useSettingsStore } from "./stores/settings";
import "./styles.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia).use(router).use(i18n);
useSettingsStore();
app.mount("#app");
