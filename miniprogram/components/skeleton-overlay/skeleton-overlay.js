const { SKELETON_CONNECTIONS } = require('../../utils/constants');

const VISIBLE_THRESHOLD = 0.2;
const IMPORTANT_POINTS = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28];

Component({
  properties: {
    keypoints: {
      type: Array,
      value: null,
      observer: 'onKeypointsChange',
    },
    mirrored: {
      type: Boolean,
      value: true,
      observer: 'onOverlayPropsChange',
    },
    canvasWidth: {
      type: Number,
      value: 360,
      observer: 'onCanvasSizeChange',
    },
    canvasHeight: {
      type: Number,
      value: 640,
      observer: 'onCanvasSizeChange',
    },
  },

  data: {
    initialized: false,
    renderLines: [],
    renderPoints: [],
  },

  lifetimes: {
    attached() {
      this.initCanvas();
    },
    detached() {
      this._canvas = null;
      this._ctx = null;
    },
  },

  methods: {
    initCanvas() {
      this.createSelectorQuery()
        .select('#skeletonCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0]) return;

          const canvas = res[0].node;
          const ctx = canvas.getContext('2d');
          this._canvas = canvas;
          this._ctx = ctx;
          this.resizeCanvas();
          this.setData({ initialized: true });

          if (this.properties.keypoints) {
            this.renderSkeleton(this.properties.keypoints);
          }
        });
    },

    onCanvasSizeChange() {
      if (this._canvas && this._ctx) {
        this.resizeCanvas();
      }
      this.renderSkeleton(this.properties.keypoints);
    },

    onOverlayPropsChange() {
      this.renderSkeleton(this.properties.keypoints);
    },

    onKeypointsChange(newVal) {
      this.renderSkeleton(newVal);
    },

    resizeCanvas() {
      const canvas = this._canvas;
      const ctx = this._ctx;
      if (!canvas || !ctx) return;

      const dpr = wx.getSystemInfoSync().pixelRatio || 1;
      canvas.width = this.properties.canvasWidth * dpr;
      canvas.height = this.properties.canvasHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    },

    renderSkeleton(keypoints) {
      if (!keypoints || keypoints.length === 0) {
        this.clear();
        return;
      }
      // 只用 canvas 绘制（drawCanvasSkeleton 内部已 clearRect 每帧清屏）
      // 不再用 DOM（cover-view）骨架，避免两套重叠
      this.drawCanvasSkeleton(keypoints);
    },

    buildOverlay(keypoints) {
      const lines = [];
      const points = [];
      const w = Number(this.properties.canvasWidth) || 360;
      const h = Number(this.properties.canvasHeight) || 640;

      SKELETON_CONNECTIONS.forEach(([i, j], index) => {
        const p1 = this.projectPoint(keypoints[i], w, h);
        const p2 = this.projectPoint(keypoints[j], w, h);
        if (!p1 || !p2) return;

        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        if (!Number.isFinite(length) || length <= 1) return;

        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        const partClass = (i >= 11 && i <= 22) ? 'arm' : ((i >= 23 && i <= 32) ? 'leg' : 'body');
        lines.push({
          key: `${i}-${j}-${index}`,
          partClass,
          style: [
            `left:${p1.x}px`,
            `top:${p1.y}px`,
            `width:${length}px`,
            `transform:rotate(${angle}deg)`,
          ].join(';'),
        });
      });

      keypoints.forEach((kp, index) => {
        const point = this.projectPoint(kp, w, h);
        if (!point) return;
        points.push({
          key: `p-${index}`,
          important: IMPORTANT_POINTS.includes(index),
          style: `left:${point.x}px;top:${point.y}px`,
        });
      });

      return { lines, points };
    },

    projectPoint(kp, w, h) {
      if (!this.isVisible(kp)) return null;
      const x = Number(kp.x);
      const y = Number(kp.y);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      return {
        x: this.properties.mirrored ? w - x * w : x * w,
        y: y * h,
      };
    },

    isVisible(kp) {
      if (!kp) return false;
      const visibility = kp.visibility == null ? 1 : Number(kp.visibility);
      return visibility >= VISIBLE_THRESHOLD;
    },

    drawCanvasSkeleton(keypoints) {
      const ctx = this._ctx;
      const w = this.properties.canvasWidth;
      const h = this.properties.canvasHeight;
      if (!ctx) return;

      ctx.clearRect(0, 0, w, h);

      SKELETON_CONNECTIONS.forEach(([i, j]) => {
        const p1 = this.projectPoint(keypoints[i], w, h);
        const p2 = this.projectPoint(keypoints[j], w, h);
        if (!p1 || !p2) return;

        const isArm = (i >= 11 && i <= 22);
        const isLeg = (i >= 23 && i <= 32);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = isArm ? '#3b82f6' : (isLeg ? '#22c55e' : '#f59e0b');
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.stroke();
      });

      keypoints.forEach((kp, index) => {
        const point = this.projectPoint(kp, w, h);
        if (!point) return;
        const radius = IMPORTANT_POINTS.includes(index) ? 5 : 3.5;
        ctx.beginPath();
        ctx.arc(point.x, point.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    },

    updateKeypoints(keypoints) {
      this.setData({ keypoints }, () => {
        this.renderSkeleton(keypoints);
      });
    },

    clear() {
      if (this._ctx) {
        this._ctx.clearRect(0, 0, this.properties.canvasWidth, this.properties.canvasHeight);
      }
      this.setData({
        renderLines: [],
        renderPoints: [],
      });
    },
  },
});
