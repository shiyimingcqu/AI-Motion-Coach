// 骨架叠加组件 - Canvas 2D 绘制
const { SKELETON_CONNECTIONS } = require('../../utils/constants');

Component({
  properties: {
    // 关键点数据（33 点归一化坐标数组）
    keypoints: {
      type: Array,
      value: null,
      observer: 'onKeypointsChange'
    },
    // 是否使用前置摄像头（需要镜像）
    mirrored: {
      type: Boolean,
      value: true
    },
    // Canvas 宽度（rpx → px）
    canvasWidth: {
      type: Number,
      value: 360
    },
    // Canvas 高度
    canvasHeight: {
      type: Number,
      value: 640
    }
  },

  data: {
    canvas: null,
    ctx: null,
    initialized: false
  },

  lifetimes: {
    attached() {
      this.initCanvas();
    },
    detached() {
      this._canvas = null;
      this._ctx = null;
    }
  },

  methods: {
    initCanvas() {
      const query = this.createSelectorQuery();
      query.select('#skeletonCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0]) return;

          const canvas = res[0].node;
          const ctx = canvas.getContext('2d');

          const dpr = wx.getSystemInfoSync().pixelRatio;
          canvas.width = this.properties.canvasWidth * dpr;
          canvas.height = this.properties.canvasHeight * dpr;
          ctx.scale(dpr, dpr);

          this._canvas = canvas;
          this._ctx = ctx;
          this.setData({ initialized: true });

          // 如果已有关键点数据，立即绘制
          if (this.properties.keypoints) {
            this.drawSkeleton();
          }
        });
    },

    onKeypointsChange(newVal) {
      if (this._ctx && newVal && newVal.length > 0) {
        this.drawSkeleton();
      }
    },

    drawSkeleton() {
      const ctx = this._ctx;
      const keypoints = this.properties.keypoints;
      const w = this.properties.canvasWidth;
      const h = this.properties.canvasHeight;
      const mirrored = this.properties.mirrored;

      if (!ctx || !keypoints || keypoints.length === 0) return;

      // 清除画布
      ctx.clearRect(0, 0, w, h);

      // 绘制连线
      SKELETON_CONNECTIONS.forEach(([i, j]) => {
        const p1 = keypoints[i];
        const p2 = keypoints[j];

        if (!p1 || !p2 || p1.visibility < 0.5 || p2.visibility < 0.5) return;

        let x1 = p1.x * w;
        let y1 = p1.y * h;
        let x2 = p2.x * w;
        let y2 = p2.y * h;

        // 前置摄像头镜像
        if (mirrored) {
          x1 = w - x1;
          x2 = w - x2;
        }

        // 根据部位确定颜色
        const isArm = (i >= 11 && i <= 22);
        const isLeg = (i >= 23 && i <= 32);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = isArm ? '#3b82f6' : (isLeg ? '#22c55e' : '#f59e0b');
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.stroke();
      });

      // 绘制关键点
      keypoints.forEach((kp, i) => {
        if (!kp || kp.visibility < 0.5) return;

        let x = kp.x * w;
        let y = kp.y * h;
        if (mirrored) x = w - x;

        // 关键点大小（重要关节点更大）
        const importantIndices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28];
        const radius = importantIndices.includes(i) ? 4.5 : 3;

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    },

    // 外部调用：更新关键点并重绘
    updateKeypoints(keypoints) {
      this.setData({ keypoints }, () => {
        this.drawSkeleton();
      });
    },

    // 外部调用：清除画布
    clear() {
      const ctx = this._ctx;
      if (ctx) {
        ctx.clearRect(0, 0, this.properties.canvasWidth, this.properties.canvasHeight);
      }
    }
  }
});
