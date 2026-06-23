<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Exercise Library</p>
        <h1>动作训练库与规则配置</h1>
        <p class="subtle">按动作类型、难度和支持方式筛选训练，并查看检测规则。</p>
      </div>
      <button class="primary-button" type="button">
        <Plus :size="18" />
        新增规则
      </button>
    </header>

    <section class="split-layout">
      <aside class="filter-panel">
        <h2>筛选栏</h2>
        <div class="filter-group">
          <strong>动作类型</strong>
          <button v-for="exercise in exercises" :key="exercise.key" type="button">{{ exercise.name }}</button>
        </div>
        <div class="filter-group">
          <strong>难度</strong>
          <button type="button">初级</button>
          <button type="button">中级</button>
          <button type="button">高级</button>
        </div>
        <div class="filter-group">
          <strong>支持方式</strong>
          <button type="button">摄像头实时检测</button>
          <button type="button">视频上传分析</button>
        </div>
      </aside>

      <section class="exercise-grid">
        <article v-for="exercise in exercises" :key="exercise.key" class="exercise-card">
          <div class="exercise-visual" :style="{ '--accent': exercise.accent }">
            <Dumbbell :size="34" />
          </div>
          <div>
            <span>{{ exercise.category }} · {{ exercise.level }}</span>
            <h2>{{ exercise.name }}</h2>
          </div>
          <p>推荐时长 {{ exercise.duration }}，支持 {{ exercise.modes.join(" / ") }}。</p>
          <div class="error-chips compact">
            <span v-for="error in exercise.errors" :key="error">{{ error }}</span>
          </div>
          <div class="card-actions">
            <button class="primary-button" type="button" @click="start(exercise.key)">开始训练</button>
            <button class="secondary-button" type="button">查看规则</button>
            <button 
              class="template-button" 
              type="button" 
              @click="openTemplateModal(exercise)"
              :disabled="exercise.key !== 'squat'"
              :title="exercise.key !== 'squat' ? '当前仅支持深蹲模板生成' : ''"
            >
              <Upload :size="16" />
              {{ exercise.key === 'squat' ? '添加标准动作' : '暂未支持' }}
            </button>
          </div>
        </article>
      </section>
    </section>

    <!-- 添加标准动作弹窗 -->
    <div v-if="showTemplateModal" class="modal-overlay" @click.self="closeTemplateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加标准动作模板</h3>
          <button class="close-button" @click="closeTemplateModal">
            <X :size="20" />
          </button>
        </div>

        <div v-if="templateUploadSuccess" class="success-message">
          <CheckCircle :size="48" class="success-icon" />
          <h4>模板生成成功</h4>
          <p>有效帧数：{{ templateResult.valid_frames }} 帧</p>
          <p>模板路径：{{ templateResult.template_path }}</p>
          <div class="curves-info">
            <span v-for="(count, key) in templateResult.curves_count" :key="key">
              {{ getMetricName(key) }}: {{ count }} 点
            </span>
          </div>
          <button class="primary-button" @click="closeTemplateModal">确定</button>
        </div>

        <form v-else @submit.prevent="submitTemplate">
          <div class="form-group">
            <label>动作类型</label>
            <input type="text" :value="selectedExercise?.name" disabled />
          </div>

          <div class="form-group">
            <label>模板名称</label>
            <input 
              type="text" 
              v-model="templateForm.name" 
              placeholder="例如：标准侧面深蹲"
            />
          </div>

          <div class="form-group">
            <label>拍摄角度</label>
            <select v-model="templateForm.view">
              <option value="side">侧面 (Side)</option>
              <option value="front">正面 (Front)</option>
              <option value="diagonal">斜侧 (Diagonal)</option>
            </select>
          </div>

          <div class="form-group">
            <label>版本号</label>
            <input type="text" v-model="templateForm.version" placeholder="v1" />
          </div>

          <div class="form-group">
            <label>标准动作视频</label>
            <label class="file-upload" :class="{ 'has-file': templateForm.video }">
              <input 
                type="file" 
                accept="video/*" 
                @change="handleVideoSelect"
              />
              <div class="upload-hint">
                <Upload :size="24" />
                <span>{{ templateForm.video ? templateForm.video.name : '点击或拖拽上传视频' }}</span>
              </div>
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" class="secondary-button" @click="closeTemplateModal">取消</button>
            <button type="submit" class="primary-button" :disabled="!templateForm.video || uploading">
              <Loader2 v-if="uploading" :size="16" class="spin" />
              {{ uploading ? '上传中...' : '生成模板' }}
            </button>
          </div>
        </form>

        <div v-if="templateError" class="error-message">
          <AlertCircle :size="20" />
          {{ templateError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { Dumbbell, Plus, Upload, X, CheckCircle, AlertCircle, Loader2 } from "lucide-vue-next";

import { exercises, useTrainingStore } from "../stores/training";
import { apiUpload } from "../api/client";

const router = useRouter();
const store = useTrainingStore();

const showTemplateModal = ref(false);
const selectedExercise = ref<{ key: string; name: string } | null>(null);
const uploading = ref(false);
const templateError = ref("");
const templateUploadSuccess = ref(false);
const templateResult = reactive({
  valid_frames: 0,
  template_path: "",
  curves_count: {} as Record<string, number>
});

const templateForm = reactive({
  name: "",
  view: "side",
  version: "v1",
  video: null as File | null
});

type TemplateUploadResult = {
  valid_frames: number;
  template_path: string;
  curves_count: Record<string, number>;
};

function start(exercise: string) {
  store.setExercise(exercise);
  router.push("/realtime");
}

function openTemplateModal(exercise: { key: string; name: string }) {
  selectedExercise.value = exercise;
  templateForm.name = `标准${getViewName("side")}${exercise.name}`;
  templateForm.view = "side";
  templateForm.version = "v1";
  templateForm.video = null;
  templateError.value = "";
  templateUploadSuccess.value = false;
  showTemplateModal.value = true;
}

function closeTemplateModal() {
  showTemplateModal.value = false;
  selectedExercise.value = null;
  templateForm.video = null;
  templateError.value = "";
  templateUploadSuccess.value = false;
}

function handleVideoSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    templateForm.video = target.files[0];
  }
}

