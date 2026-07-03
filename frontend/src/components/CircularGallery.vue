<template>
  <div
    ref="containerRef"
    class="circular-gallery"
    :class="{ clickable: props.items && props.items.length > 0 }"
    tabindex="0"
    role="region"
    aria-label="Circular image gallery. Use left and right arrow keys to navigate."
  />
</template>

<script setup lang="ts">
import { Camera, Mesh, Plane, Program, Renderer, Texture, Transform } from "ogl";
import { onBeforeUnmount, onMounted, ref } from "vue";

const emit = defineEmits<{
  onItemClick: [index: number];
}>();

interface GalleryItem {
  image: string;
  text: string;
}

const props = withDefaults(defineProps<{
  items?: GalleryItem[];
  bend?: number;
  textColor?: string;
  borderRadius?: number;
  font?: string;
  fontUrl?: string;
  scrollSpeed?: number;
  scrollEase?: number;
}>(), {
  bend: 3,
  textColor: "#ffffff",
  borderRadius: 0.05,
  font: "bold 30px Figtree",
  scrollSpeed: 2,
  scrollEase: 0.05,
});

const containerRef = ref<HTMLDivElement | null>(null);

// ─── helpers ────────────────────────────────────
function debounce<T extends (...args: unknown[]) => void>(fn: T, wait: number) {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

function lerp(p1: number, p2: number, t: number) { return p1 + (p2 - p1) * t; }

function autoBind(instance: any) {
  const proto = Object.getPrototypeOf(instance);
  Object.getOwnPropertyNames(proto).forEach(key => {
    if (key !== "constructor" && typeof instance[key] === "function") {
      instance[key] = (instance[key] as Function).bind(instance);
    }
  });
}

const DEFAULT_FONT = "bold 30px Figtree";
const DEFAULT_FONT_URL = "https://fonts.googleapis.com/css2?family=Figtree:wght@400;700&display=swap";

function deriveFontFamilyFromUrl(url: string) {
  const fileName = (url.split("/").pop() || "custom-font").split("?")[0];
  const base = fileName.replace(/\.(woff2?|ttf|otf|eot)$/i, "");
  return base.replace(/[^a-zA-Z0-9-_ ]/g, "").trim() || "CircularGalleryFont";
}

async function loadFontFromStylesheet(url: string) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to fetch font stylesheet (${response.status})`);
  const cssText = await response.text();
  const faceBlocks = cssText.match(/@font-face\s*{[^}]*}/g) || [];
  let family: string | null = null;
  const fontFaces: FontFace[] = [];
  for (const block of faceBlocks) {
    const familyMatch = block.match(/font-family:\s*['"]?([^;'"]+)['"]?/);
    const urlMatch = block.match(/url\(\s*['"]?([^'")]+)['"]?\s*\)/);
    if (!familyMatch || !urlMatch) continue;
    family = familyMatch[1].trim();
    const descriptors: Record<string, string> = {};
    const weightMatch = block.match(/font-weight:\s*([^;]+);/);
    const styleMatch = block.match(/font-style:\s*([^;]+);/);
    const rangeMatch = block.match(/unicode-range:\s*([^;]+);/);
    if (weightMatch) descriptors.weight = weightMatch[1].trim();
    if (styleMatch) descriptors.style = styleMatch[1].trim();
    if (rangeMatch) descriptors.unicodeRange = rangeMatch[1].trim();
    fontFaces.push(new FontFace(family, `url(${urlMatch[1]})`, descriptors));
  }
  if (!family) throw new Error("No @font-face rule found in the stylesheet");
  await Promise.allSettled(fontFaces.map(async face => {
    await face.load();
    document.fonts.add(face);
  }));
  return family;
}

async function loadFontFromFile(url: string) {
  const family = deriveFontFamilyFromUrl(url);
  const fontFace = new FontFace(family, `url(${url})`);
  await fontFace.load();
  document.fonts.add(fontFace);
  return family;
}

async function loadCustomFont(fontUrl: string) {
  const isStylesheet = fontUrl.includes("fonts.googleapis.com") || /\.css(\?.*)?$/i.test(fontUrl);
  return isStylesheet ? loadFontFromStylesheet(fontUrl) : loadFontFromFile(fontUrl);
}

async function resolveFont(font: string, fontUrl?: string): Promise<string> {
  const effectiveUrl = fontUrl || (font === DEFAULT_FONT ? DEFAULT_FONT_URL : undefined);
  if (!effectiveUrl) {
    if (document.fonts && document.fonts.load) {
      try { await document.fonts.load(font); await document.fonts.ready; } catch { /* ignore */ }
    }
    return font;
  }
  try {
    const family = await loadCustomFont(effectiveUrl);
    const sizeMatch = font.match(/^\s*(.*?\d+px)/);
    const prefix = sizeMatch ? sizeMatch[1].trim() : "bold 30px";
    return `${prefix} "${family}"`;
  } catch (err) {
    console.error("CircularGallery: unable to load font from", fontUrl, err);
    return font;
  }
}

function getFontSize(font: string) {
  const match = font.match(/(\d+)px/);
  return match ? parseInt(match[1], 10) : 30;
}

function createTextTexture(
  gl: any,
  text: string,
  font = "bold 30px monospace",
  color = "black",
) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  ctx.font = font;
  const metrics = ctx.measureText(text);
  const textWidth = Math.ceil(metrics.width);
  const textHeight = Math.ceil(getFontSize(font) * 1.2);
  canvas.width = textWidth + 20;
  canvas.height = textHeight + 20;
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textBaseline = "middle";
  ctx.textAlign = "center";
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
  const texture = new Texture(gl, { generateMipmaps: false });
  texture.image = canvas;
  return { texture, width: canvas.width, height: canvas.height };
}

// ─── Title class ─────────────────────────────────
class Title {
  gl: any;
  plane: Mesh;
  renderer: Renderer;
  text: string;
  textColor: string;
  font: string;
  mesh!: Mesh;

  constructor({
    gl, plane, renderer, text, textColor = "#545050", font = "30px sans-serif",
  }: {
    gl: any;
    plane: Mesh;
    renderer: Renderer;
    text: string;
    textColor?: string;
    font?: string;
  }) {
    autoBind(this);
    this.gl = gl;
    this.plane = plane;
    this.renderer = renderer;
    this.text = text;
    this.textColor = textColor;
    this.font = font;
    this.createMesh();
  }

  createMesh() {
    const { texture, width, height } = createTextTexture(this.gl, this.text, this.font, this.textColor);
    const geometry = new Plane(this.gl);
    const program = new Program(this.gl, {
      vertex: `
        attribute vec3 position;
        attribute vec2 uv;
        uniform mat4 modelViewMatrix;
        uniform mat4 projectionMatrix;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragment: `
        precision highp float;
        uniform sampler2D tMap;
        varying vec2 vUv;
        void main() {
          vec4 color = texture2D(tMap, vUv);
          if (color.a < 0.1) discard;
          gl_FragColor = color;
        }
      `,
      uniforms: { tMap: { value: texture } },
      transparent: true,
    });
    this.mesh = new Mesh(this.gl, { geometry, program });
    const aspect = width / height;
    const textHeight = this.plane.scale.y * 0.15;
    const textWidth = textHeight * aspect;
    this.mesh.scale.set(textWidth, textHeight, 1);
    this.mesh.position.y = -this.plane.scale.y * 0.5 - textHeight * 0.5 - 0.05;
    this.mesh.setParent(this.plane);
  }
}

