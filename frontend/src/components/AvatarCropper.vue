<template>
  <div class="avatar-crop-stage">
    <div class="avatar-crop-shell">
      <img ref="imageRef" :src="imageUrl" alt="待裁剪图片" draggable="false" @load="scheduleInit" />
      <div
        v-show="isReady"
        class="avatar-crop-box"
        :style="boxStyle"
        @pointerdown="startDrag($event, 'move')"
      >
        <span
          class="avatar-crop-handle"
          aria-hidden="true"
          @pointerdown.stop="startDrag($event, 'resize')"
        ></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from "vue";

const props = defineProps<{ imageUrl: string }>();

const imageRef = ref<HTMLImageElement | null>(null);
const isReady = ref(false);
const displayWidth = ref(0);
const displayHeight = ref(0);

const box = reactive({ x: 0, y: 0, size: 120 });

const MIN_BOX = 48;
const OUTPUT_SIZE = 512;

type DragMode = "move" | "resize";

const drag = reactive({
  mode: null as DragMode | null,
  startX: 0,
  startY: 0,
  startBox: { x: 0, y: 0, size: 0 }
});

const boxStyle = computed(() => ({
  left: `${box.x}px`,
  top: `${box.y}px`,
  width: `${box.size}px`,
  height: `${box.size}px`
}));

function scheduleInit() {
  isReady.value = false;
  requestAnimationFrame(() => {
    requestAnimationFrame(initBox);
  });
}

function clampBox() {
  if (!displayWidth.value || !displayHeight.value) {
    return;
  }

  box.size = Math.max(MIN_BOX, Math.min(box.size, displayWidth.value, displayHeight.value));
  box.x = Math.max(0, Math.min(box.x, displayWidth.value - box.size));
  box.y = Math.max(0, Math.min(box.y, displayHeight.value - box.size));
}

function initBox() {
  const image = imageRef.value;
  if (!image) {
    return;
  }

  if (!image.clientWidth || !image.clientHeight || !image.naturalWidth || !image.naturalHeight) {
    requestAnimationFrame(initBox);
    return;
  }

  displayWidth.value = image.clientWidth;
  displayHeight.value = image.clientHeight;

  const size = Math.min(displayWidth.value, displayHeight.value) * 0.72;
  box.size = Math.max(MIN_BOX, size);
  box.x = (displayWidth.value - box.size) / 2;
  box.y = (displayHeight.value - box.size) / 2;
  clampBox();
  isReady.value = true;
}

function startDrag(event: PointerEvent, mode: DragMode) {
  if (!isReady.value) {
    return;
  }

  drag.mode = mode;
  drag.startX = event.clientX;
  drag.startY = event.clientY;
  drag.startBox = { x: box.x, y: box.y, size: box.size };
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", stopDrag);
}

function onPointerMove(event: PointerEvent) {
  if (!drag.mode) {
    return;
  }

  const dx = event.clientX - drag.startX;
  const dy = event.clientY - drag.startY;

  if (drag.mode === "move") {
    box.x = drag.startBox.x + dx;
    box.y = drag.startBox.y + dy;
  } else {
    box.size = drag.startBox.size + Math.max(dx, dy);
  }

  clampBox();
}

function stopDrag() {
  drag.mode = null;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", stopDrag);
}

async function getCroppedImage(): Promise<string> {
  const image = imageRef.value;
  if (!image || !image.naturalWidth || !image.naturalHeight) {
    throw new Error("图片尚未加载完成，请稍后再试。");
  }

  if (!displayWidth.value || !displayHeight.value || !isReady.value) {
    throw new Error("裁剪区域尚未准备好，请稍后再试。");
  }

  const scale = image.naturalWidth / displayWidth.value;
  let sourceX = Math.round(box.x * scale);
  let sourceY = Math.round(box.y * scale);
  let sourceSize = Math.round(box.size * scale);

  sourceSize = Math.min(sourceSize, image.naturalWidth - sourceX, image.naturalHeight - sourceY);

  if (sourceSize <= 0) {
    throw new Error("裁剪区域无效，请调整方框后重试。");
  }

  const canvas = document.createElement("canvas");
  canvas.width = OUTPUT_SIZE;
  canvas.height = OUTPUT_SIZE;

  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("浏览器不支持图片裁剪。");
  }

  context.drawImage(image, sourceX, sourceY, sourceSize, sourceSize, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);

  const result = canvas.toDataURL("image/jpeg", 0.9);
  if (!result || result === "data:,") {
    throw new Error("图片导出失败，请换一张图片。");
  }

  return result;
}

function handleResize() {
  if (imageRef.value?.complete) {
    scheduleInit();
  }
}

window.addEventListener("resize", handleResize);

onUnmounted(() => {
  stopDrag();
  window.removeEventListener("resize", handleResize);
});

watch(
  () => props.imageUrl,
  () => {
    isReady.value = false;
  }
);

defineExpose({ getCroppedImage });
</script>
