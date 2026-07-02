<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Standard Videos</p>
        <h1>标准视频管理</h1>
        <p class="subtle">为用户提供可参考的标准动作视频，支持上传、启停和删除。</p>
      </div>
      <button class="primary-button" type="button" @click="showUploadModal = true">+ 上传标准视频</button>
    </header>

    <!-- 上传弹窗 -->
    <div v-if="showUploadModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-card">
        <h3 class="modal-title">上传标准视频</h3>
        <div class="modal-form">
          <label>
            <span>标题 <em>*</em></span>
            <input v-model="form.title" type="text" placeholder="如：深蹲标准正面示范" />
          </label>
          <label>
            <span>动作</span>
            <select v-model="form.exercise">
              <option value="squat">深蹲</option>
              <option value="push_up">俯卧撑</option>
              <option value="plank">平板支撑</option>
              <option value="lunge">弓步蹲</option>
              <option value="jumping_jack">开合跳</option>
              <option value="burpee">波比跳</option>
              <option value="high_knees">高抬腿</option>
            </select>
          </label>
          <label>
            <span>视角</span>
            <select v-model="form.camera_view">
              <option value="front">正面</option>
              <option value="side">侧面</option>
            </select>
          </label>
          <label>
            <span>描述（可选）</span>
            <textarea v-model="form.description" rows="3" placeholder="简要说明这个标准视频的要点..."></textarea>
          </label>
          <label class="file-label">
            <span>视频文件 <em>*</em></span>
            <div class="file-drop" @click="fileInput?.click()">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <span>{{ selectedFile ? selectedFile.name : '点击选择视频文件' }}</span>
            </div>
            <input ref="fileInput" type="file" accept="video/*" style="display:none" @change="onFileChange" />
          </label>
        </div>
        <div class="modal-actions">
          <button class="secondary-button" @click="closeModal" :disabled="uploading">取消</button>
          <button class="primary-button" @click="submitUpload" :disabled="uploading || !form.title || !selectedFile">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
        <p v-if="!uploading && (!form.title || !selectedFile)" class="form-hint">
          请先{{ !form.title ? '填写标题' : '' }}{{ !form.title && !selectedFile ? '并' : '' }}{{ !selectedFile ? '选择视频文件' : '' }}后再上传
        </p>
        <p v-if="uploadError" class="form-error">{{ uploadError }}</p>
      </div>
    </div>

    <!-- 视频列表 -->
    <section class="admin-table panel">
      <div v-if="loading" class="admin-empty">加载中...</div>
      <template v-else-if="videos.length">
        <div class="admin-table-head admin-refvideo-grid">
          <span>标题</span>
          <span>动作</span>
          <span>视角</span>
          <span>上传时间</span>
          <span>状态</span>
          <span>操作</span>
        </div>
        <div v-for="v in videos" :key="v.id" class="admin-table-row admin-refvideo-grid">
          <div>
            <strong>{{ v.title }}</strong>
            <small v-if="v.description" class="row-desc">{{ v.description }}</small>
          </div>
          <span>{{ exerciseName(v.exercise) }}</span>
          <span>{{ v.camera_view === 'front' ? '正面' : '侧面' }}</span>
          <span>{{ formatDate(v.created_at) }}</span>
          <span class="status-pill" :class="v.is_active ? 'good' : 'idle'">
            {{ v.is_active ? '启用' : '停用' }}
          </span>
          <div class="admin-row-actions">
            <button class="text-button" @click="toggleStatus(v)">{{ v.is_active ? '停用' : '启用' }}</button>
            <button class="text-button danger" @click="deleteVideo(v)">删除</button>
          </div>
        </div>
      </template>
      <div v-else class="admin-empty">暂无标准视频，点击右上角上传</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { apiGet, apiDelete, apiPatch, apiUpload } from "@/api/client";

interface RefVideo {
  id: number;
  title: string;
  exercise: string;
  camera_view: string;
  description?: string;
  file_uri: string;
  is_active: boolean;
  created_at: string;
}

