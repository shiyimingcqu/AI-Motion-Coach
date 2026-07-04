<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Template Management</p>
        <h1>模板管理</h1>
        <p class="subtle">管理标准动作模板、版本和来源。每种动作只能启用一个模板用于评分。</p>
      </div>
      <button class="primary-button" type="button" @click="openUploadModal()">
        <Upload :size="18" />
        上传模板
      </button>
    </header>

    <StateDisplay v-if="loading" type="loading" skeleton="table" text="加载模板..." />

    <section v-else class="admin-table panel">
      <div class="admin-table-head admin-templates-grid">
        <span>模板</span>
        <span>动作</span>
        <span>视角</span>
        <span>版本</span>
        <span>来源</span>
        <span>启用状态</span>
        <span>操作</span>
      </div>
      <div v-if="templates.length === 0" class="empty-row">暂无模板</div>
      <div
        v-for="template in templates"
        :key="template.template_id"
        class="admin-table-row admin-templates-grid"
        :class="{ 'enabled-row': template.is_enabled }"
      >
        <div>
          <strong>{{ template.name }}</strong>
          <small>{{ template.valid_frames }} 有效帧 · {{ template.template_id }}</small>
        </div>
        <span>{{ exerciseName(template.action) }}</span>
        <span>{{ viewName(template.view) }}</span>
        <span>{{ template.version || "-" }}</span>
        <span class="status-pill" :class="template.source === 'storage' ? 'good' : 'idle'">
          {{ template.source === "storage" ? "上传" : "内置" }}
        </span>
        <span>
          <button
            class="toggle-button"
            :class="{ active: template.is_enabled }"
            type="button"
            :disabled="toggleLoading === template.template_id"
            @click="toggleTemplate(template)"
          >
            <span v-if="toggleLoading === template.template_id" class="mini-spin">⟳</span>
            <span v-else>{{ template.is_enabled ? "已启用" : "未启用" }}</span>
          </button>
        </span>
        <div class="admin-row-actions">
          <button class="secondary-button" type="button" @click="openUploadModal(template.action)">
            替换
          </button>
        </div>
      </div>
    </section>

    <div v-if="showUploadModal" class="modal-overlay" @click.self="closeUploadModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>上传标准动作模板</h3>
          <button class="close-button" type="button" @click="closeUploadModal">
            <X :size="20" />
          </button>
        </div>
        <form class="template-form" @submit.prevent="submitTemplate">
          <label class="form-field">
            <span>动作</span>
            <select v-model="templateForm.exerciseKey" required>
              <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
                {{ exercise.name }}
              </option>
            </select>
          </label>
          <label class="form-field">
            <span>模板名称</span>
            <input v-model="templateForm.name" type="text" placeholder="例如：标准侧面平板支撑" required />
          </label>
          <label class="form-field">
            <span>拍摄角度</span>
            <select v-model="templateForm.view">
              <option value="side">侧面</option>
              <option value="front">正面</option>
              <option value="diagonal">斜侧面</option>
            </select>
          </label>
          <label class="file-upload" :class="{ 'has-file': templateForm.videoFile }">
            <input ref="fileInput" type="file" accept="video/*" required @change="handleFileChange" />
            <Upload :size="32" />
            <span>{{ templateForm.videoFile ? templateForm.videoFile.name : "选择标准动作视频" }}</span>
            <small>MP4、MOV、AVI</small>
          </label>
          <div v-if="uploadMessage" class="success-message compact">{{ uploadMessage }}</div>
          <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
          <button class="primary-button" type="submit" :disabled="isUploading || !templateForm.videoFile">
            <Loader2 v-if="isUploading" :size="18" class="spin" />
            <span v-else>生成模板</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { apiGet, apiPost, apiUpload, apiDelete } from "@/api/client";
import { getExerciseLibrary, type ExerciseItem } from "@/api/exercises";
import StateDisplay from "@/components/StateDisplay.vue";
import { Loader2, Upload, X } from "lucide-vue-next";

type TemplateItem = {
  template_id: string;
  action: string;
  name: string;
  view: string;
  version?: string;
  valid_frames: number;
  source: "storage" | "builtin" | string;
  is_enabled?: boolean;
};

const loading = ref(true);
const exercises = ref<ExerciseItem[]>([]);
const templates = ref<TemplateItem[]>([]);
const showUploadModal = ref(false);
const isUploading = ref(false);
const uploadError = ref("");
const uploadMessage = ref("");
const fileInput = ref<HTMLInputElement | null>(null);
const toggleLoading = ref<string | null>(null);

const exerciseMap = computed(() =>
  new Map(exercises.value.map((exercise) => [exercise.key, exercise.name]))
);

const templateForm = reactive({
  exerciseKey: "",
  name: "",
  view: "side",
  videoFile: null as File | null,
});

function exerciseName(key: string) {
  return exerciseMap.value.get(key) || key;
}

function viewName(view: string) {
  const names: Record<string, string> = {
    side: "侧面",
    front: "正面",
    diagonal: "斜侧面",
    default: "默认",
  };
  return names[view] || view;
}

function openUploadModal(exerciseKey?: string) {
  const key = exerciseKey || exercises.value[0]?.key || "";
  templateForm.exerciseKey = key;
  templateForm.name = key ? `标准${exerciseName(key)}` : "";
  templateForm.view = "side";
  templateForm.videoFile = null;
  uploadError.value = "";
  uploadMessage.value = "";
  if (fileInput.value) {
    fileInput.value.value = "";
  }
  showUploadModal.value = true;
}

