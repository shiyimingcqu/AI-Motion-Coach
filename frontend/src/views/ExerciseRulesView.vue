<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Rule Management</p>
        <h1>动作规则管理</h1>
        <p class="subtle">维护动作检测规则、评分阈值、错误提示和标准动作模板。</p>
      </div>
      <button class="primary-button" type="button">
        <Plus :size="18" />
        新增规则
      </button>
    </header>

    <section class="admin-table panel">
      <div class="admin-table-head admin-rules-grid">
        <span>动作</span>
        <span>类型</span>
        <span>检测方式</span>
        <span>主要错误</span>
        <span>状态</span>
        <span>操作</span>
      </div>
      <div v-for="exercise in exercises" :key="exercise.key" class="admin-table-row admin-rules-grid">
        <div>
          <strong>{{ exercise.name }}</strong>
          <small>{{ exercise.level }} · 推荐 {{ exercise.duration }}</small>
        </div>
        <span>{{ exercise.category }}</span>
        <span>{{ exercise.modes.join(" / ") }}</span>
        <span>{{ exercise.errors.join("、") }}</span>
        <span class="status-pill good">启用中</span>
        <div class="admin-row-actions">
          <button class="secondary-button" type="button">编辑规则</button>
          <button
            class="text-button"
            type="button"
            :disabled="exercise.key !== 'squat'"
            :title="exercise.key !== 'squat' ? '当前仅支持深蹲模板生成' : ''"
            @click="openTemplateModal(exercise)"
          >
            添加模板
          </button>
        </div>
      </div>
    </section>

    <section class="admin-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Thresholds</p>
            <h2>评分阈值示例</h2>
          </div>
        </div>
        <div class="admin-note-list">
          <p>深蹲膝关节角度：最低 80°，低于阈值提示“下蹲深度不足”。</p>
          <p>俯卧撑躯干稳定：髋肩偏移超过阈值提示“身体塌腰”。</p>
          <p>开合跳节奏：连续帧节奏过快时提示“动作幅度不足”。</p>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Template</p>
            <h2>模板生成说明</h2>
          </div>
        </div>
        <p class="subtle">上传标准动作视频后，系统会提取有效帧、关键角度曲线和动作周期，用于后续模板相似性评分。</p>
      </article>
    </section>

    <div v-if="showTemplateModal" class="modal-overlay" @click.self="closeTemplateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加标准动作模板</h3>
          <button class="close-button" type="button" @click="closeTemplateModal">
            <X :size="20" />
          </button>
        </div>

        <div v-if="templateUploadSuccess" class="success-message">
          <CheckCircle :size="48" class="success-icon" />
          <h4>模板生成成功</h4>
          <p>有效帧数：{{ templateResult.valid_frames }} 帧</p>
          <p>模板路径：{{ templateResult.template_path }}</p>
          <p>曲线数量：{{ templateResult.curve_count }} 条</p>
          <button class="primary-button" type="button" @click="closeTemplateModal">确定</button>
        </div>

        <form v-else class="template-form" @submit.prevent="submitTemplate">
          <label class="form-field">
            <span>动作类型</span>
            <input v-model="templateForm.action" type="text" readonly />
          </label>

          <label class="form-field">
            <span>模板名称</span>
            <input v-model="templateForm.name" type="text" placeholder="例如：标准侧面深蹲" required />
          </label>

          <label class="form-field">
            <span>拍摄角度</span>
            <select v-model="templateForm.view" required>
              <option value="side">侧面</option>
              <option value="front">正面</option>
              <option value="diagonal">斜侧面</option>
            </select>
          </label>

          <label class="form-field">
            <span>版本号</span>
            <input v-model="templateForm.version" type="text" placeholder="v1" required />
          </label>

          <label class="file-upload" :class="{ 'has-file': templateForm.videoFile }">
            <input ref="fileInput" type="file" accept="video/*" required @change="handleFileChange" />
            <Upload :size="32" />
            <span>{{ templateForm.videoFile ? templateForm.videoFile.name : "点击上传标准动作视频" }}</span>
            <small>支持 MP4、MOV、AVI 等常见格式</small>
          </label>

          <div v-if="templateError" class="error-message">{{ templateError }}</div>

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
import { reactive, ref } from "vue";
import { apiUpload } from "@/api/client";
import { exercises as trainingExercises } from "@/stores/training";
import { CheckCircle, Loader2, Plus, Upload, X } from "lucide-vue-next";

const exercises = trainingExercises;

const showTemplateModal = ref(false);
const isUploading = ref(false);
const templateUploadSuccess = ref(false);
const templateError = ref("");
const templateResult = reactive({
  valid_frames: 0,
  template_path: "",
  curve_count: 0
});

const templateForm = reactive({
  action: "",
  name: "",
  view: "side",
  version: "v1",
  videoFile: null as File | null
});

function openTemplateModal(exercise: (typeof exercises)[0]) {
  if (exercise.key !== "squat") {
    return;
  }
  templateForm.action = exercise.key;
  templateForm.name = `标准${exercise.name}`;
  templateForm.view = "side";
  templateForm.version = "v1";
  templateForm.videoFile = null;
  templateError.value = "";
  templateUploadSuccess.value = false;
  showTemplateModal.value = true;
}

function closeTemplateModal() {
  showTemplateModal.value = false;
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  templateForm.videoFile = input.files?.[0] ?? null;
}

async function submitTemplate() {
  if (!templateForm.videoFile) {
    templateError.value = "请选择视频文件";
    return;
  }

  isUploading.value = true;
  templateError.value = "";

  try {
    const formData = new FormData();
    formData.append("video", templateForm.videoFile);
    formData.append("name", templateForm.name);
    formData.append("view", templateForm.view);
    formData.append("version", templateForm.version);

    const result = await apiUpload<any>(`/exercises/${templateForm.action}/templates/from-video`, formData);
    templateResult.valid_frames = result.valid_frames || 0;
    templateResult.template_path = result.template_path || "";
    templateResult.curve_count = result.curve_count || 0;
    templateUploadSuccess.value = true;
  } catch (error: any) {
    templateError.value = error.message || "模板生成失败";
  } finally {
    isUploading.value = false;
  }
}
</script>