const videos = ref<RefVideo[]>([]);
const loading = ref(true);
const showUploadModal = ref(false);
const uploading = ref(false);
const uploadError = ref("");
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);

const route = useRoute();

const form = ref({
  title: "",
  exercise: "squat",
  camera_view: "front",
  description: "",
});

async function loadVideos() {
  loading.value = true;
  try {
    const data = await apiGet<{ items: RefVideo[] }>("/reference-videos/all");
    videos.value = data.items || [];
  } catch {
    videos.value = [];
  } finally {
    loading.value = false;
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

function closeModal() {
  showUploadModal.value = false;
  uploading.value = false;
  uploadError.value = "";
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
  form.value = { title: "", exercise: "squat", camera_view: "front", description: "" };
}

async function submitUpload() {
  if (!form.value.title || !selectedFile.value) return;
  uploading.value = true;
  uploadError.value = "";
  try {
    const fd = new FormData();
    fd.append("title", form.value.title);
    fd.append("exercise", form.value.exercise);
    fd.append("camera_view", form.value.camera_view);
    fd.append("description", form.value.description);
    fd.append("file", selectedFile.value);
    await apiUpload("/reference-videos", fd);
    closeModal();
    await loadVideos();
  } catch (err: any) {
    uploadError.value = err?.message || "上传失败，请重试";
  } finally {
    uploading.value = false;
  }
}

async function toggleStatus(v: RefVideo) {
  try {
    await apiPatch(`/reference-videos/${v.id}`, {});
    await loadVideos();
  } catch (err: any) {
    alert(err?.message || "操作失败，请检查后端是否正常");
  }
}

async function deleteVideo(v: RefVideo) {
  if (!confirm(`确定要删除《${v.title}》吗？此操作不可撤销。`)) return;
  try {
    await apiDelete(`/reference-videos/${v.id}`);
    await loadVideos();
  } catch {}
}

function exerciseName(key: string): string {
  const map: Record<string, string> = {
    squat: "深蹲", push_up: "俯卧撑", plank: "平板支撑", lunge: "弓步蹲",
    jumping_jack: "开合跳", burpee: "波比跳", high_knees: "高抬腿",
    mountain_climber: "登山跑", pull_up: "引体向上", dumbbell_curl: "哑铃弯举",
  };
  return map[key] || key;
}

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

onMounted(() => {
  loadVideos();
  // 如果从动作管理页跳转过来，自动打开上传弹窗并预选动作
  const ex = route.query.exercise;
  if (ex && typeof ex === "string") {
    form.value.exercise = ex;
    showUploadModal.value = true;
  }
});
</script>

<style scoped>
.admin-refvideo-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.2fr 80px 130px;
  align-items: center;
  gap: 0 12px;
}
.row-desc {
  display: block;
  font-size: 12px;
  color: var(--text-muted, #888);
  margin-top: 2px;
}
.admin-empty {
  padding: 40px;
  text-align: center;
  color: var(--text-muted, #aaa);
}
/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 999;
}
.modal-card {
  background: #fff; border-radius: 16px; padding: 28px 32px; width: 480px; max-width: 95vw;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
}
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; }
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.modal-form label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #444; }
.modal-form label em { color: #ef4444; font-style: normal; }
.modal-form input, .modal-form select, .modal-form textarea {
  border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 12px;
  font-size: 14px; color: #111; background: #fff; outline: none;
  transition: border 0.2s;
}
.modal-form input:focus, .modal-form select:focus, .modal-form textarea:focus {
  border-color: #3b82f6;
}
.file-drop {
  display: flex; align-items: center; gap: 10px;
  border: 1.5px dashed #c8d0da; border-radius: 8px; padding: 14px 16px;
  cursor: pointer; background: #f9fafb; transition: border-color 0.2s;
}
.file-drop:hover { border-color: #3b82f6; }
.file-drop span { font-size: 13px; color: #555; }
.modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px; }
.form-error { color: #ef4444; font-size: 13px; margin-top: 8px; }
.form-hint { color: #f59e0b; font-size: 13px; margin-top: 8px; text-align: right; }
.danger { color: #ef4444 !important; }
</style>