// ─── Media class ─────────────────────────────────
class Media {
  extra = 0;
  geometry: Plane;
  gl: any;
  image: string;
  index: number;
  length: number;
  renderer: Renderer;
  scene: Transform;
  screen!: { width: number; height: number };
  text: string;
  viewport!: { width: number; height: number };
  bend: number;
  textColor: string;
  borderRadius: number;
  font: string;
  program!: Program;
  plane!: Mesh;
  title!: Title;
  scale!: number;
  padding!: number;
  width!: number;
  widthTotal!: number;
  x!: number;
  speed = 0;
  isBefore = false;
  isAfter = false;

  constructor({
    geometry, gl, image, index, length, renderer, scene, screen, text, viewport, bend, textColor, borderRadius, font,
  }: {
    geometry: Plane; gl: any; image: string; index: number; length: number;
    renderer: Renderer; scene: Transform; screen: { width: number; height: number };
    text: string; viewport: { width: number; height: number };
    bend: number; textColor: string; borderRadius: number; font: string;
  }) {
    this.geometry = geometry;
    this.gl = gl;
    this.image = image;
    this.index = index;
    this.length = length;
    this.renderer = renderer;
    this.scene = scene;
    this.screen = screen;
    this.text = text;
    this.viewport = viewport;
    this.bend = bend;
    this.textColor = textColor;
    this.borderRadius = borderRadius;
    this.font = font;
    this.createShader();
    this.createMesh();
    this.createTitle();
    this.onResize();
  }

