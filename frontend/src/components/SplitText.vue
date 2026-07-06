<template>
  <component :is="tag" :class="['split-parent', className]" :style="wrapperStyle" ref="elRef">
    <span
      v-for="(item, i) in parts"
      :key="i"
      class="split-item"
      :class="{'is-visible': visible}"
      :style="itemStyle(i)"
    >{{ item }}</span>
  </component>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

const props = withDefaults(defineProps<{
  text?: string
  className?: string
  tag?: string
  delay?: number
  duration?: number
  ease?: string
  from?: Record<string, any>
  to?: Record<string, any>
  splitType?: string
  textAlign?: string
  onLetterAnimationComplete?: () => void
}>(), {
  text: '',
  className: '',
  tag: 'p',
  delay: 50,
  duration: 0.6,
  ease: 'cubic-bezier(0.22, 1, 0.36, 1)',
  from: () => ({ opacity: 0, y: 40 }),
  to: () => ({ opacity: 1, y: 0 }),
  splitType: 'chars',
  textAlign: 'center',
});

const emit = defineEmits<{ (e: 'complete'): void }>();

const visible = ref(false);
const completed = ref(false);

const parts = computed(() => {
  if (!props.text) return [];
  if (props.splitType === 'words') {
    return props.text.split(/(\s+)/).filter(Boolean);
  }
  return props.text.split('');
});

const wrapperStyle = computed(() => ({
  textAlign: props.textAlign,
  overflow: 'hidden',
  display: 'block',
}));

function itemStyle(i: number): Record<string, string> {
  const f = props.from || {};
  const delayMs = i * props.delay;
  const t = props.duration;
  const style: Record<string, string> = {
    display: 'inline-block',
    whiteSpace: 'pre',
    transition: `all ${t}s ${props.ease} ${delayMs}ms`,
    willChange: 'transform, opacity',
  };
  if (f.opacity !== undefined) style.opacity = String(f.opacity);
  if (f.y !== undefined) style.transform = `translateY(${f.y}px)`;
  if (f.x !== undefined) style.transform = `translateX(${f.x}px)`;
  if (f.scale !== undefined) style.transform = `scale(${f.scale})`;
  if (f.rotate !== undefined) style.transform = `rotate(${f.rotate}deg)`;
  return style;
}

onMounted(() => {
  // Trigger animation on next frame
  requestAnimationFrame(() => {
    visible.value = true;
    // Fire complete callback after all items animate
    const totalMs = props.text.length * props.delay + props.duration * 1000 + 100;
    setTimeout(() => {
      if (!completed.value) {
        completed.value = true;
        emit('complete');
        props.onLetterAnimationComplete?.();
      }
    }, totalMs);
  });
});
</script>

<style scoped>
.split-item {
  display: inline-block;
  white-space: pre;
}

/* When visible, apply 'to' state */
.split-item.is-visible {
  opacity: 1 !important;
  transform: translateY(0) !important;
}
</style>
