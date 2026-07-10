<template>
  <Teleport to="body">
    <div class="wlm-overlay" @click.self="cancel">
      <div class="wlm-card">
        <button class="wlm-close" type="button" @click="cancel">
          <X :size="20" />
        </button>

        <h2 class="wlm-title">微信扫码登录</h2>
        <p class="wlm-subtitle">扫码后小程序将自动完成登录</p>

        <div class="wlm-qr-wrap">
          <div v-if="loading" class="wlm-loading">
            <div class="wlm-spinner"></div>
            <span>生成二维码中...</span>
          </div>
          <img v-else-if="qrImageUrl" :src="qrImageUrl" alt="微信小程序码" class="wlm-qr-img" />
          <div v-else class="wlm-error">
            <p>{{ errorMsg }}</p>
            <button type="button" class="wlm-retry" @click="loadQrCode">重试</button>
          </div>
        </div>

        <div v-if="statusText" class="wlm-status">
          <div v-if="status === 'pending'" class="wlm-spinner small"></div>
          <span :class="status === 'done' ? 'wlm-status-done' : 'wlm-status-text'">{{ statusText }}</span>
        </div>

        <p class="wlm-hint">扫码后等待自动登录...</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { X } from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const emit = defineEmits<{
  (e: "close"): void;
}>();

const router = useRouter();
const auth = useAuthStore();

const loading = ref(true);
const qrImageUrl = ref("");
const status = ref<"loading" | "pending" | "done">("loading");
const statusText = ref("");
const errorMsg = ref("");
let currentTicket = "";
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function loadQrCode() {
  loading.value = true;
  status.value = "loading";
  statusText.value = "";
  errorMsg.value = "";
  qrImageUrl.value = "";

  try {
    // 1. 创建 ticket
    const ticketResp = await fetch(`${API_BASE}/wechat/web-login/ticket`);
    if (!ticketResp.ok) throw new Error("获取 ticket 失败");
    const { ticket } = await ticketResp.json();
    currentTicket = ticket;

    // 2. 获取小程序码
    const qrResp = await fetch(`${API_BASE}/wechat/web-login/qrcode/${ticket}`);
    if (!qrResp.ok) {
      const err = await qrResp.json().catch(() => ({}));
      throw new Error(err.detail || "生成二维码失败");
    }
    const blob = await qrResp.blob();
    qrImageUrl.value = URL.createObjectURL(blob);

    status.value = "pending";
    statusText.value = "等待扫码...";

    // 3. 轮询
    startPolling(ticket);
  } catch (e: any) {
    errorMsg.value = e.message || "生成失败";
  } finally {
    loading.value = false;
  }
}

function startPolling(ticket: string) {
  pollTimer = setInterval(async () => {
    try {
      const resp = await fetch(`${API_BASE}/wechat/web-login/status/${ticket}`);
      const data = await resp.json();

      if (data.status === "done" && data.token) {
        clearInterval(pollTimer!);
        pollTimer = null;
        status.value = "done";
        statusText.value = "登录成功！";

        auth.setToken(data.token);
        await auth.fetchCurrentUser();

        setTimeout(() => {
          emit("close");
          router.push("/");
        }, 800);
      } else if (data.status === "expired") {
        clearInterval(pollTimer!);
        pollTimer = null;
        statusText.value = "二维码已过期，请重新生成";
      }
    } catch {
      // ignore
    }
  }, 1500);
}

function cancel() {
  if (pollTimer) clearInterval(pollTimer);
  emit("close");
}

onMounted(loadQrCode);

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<style scoped>
.wlm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.wlm-card {
  background: #fff; border-radius: 20px; padding: 32px; max-width: 360px;
  width: 90vw; text-align: center; position: relative;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18); animation: slideUp 0.25s ease;
}
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.wlm-close {
  position: absolute; top: 12px; right: 12px; width: 32px; height: 32px;
  border-radius: 8px; border: 0; background: #f1f5f9; color: #64748b;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.wlm-close:hover { background: #e2e8f0; color: #334155; }
.wlm-title { font-size: 20px; font-weight: 700; color: #101828; margin: 0 0 6px; }
.wlm-subtitle { font-size: 13px; color: #64748b; margin: 0 0 24px; }
.wlm-qr-wrap { display: flex; justify-content: center; align-items: center; margin-bottom: 16px; min-height: 200px; }
.wlm-qr-img { width: 200px; height: 200px; border-radius: 12px; border: 2px solid #e2e8f0; object-fit: contain; }
.wlm-loading { width: 200px; height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; border-radius: 12px; background: #f8fafc; border: 2px solid #e2e8f0; color: #94a3b8; font-size: 14px; }
.wlm-spinner { width: 36px; height: 36px; border: 3px solid #e2e8f0; border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; }
.wlm-spinner.small { width: 16px; height: 16px; border-width: 2px; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.wlm-error { width: 200px; height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; border-radius: 12px; background: #fef2f2; border: 2px solid #fecaca; color: #ef4444; font-size: 14px; }
.wlm-error p { margin: 0; }
.wlm-retry { padding: 6px 16px; border: 1px solid #fca5a5; border-radius: 8px; background: #fff; color: #ef4444; font-size: 13px; font-weight: 600; cursor: pointer; }
.wlm-status { display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 12px; min-height: 24px; }
.wlm-status-text { font-size: 14px; color: #64748b; }
.wlm-status-done { font-size: 15px; color: #16a34a; font-weight: 600; }
.wlm-hint { font-size: 12px; color: #94a3b8; margin: 0; }
</style>