  createShader() {
    const texture = new Texture(this.gl, { generateMipmaps: true });
    this.program = new Program(this.gl, {
      depthTest: false,
      depthWrite: false,
      vertex: `
        precision highp float;
        attribute vec3 position;
        attribute vec2 uv;
        uniform mat4 modelViewMatrix;
        uniform mat4 projectionMatrix;
        uniform float uTime;
        uniform float uSpeed;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          vec3 p = position;
          p.z = (sin(p.x * 4.0 + uTime) * 1.5 + cos(p.y * 2.0 + uTime) * 1.5) * (0.1 + uSpeed * 0.5);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
        }
      `,
      fragment: `
        precision highp float;
        uniform vec2 uImageSizes;
        uniform vec2 uPlaneSizes;
        uniform sampler2D tMap;
        uniform float uBorderRadius;
        varying vec2 vUv;

        float roundedBoxSDF(vec2 p, vec2 b, float r) {
          vec2 d = abs(p) - b;
          return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - r;
        }

        void main() {
          vec2 ratio = vec2(
            min((uPlaneSizes.x / uPlaneSizes.y) / (uImageSizes.x / uImageSizes.y), 1.0),
            min((uPlaneSizes.y / uPlaneSizes.x) / (uImageSizes.y / uImageSizes.x), 1.0)
          );
          vec2 uv = vec2(
            vUv.x * ratio.x + (1.0 - ratio.x) * 0.5,
            vUv.y * ratio.y + (1.0 - ratio.y) * 0.5
          );
          vec4 color = texture2D(tMap, uv);

          float d = roundedBoxSDF(vUv - 0.5, vec2(0.5 - uBorderRadius), uBorderRadius);
          float edgeSmooth = 0.002;
          float alpha = 1.0 - smoothstep(-edgeSmooth, edgeSmooth, d);

          gl_FragColor = vec4(color.rgb, alpha);
        }
      `,
      uniforms: {
        tMap: { value: texture },
        uPlaneSizes: { value: [0, 0] },
        uImageSizes: { value: [0, 0] },
        uSpeed: { value: 0 },
        uTime: { value: 100 * Math.random() },
        uBorderRadius: { value: this.borderRadius },
      },
      transparent: true,
    });
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = this.image;
    img.onload = () => {
      texture.image = img;
      this.program.uniforms.uImageSizes.value = [img.naturalWidth, img.naturalHeight];
    };
  }

  createMesh() {
    this.plane = new Mesh(this.gl, { geometry: this.geometry, program: this.program });
    this.plane.setParent(this.scene);
  }

  createTitle() {
    this.title = new Title({
      gl: this.gl, plane: this.plane, renderer: this.renderer,
      text: this.text, textColor: this.textColor, font: this.font,
    });
  }