function closeUploadModal() {
  showUploadModal.value = false;
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  templateForm.videoFile = input.files?.[0] ?? null;
}

async function submitTemplate() {
  if (!templateForm.exerciseKey || !templateForm.videoFile) return;

  isUploading.value = true;
  uploadError.value = "";
  uploadMessage.value = "";

  try {
    const form = new FormData();
    form.append("video", templateForm.videoFile);
    form.append("name", templateForm.name);
    form.append("view", templateForm.view);
    form.append("version", "v1");

    const result = await apiUpload<{ valid_frames?: number }>(
      `/exercises/${templateForm.exerciseKey}/templates/from-video`,
      form
    );
    uploadMessage.value = `模板生成成功，有效帧 ${result.valid_frames ?? 0} 帧`;
    await loadTemplates();
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "模板生成失败";
  } finally {
    isUploading.value = false;
  }
}

async function toggleTemplate(template: TemplateItem) {
  toggleLoading.value = template.template_id;
  try {
    if (template.is_enabled) {
      // 禁用：取消启用
      await apiDelete(`/admin/templates/active/${encodeURIComponent(template.action)}`);
    } else {
      // 启用：设置该模板为当前动作的启用模板
      await apiPost("/admin/templates/active", {
        action: template.action,
        template_id: template.template_id,
      });
    }
    await loadTemplates();
  } catch (err) {
    console.error("切换模板状态失败", err);
  } finally {
    toggleLoading.value = null;
  }
}

async function loadTemplates() {
  const results = await Promise.all(
    exercises.value.map(async (exercise) => {
      try {
        const response = await apiGet<{ items: TemplateItem[] }>(`/exercises/${exercise.key}/templates`);
        return response.items;
      } catch {
        return [];
      }
    })
  );
  templates.value = results.flat().sort((a, b) => {
    if (a.source !== b.source) return a.source === "storage" ? -1 : 1;
    return a.name.localeCompare(b.name, "zh-Hans-CN");
  });
}

async function loadPage() {
  loading.value = true;
  try {
    const data = await getExerciseLibrary();
    exercises.value = data.items;
    await loadTemplates();
  } catch {
    exercises.value = [];
    templates.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(loadPage);
</script>

<style scoped>
.page { display: grid; gap: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
.page-header h1 { color: #f8fafc; font-size: 28px; margin: 0; }
.page-header p { margin: 4px 0 0; color: #64748b; }

.admin-templates-grid {
  display: grid;
  grid-template-columns: 1.8fr 1fr 1fr 0.8fr 0.8fr 1fr 0.8fr;
  gap: 12px;
  align-items: center;
}

.enabled-row {
  background: rgba(16, 185, 129, 0.04);
}

.enabled-row strong {
  color: #34d399;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 18px;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.primary-button { border: none; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; }
.secondary-button { border: 1px solid rgba(59,130,246,0.1); background: rgba(8,13,26,0.5); color: #cbd5e1; }
.primary-button:disabled { opacity: 0.65; cursor: not-allowed; }

.empty-row { padding: 24px; color: #94a3b8; text-align: center; }

.toggle-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(59,130,246,0.15);
  background: rgba(8,13,26,0.5);
  color: #94a3b8;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.toggle-button:hover {
  border-color: rgba(59,130,246,0.3);
  color: #cbd5e1;
}
.toggle-button.active {
  background: rgba(16,185,129,0.12);
  border-color: rgba(16,185,129,0.25);
  color: #34d399;
}
.toggle-button.active:hover {
  background: rgba(239,68,68,0.1);
  border-color: rgba(239,68,68,0.2);
  color: #f87171;
}
.toggle-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mini-spin {
  display: inline-block;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.65); display: grid; place-items: center; padding: 24px; }
.modal-content { width: 100%; max-width: 520px; max-height: 90vh; overflow-y: auto; background: #0f172a; border: 1px solid rgba(59,130,246,0.15); border-radius: 16px; padding: 28px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h3 { color: #f8fafc; font-size: 18px; margin: 0; }
.close-button { background: none; border: none; color: #64748b; cursor: pointer; }
.template-form { display: grid; gap: 16px; }
.form-field { display: grid; gap: 6px; }
.form-field span { color: #94a3b8; font-size: 13px; font-weight: 600; }
.form-field input,
.form-field select {
  padding: 10px 14px;
  border: 1px solid rgba(59,130,246,0.1);
  border-radius: 8px;
  background: rgba(8,13,26,0.7);
  color: #f8fafc;
  font-size: 14px;
}
.file-upload { display: grid; gap: 6px; place-items: center; padding: 28px; border: 2px dashed rgba(59,130,246,0.15); border-radius: 10px; cursor: pointer; color: #64748b; }
.file-upload.has-file { border-color: rgba(16,185,129,0.3); }
.file-upload input { display: none; }
.file-upload span { font-size: 14px; }
.file-upload small { font-size: 11px; }
.error-message { color: #f87171; background: rgba(239,68,68,0.08); padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.success-message.compact { color: #34d399; background: rgba(16,185,129,0.08); padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) {
  .page-header { display: grid; }
}
</style>
