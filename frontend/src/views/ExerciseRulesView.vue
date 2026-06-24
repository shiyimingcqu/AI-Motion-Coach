<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Exercise Library</p>
        <h1>动作训练库与规则配置</h1>
        <p class="subtle">按动作类型、难度和支持方式筛选训练，并查看检测规则。</p>
      </div>
      <button v-if="authStore.isAdmin" class="primary-button" type="button">
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
              v-if="authStore.isAdmin"
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
            <input
              ref="fileInput"
              type="file"
              accept="video/*"
              @change="handleFileChange"
              required
            />
            <Upload :size="32" />
            <span>{{ templateForm.videoFile ? templateForm.videoFile.name : '点击上传标准动作视频' }}</span>
            <small>支持 MP4、MOV、AVI 等常见格式</small>
          </label>

          <div v-if="templateError" class="error-message">{{ templateError }}</div>

          <button 
            class="primary-button" 
            type="submit" 
            :disabled="isUploading || !templateForm.videoFile"
          >
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
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { apiUpload } from "@/api/client";
import { useTrainingStore, exercises as trainingExercises } from "@/stores/training";
import { Dumbbell, Plus, Upload, X, CheckCircle, Loader2 } from "lucide-vue-next";

const router = useRouter();
const trainingStore = useTrainingStore();
const authStore = useAuthStore();

const exercises = trainingExercises;

function start(exerciseKey: string) {
  trainingStore.setExercise(exerciseKey);
  router.push("/realtime");
}

// 模板弹窗相关
const showTemplateModal = ref(false);
const isUploading = ref(false);
const templateUploadSuccess = ref(false);
const templateError = ref("");
const templateResult = reactive({
  valid_frames: 0,
  template_path: "",
  curve_count: 0,
});

const templateForm = reactive({
  action: "",
  name: "",
  view: "side",
  version: "v1",
  videoFile: null as File | null,
});

function openTemplateModal(exercise: typeof exercises[0]) {
  if (!authStore.isAdmin) {
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
  if (input.files && input.files.length > 0) {
    templateForm.videoFile = input.files[0];
  }
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