  update(scroll: Record<string, number>, direction: string) {
    this.plane.position.x = this.x - scroll.current - this.extra;
    const x = this.plane.position.x;
    const H = this.viewport.width / 2;
    if (this.bend === 0) {
      this.plane.position.y = 0;
      this.plane.rotation.z = 0;
    } else {
      const B_abs = Math.abs(this.bend);
      const R = (H * H + B_abs * B_abs) / (2 * B_abs);
      const effectiveX = Math.min(Math.abs(x), H);
      const arc = R - Math.sqrt(R * R - effectiveX * effectiveX);
      if (this.bend > 0) {
        this.plane.position.y = -arc;
        this.plane.rotation.z = -Math.sign(x) * Math.asin(effectiveX / R);
      } else {
        this.plane.position.y = arc;
        this.plane.rotation.z = Math.sign(x) * Math.asin(effectiveX / R);
      }
    }
    this.speed = scroll.current - scroll.last;
    this.program.uniforms.uTime.value += 0.04;
    this.program.uniforms.uSpeed.value = this.speed;
    const planeOffset = this.plane.scale.x / 2;
    const viewportOffset = this.viewport.width / 2;
    this.isBefore = this.plane.position.x + planeOffset < -viewportOffset;
    this.isAfter = this.plane.position.x - planeOffset > viewportOffset;
    if (direction === "right" && this.isBefore) {
      this.extra -= this.widthTotal;
      this.isBefore = this.isAfter = false;
    }
    if (direction === "left" && this.isAfter) {
      this.extra += this.widthTotal;
      this.isBefore = this.isAfter = false;
    }
  }

  onResize(resizeData?: { screen?: { width: number; height: number }; viewport?: { width: number; height: number } }) {
    if (resizeData?.screen) this.screen = resizeData.screen;
    if (resizeData?.viewport) this.viewport = resizeData.viewport;
    this.scale = this.screen.height / 1500;
    this.plane.scale.y = (this.viewport.height * (900 * this.scale)) / this.screen.height;
    this.plane.scale.x = (this.viewport.width * (700 * this.scale)) / this.screen.width;
    this.plane.program.uniforms.uPlaneSizes.value = [this.plane.scale.x, this.plane.scale.y];
    this.padding = 2;
    this.width = this.plane.scale.x + this.padding;
    this.widthTotal = this.width * this.length;
    this.x = this.width * this.index;
  }
}

// ─── App class ───────────────────────────────────
class GalleryApp {
  container: HTMLElement;
  renderer!: Renderer;
  gl!: any;
  camera!: Camera;
  scene!: Transform;
  planeGeometry!: Plane;
  mediasImages!: GalleryItem[];
  medias!: Media[];
  screen!: { width: number; height: number };
  viewport!: { width: number; height: number };
  scroll: { ease: number; current: number; target: number; last: number };
  scrollSpeed: number;
  isDown = false;
  start = 0;
  raf = 0;
  scrollPosition = 0;
  /** Track mouse/finger position at start to distinguish click from drag */
  startY = 0;
  /** callback invoked when the user clicks/taps a gallery item */
  onClickItem?: (index: number) => void;
  boundOnResize!: () => void;
  boundOnWheel!: (e: WheelEvent) => void;
  boundOnTouchDown!: (e: MouseEvent | TouchEvent) => void;
  boundOnTouchMove!: (e: MouseEvent | TouchEvent) => void;
  boundOnTouchUp!: () => void;
  boundOnKeyDown!: (e: KeyboardEvent) => void;
  onCheckDebounce: () => void;

  constructor(container: HTMLElement, opts: {
    items?: GalleryItem[];
    bend?: number;
    textColor?: string;
    borderRadius?: number;
    font?: string;
    scrollSpeed?: number;
    scrollEase?: number;
    onClickItem?: (index: number) => void;
  }) {
    this.container = container;
    this.onClickItem = opts.onClickItem;
    this.scrollSpeed = opts.scrollSpeed ?? 2;
    this.scroll = {
      ease: opts.scrollEase ?? 0.05,
      current: 0, target: 0, last: 0,
    };
    this.onCheckDebounce = debounce(this.onCheck, 200);
    this.createRenderer();
    this.createCamera();
    this.createScene();
    this.onResize();
    this.createGeometry();
    this.createMedias(opts);
    this.update();
    this.addEventListeners();
  }

  createRenderer() {
    this.renderer = new Renderer({
      alpha: true,
      antialias: true,
      dpr: Math.min(window.devicePixelRatio || 1, 2),
    });
    this.gl = this.renderer.gl;
    this.gl.clearColor(0, 0, 0, 0);
    this.container.appendChild(this.gl.canvas as HTMLCanvasElement);
  }