async function submitTemplate() {
  if (!templateForm.video || !selectedExercise.value) return;

  uploading.value = true;
  templateError.value = "";

  try {
    const formData = new FormData();
    formData.append("video", templateForm.video);
    if (templateForm.name) {
      formData.append("name", templateForm.name);
    }
    formData.append("view", templateForm.view);
    formData.append("version", templateForm.version);

    const result = await apiUpload<TemplateUploadResult>(
      `/exercises/${selectedExercise.value.key}/templates/from-video`,
      formData
    );

    templateResult.valid_frames = result.valid_frames;
    templateResult.template_path = result.template_path;
    templateResult.curves_count = result.curves_count;
    templateUploadSuccess.value = true;
  } catch (error) {
    templateError.value = error instanceof Error ? error.message : "上传失败";
  } finally {
    uploading.value = false;
  }
}

function getViewName(view: string): string {
  const names: Record<string, string> = {
    side: "侧面",
    front: "正面",
    diagonal: "斜侧"
  };
  return names[view] || view;
}

function getMetricName(key: string): string {
  const names: Record<string, string> = {
    knee_angle: "膝角",
    hip_angle: "髋角",
    trunk_angle: "躯干角",
    knee_symmetry_diff: "对称性"
  };
  return names[key] || key;
}
</script>

<style scoped>
.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.template-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
  transition: all 0.2s;
}

.template-button:hover:not(:disabled) {
  background: var(--green);
  color: white;
  border-color: var(--green);
}

.template-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--muted);
  padding: 4px;
  border-radius: 4px;
}

.close-button:hover {
  background: var(--surface);
  color: var(--ink);
}

.form-group {
  padding: 12px 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--surface);
}

.form-group input:disabled {
  background: #f5f5f5;
  color: var(--muted);
}

.file-upload {
  border: 2px dashed var(--border);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.file-upload:hover,
.file-upload.has-file {
  border-color: var(--green);
  background: rgba(34, 197, 94, 0.05);
}

.file-upload input {
  display: none;
}

.upload-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--muted);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 20px 16px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  color: var(--danger);
  font-size: 14px;
}

.success-message {
  padding: 24px;
  text-align: center;
}

.success-icon {
  color: var(--green);
  margin-bottom: 12px;
}

.success-message h4 {
  margin: 0 0 8px;
  color: var(--green);
}

.success-message p {
  margin: 4px 0;
  color: var(--muted);
  font-size: 14px;
}

.curves-info {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin: 12px 0;
  padding: 12px;
  background: var(--surface);
  border-radius: 8px;
}

.curves-info span {
  font-size: 12px;
  color: var(--muted);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
