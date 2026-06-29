<template>
  <component :is="asTag" :class="['text-type', className]">
    <span class="text-type__content" :style="{ color: currentColor }">{{ displayText }}<wbr /></span>
    <span
      v-if="showCursor"
      ref="cursorRef"
      :class="['text-type__cursor', cursorClassName, { hidden: hideCursor }]"
    >{{ cursorCharacter }}</span>
  </component>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';

const props = withDefaults(defineProps<{
  text?: string | string[]
  as?: string
  typingSpeed?: number
  initialDelay?: number
  pauseDuration?: number
  deletingSpeed?: number
  loop?: boolean
  className?: string
  showCursor?: boolean
  hideCursorWhileTyping?: boolean
  cursorCharacter?: string
  cursorBlinkDuration?: number
  cursorClassName?: string
  textColors?: string[]
  variableSpeed?: { min: number; max: number }
  onSentenceComplete?: (sentence: string, index: number) => void
  startOnVisible?: boolean
  reverseMode?: boolean
}>(), {
  text: '',
  as: 'div',
  typingSpeed: 75,
  initialDelay: 500,
  pauseDuration: 2000,
  deletingSpeed: 30,
  loop: true,
  className: '',
  showCursor: true,
  hideCursorWhileTyping: false,
  cursorCharacter: '|',
  cursorBlinkDuration: 0.5,
  cursorClassName: '',
  textColors: () => [],
  variableSpeed: undefined,
  startOnVisible: false,
  reverseMode: false,
});

const asTag = computed(() => props.as);

const textArray = computed(() =>
  Array.isArray(props.text) ? props.text : [props.text]
);

const displayText = ref('');
const isDeleting = ref(false);
const currentTextIndex = ref(0);
const currentCharIndex = ref(0);
const isVisible = ref(false);
const cursorRef = ref<HTMLElement | null>(null);
const hideCursor = ref(false);

const currentColor = computed(() => {
  if (!props.textColors || props.textColors.length === 0) return 'inherit';
  return props.textColors[currentTextIndex.value % props.textColors.length];
});

let timer: ReturnType<typeof setTimeout> | null = null;
let blinkTimer: ReturnType<typeof setInterval> | null = null;

function getSpeed(): number {
  if (props.variableSpeed) {
    return Math.random() * (props.variableSpeed.max - props.variableSpeed.min) + props.variableSpeed.min;
  }
  return props.typingSpeed;
}

onMounted(() => {
  // Cursor blink
  if (props.showCursor) {
    blinkTimer = setInterval(() => {
      if (cursorRef.value) {
        cursorRef.value.style.opacity = cursorRef.value.style.opacity === '0' ? '1' : '0';
      }
    }, props.cursorBlinkDuration * 1000);
  }

  if (!props.startOnVisible) {
    isVisible.value = true;
    startTyping();
  }
});

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
  if (blinkTimer) clearInterval(blinkTimer);
});

function startTyping() {
  if (!isVisible.value) return;
  let firstRun = true;

  function step() {
    const currentFullText = textArray.value[currentTextIndex.value];
    const processed = props.reverseMode
      ? currentFullText.split('').reverse().join('')
      : currentFullText;

    if (isDeleting.value) {
      if (displayText.value === '') {
        isDeleting.value = false;
        if (currentTextIndex.value === textArray.value.length - 1 && !props.loop) return;

        props.onSentenceComplete?.(textArray.value[currentTextIndex.value], currentTextIndex.value);
        currentTextIndex.value = (currentTextIndex.value + 1) % textArray.value.length;
        currentCharIndex.value = 0;

        timer = setTimeout(step, props.pauseDuration);
        return;
      }

      hideCursor.value = props.hideCursorWhileTyping;
      timer = setTimeout(() => {
        displayText.value = displayText.value.slice(0, -1);
        hideCursor.value = false;
        timer = setTimeout(step, 16);
      }, props.deletingSpeed);
      return;
    }

    // Typing
    if (currentCharIndex.value < processed.length) {
      hideCursor.value = props.hideCursorWhileTyping;
      timer = setTimeout(() => {
        displayText.value += processed[currentCharIndex.value];
        currentCharIndex.value++;
        hideCursor.value = false;
        timer = setTimeout(step, getSpeed());
      }, firstRun ? props.initialDelay : 0);
      firstRun = false;
    } else {
      if (textArray.value.length >= 1) {
        if (!props.loop && currentTextIndex.value === textArray.value.length - 1) return;
        timer = setTimeout(() => {
          isDeleting.value = true;
          timer = setTimeout(step, 16);
        }, props.pauseDuration);
      }
    }
  }

  step();
}
</script>

<style scoped>
.text-type {
  display: inline-block;
  white-space: pre-wrap;
}
.text-type__cursor {
  margin-left: 0.125rem;
  display: inline-block;
  opacity: 1;
  font-weight: 300;
}
.text-type__cursor.hidden {
  display: none;
}
</style>