  createCamera() {
    this.camera = new Camera(this.gl);
    this.camera.fov = 45;
    this.camera.position.z = 20;
  }

  createScene() { this.scene = new Transform(); }

  createGeometry() {
    this.planeGeometry = new Plane(this.gl, { heightSegments: 50, widthSegments: 100 });
  }

  createMedias(opts: {
    items?: GalleryItem[]; bend?: number; textColor?: string; borderRadius?: number; font?: string;
  }) {
    const galleryItems = opts.items && opts.items.length ? opts.items : [];
    this.mediasImages = galleryItems.concat(galleryItems);
    this.medias = this.mediasImages.map((data, index) => {
      return new Media({
        geometry: this.planeGeometry,
        gl: this.gl,
        image: data.image,
        index,
        length: this.mediasImages.length,
        renderer: this.renderer,
        scene: this.scene,
        screen: this.screen,
        text: data.text,
        viewport: this.viewport,
        bend: opts.bend ?? 3,
        textColor: opts.textColor ?? "#ffffff",
        borderRadius: opts.borderRadius ?? 0.05,
        font: opts.font ?? "bold 30px Figtree",
      });
    });
  }

  onTouchDown(e: MouseEvent | TouchEvent) {
    this.isDown = true;
    this.scrollPosition = this.scroll.current;
    this.start = "touches" in e ? e.touches[0].clientX : e.clientX;
    this.startY = "touches" in e ? e.touches[0].clientY : e.clientY;
  }

  onTouchMove(e: MouseEvent | TouchEvent) {
    if (!this.isDown) return;
    const x = "touches" in e ? e.touches[0].clientX : e.clientX;
    const distance = (this.start - x) * (this.scrollSpeed * 0.025);
    this.scroll.target = this.scrollPosition + distance;
  }

  onTouchUp(e?: MouseEvent | TouchEvent) {
    if (this.isDown && this.onClickItem) {
      // Check if this was a click (no significant movement) or a drag
      let movedX = 0;
      let movedY = 0;
      if (e) {
        const endX = "changedTouches" in e ? e.changedTouches[0].clientX : (e as MouseEvent).clientX;
        const endY = "changedTouches" in e ? e.changedTouches[0].clientY : (e as MouseEvent).clientY;
        movedX = Math.abs(endX - this.start);
        movedY = Math.abs(endY - this.startY);
      }
      if (movedX < 8 && movedY < 8) {
        this.onClickItem(this.getCenteredIndex());
      }
    }
    this.isDown = false;
    this.onCheck();
  }

  /** Determine the centered item index from the current scroll position */
  getCenteredIndex(): number {
    if (!this.medias || this.medias.length === 0) return 0;
    const first = this.medias[0];
    const halfLength = this.medias.length / 2;
    const rawIndex = this.scroll.target / first.width;
    const half = Math.round(halfLength);
    const wrapped = ((Math.round(rawIndex) % half) + half) % half;
    return wrapped;
  }

  onWheel(e: WheelEvent) {
    const delta = e.deltaY || 0;
    this.scroll.target += (delta > 0 ? this.scrollSpeed : -this.scrollSpeed) * 0.2;
    this.onCheckDebounce();
  }

  onKeyDown(e: KeyboardEvent) {
    switch (e.key) {
      case "ArrowRight": e.preventDefault(); this.scroll.target += this.scrollSpeed * 5; this.onCheckDebounce(); break;
      case "ArrowLeft": e.preventDefault(); this.scroll.target -= this.scrollSpeed * 5; this.onCheckDebounce(); break;
      case "Home": e.preventDefault(); this.scroll.target = 0; this.onCheckDebounce(); break;
    }
  }

  onCheck() {
    if (!this.medias || !this.medias[0]) return;
    const width = this.medias[0].width;
    const itemIndex = Math.round(Math.abs(this.scroll.target) / width);
    const item = width * itemIndex;
    this.scroll.target = this.scroll.target < 0 ? -item : item;
  }

