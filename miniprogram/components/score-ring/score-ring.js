// 分数环形图组件
const { getScoreLevel } = require('../../utils/constants');

Component({
  properties: {
    score: {
      type: Number,
      value: 0,
      observer: 'draw'
    },
    size: {
      type: Number,
      value: 200       // rpx
    },
    lineWidth: {
      type: Number,
      value: 10        // rpx
    }
  },

  data: {
    scoreColor: '#3b82f6',
    levelLabel: ''
  },

  lifetimes: {
    attached() {
      // 延迟绘制等 canvas ready
      setTimeout(() => this.draw(), 200);
    }
  },

  methods: {
    draw() {
      const query = this.createSelectorQuery();
      query.select('#scoreRingCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0] || !res[0].node) return;

          const canvas = res[0].node;
          const size = this.properties.size;
          const dpr = wx.getSystemInfoSync().pixelRatio;

          canvas.width = size * dpr;
          canvas.height = size * dpr;

          const ctx = canvas.getContext('2d');
          ctx.scale(dpr, dpr);

          const centerX = size / 2;
          const centerY = size / 2;
          const radius = (size - this.properties.lineWidth) / 2;
          const lineWidth = this.properties.lineWidth;

          const score = Math.min(100, Math.max(0, this.properties.score));
          const level = getScoreLevel(score);
          const color = level.color;

          this.setData({
            scoreColor: color,
            levelLabel: level.label
          });

          // 清除
          ctx.clearRect(0, 0, size, size);

          // 背景圆环
          ctx.beginPath();
          ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
          ctx.lineWidth = lineWidth;
          ctx.lineCap = 'round';
          ctx.stroke();

          // 进度圆环
          const startAngle = -Math.PI / 2;
          const endAngle = startAngle + (score / 100) * 2 * Math.PI;

          ctx.beginPath();
          ctx.arc(centerX, centerY, radius, startAngle, endAngle);
          ctx.strokeStyle = color;
          ctx.lineWidth = lineWidth;
          ctx.lineCap = 'round';
          ctx.stroke();
        });
    }
  }
});
