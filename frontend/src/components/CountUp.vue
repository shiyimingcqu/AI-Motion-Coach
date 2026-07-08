<template>
  <span ref="countRef" :class="className">{{ displayValue }}</span>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    to: number;
    from?: number;
    direction?: "up" | "down";
    delay?: number;
    duration?: number;
    className?: string;
    startWhen?: boolean;
    separator?: string;
  }>(),
  {
    from: 0,
    direction: "up",
    delay: 0,
    duration: 2,
    className: "",
    startWhen: true,
    separator: "",
  },
);

const emit = defineEmits<{
  start: [];
  end: [];
}>();

const countRef = ref<HTMLElement | null>(null);
const currentValue = ref(props.direction === "down" ? props.to : props.from);
const isInView = ref(false);
const hasStarted = ref(false);
let frameId = 0;
let delayTimer: number | undefined;
let observer: IntersectionObserver | undefined;

const fromValue = computed(() => (props.direction === "down" ? props.to : props.from));
const toValue = computed(() => (props.direction === "down" ? props.from : props.to));

function decimalPlaces(value: number) {
  const [, decimals = ""] = value.toString().split(".");
  return decimals.replace(/0+$/, "").length;
}

const maxDecimals = computed(() =>
  Math.max(decimalPlaces(props.from), decimalPlaces(props.to)),
);

const displayValue = computed(() => formatValue(currentValue.value));

function formatValue(value: number) {
  const formatted = new Intl.NumberFormat("en-US", {
    useGrouping: Boolean(props.separator),
    minimumFractionDigits: maxDecimals.value,
    maximumFractionDigits: maxDecimals.value,
  }).format(value);

  return props.separator ? formatted.replace(/,/g, props.separator) : formatted;
}

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3);
}

function stopAnimation() {
  if (frameId) cancelAnimationFrame(frameId);
  if (delayTimer) window.clearTimeout(delayTimer);
  frameId = 0;
  delayTimer = undefined;
}

function startAnimation() {
  if (hasStarted.value || !props.startWhen || !isInView.value) return;

  hasStarted.value = true;
  emit("start");
  currentValue.value = fromValue.value;

  delayTimer = window.setTimeout(() => {
    const startedAt = performance.now();
    const durationMs = Math.max(props.duration, 0.01) * 1000;

    const tick = (time: number) => {
      const progress = Math.min((time - startedAt) / durationMs, 1);
      const eased = easeOutCubic(progress);
      currentValue.value = fromValue.value + (toValue.value - fromValue.value) * eased;

      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      } else {
        currentValue.value = toValue.value;
        emit("end");
      }
    };

    frameId = requestAnimationFrame(tick);
  }, props.delay * 1000);
}

watch(
  () => [props.to, props.from, props.direction, props.startWhen],
  () => {
    stopAnimation();
    hasStarted.value = false;
    currentValue.value = fromValue.value;
    startAnimation();
  },
);

onMounted(() => {
  if (!countRef.value) return;

  observer = new IntersectionObserver(
    ([entry]) => {
      isInView.value = entry.isIntersecting;
      startAnimation();
    },
    { threshold: 0.2 },
  );

  observer.observe(countRef.value);
});

onBeforeUnmount(() => {
  stopAnimation();
  observer?.disconnect();
});
</script>