  onResize() {
    this.screen = { width: this.container.clientWidth, height: this.container.clientHeight };
    this.renderer.setSize(this.screen.width, this.screen.height);
    this.camera.perspective({ aspect: this.screen.width / this.screen.height });
    const fov = (this.camera.fov * Math.PI) / 180;
    const height = 2 * Math.tan(fov / 2) * this.camera.position.z;
    const width = height * this.camera.aspect;
    this.viewport = { width, height };
    if (this.medias) {
      this.medias.forEach(m => m.onResize({ screen: this.screen, viewport: this.viewport }));
    }
  }

  update() {
    this.scroll.current = lerp(this.scroll.current, this.scroll.target, this.scroll.ease);
    const direction = this.scroll.current > this.scroll.last ? "right" : "left";
    if (this.medias) this.medias.forEach(m => m.update(this.scroll, direction));
    this.renderer.render({ scene: this.scene, camera: this.camera });
    this.scroll.last = this.scroll.current;
    this.raf = window.requestAnimationFrame(() => this.update());
  }

  addEventListeners() {
    this.boundOnResize = this.onResize.bind(this);
    this.boundOnWheel = this.onWheel.bind(this);
    this.boundOnTouchDown = this.onTouchDown.bind(this);
    this.boundOnTouchMove = this.onTouchMove.bind(this);
    this.boundOnTouchUp = this.onTouchUp.bind(this);
    this.boundOnKeyDown = this.onKeyDown.bind(this);
    window.addEventListener("resize", this.boundOnResize);
    window.addEventListener("mousewheel", this.boundOnWheel as EventListener);
    window.addEventListener("wheel", this.boundOnWheel as EventListener);
    window.addEventListener("mousedown", this.boundOnTouchDown);
    window.addEventListener("mousemove", this.boundOnTouchMove);
    window.addEventListener("mouseup", this.boundOnTouchUp as EventListener);
    window.addEventListener("touchstart", this.boundOnTouchDown as EventListener);
    window.addEventListener("touchmove", this.boundOnTouchMove as EventListener);
    window.addEventListener("touchend", this.boundOnTouchUp as EventListener);
    this.container.addEventListener("keydown", this.boundOnKeyDown);
  }

  destroy() {
    window.cancelAnimationFrame(this.raf);
    window.removeEventListener("resize", this.boundOnResize);
    window.removeEventListener("mousewheel", this.boundOnWheel as EventListener);
    window.removeEventListener("wheel", this.boundOnWheel as EventListener);
    window.removeEventListener("mousedown", this.boundOnTouchDown);
    window.removeEventListener("mousemove", this.boundOnTouchMove);
    window.removeEventListener("mouseup", this.boundOnTouchUp as EventListener);
    window.removeEventListener("touchstart", this.boundOnTouchDown as EventListener);
    window.removeEventListener("touchmove", this.boundOnTouchMove as EventListener);
    window.removeEventListener("touchend", this.boundOnTouchUp as EventListener);
    this.container.removeEventListener("keydown", this.boundOnKeyDown);
    if (this.renderer?.gl?.canvas?.parentNode) {
      this.renderer.gl.canvas.parentNode.removeChild(this.renderer.gl.canvas);
    }
  }
}

// ─── Component lifecycle ─────────────────────────
let appInstance: GalleryApp | null = null;

onMounted(() => {
  if (!containerRef.value) return;
  let cancelled = false;

  resolveFont(props.font, props.fontUrl).then(resolvedFont => {
    if (cancelled || !containerRef.value) return;
    appInstance = new GalleryApp(containerRef.value, {
      items: props.items,
      bend: props.bend,
      textColor: props.textColor,
      borderRadius: props.borderRadius,
      font: resolvedFont,
      scrollSpeed: props.scrollSpeed,
      scrollEase: props.scrollEase,
      onClickItem: (index) => emit("onItemClick", index),
    });
  });

  onBeforeUnmount(() => {
    cancelled = true;
    if (appInstance) appInstance.destroy();
  });
});
</script>

<style scoped>
.circular-gallery {
  width: 100%;
  height: 100%;
  overflow: hidden;
  cursor: grab;
}
.circular-gallery:active {
  cursor: grabbing;
}
.circular-gallery.clickable {
  cursor: pointer;
}
.circular-gallery.clickable:active {
  cursor: grabbing;
}
.circular-gallery:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 4px;
}
</style>
