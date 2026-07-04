// 个人中心 / 我的训练
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDate, formatDuration, getWeekRange } = require('../../utils/util');
const app = getApp();

Page({
  data: {
    statusBarHeight: 44,
    userInfo: {},
    stats: { totalSessions: 0, averageScore: 0, totalDuration: 0 },
    trendDays: [],
    weeklyAvg: 0,
    recentSessions: [],
    trendSVG: '',
    honor: { bestScore: 0, streakDays: 0, toImprove: 0 },
  },

  onLoad() {
    try {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 });
    } catch (e) {}
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({ userInfo });

    try {
      const stats = await ApiClient.get('/api/dashboard/stats').catch(() => ({}));

      // 处理本周趋势
      const trendData = (stats.recent_trend || []).slice(-7);
      const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '今天'];
      const padTrend = this.padTrendToSeven(trendData, labels);
      const trendDays = padTrend.map((item, idx) => {
        const score = item.score || 0;
        const yPct = score > 0 ? Math.max(8, (score / 100) * 100) : 0;
        return {
          date: item.date,
          score,
          xPct: (idx / (padTrend.length - 1)) * 100,
          yPct,
        };
      });

      this.setData({
        trendDays,
        trendSVG: this.buildTrendSVG(trendDays),
        weeklyAvg: this.computeAverage(trendDays),
        stats: {
          totalSessions: stats.total_sessions || 0,
          averageScore: Math.round(stats.average_score || 0),
          totalDuration: stats.total_duration_minutes || 0,
        },
      });

      // 计算荣誉
      const allScores = (stats.recent_sessions || []).map(s => s.average_score || 0);
      const best = allScores.length > 0 ? Math.max(...allScores) : 0;
      this.setData({
        honor: {
          bestScore: Math.round(best),
          streakDays: this.calcStreak(stats.recent_sessions || []),
          toImprove: this.calcToImprove(stats.exercise_stats || {}),
        }
      });

      // 加载最近训练
      this.loadRecent();
    } catch (err) {
      console.error('Load profile error:', err);
    }
  },

  padTrendToSeven(trendData, labels) {
    if (trendData.length >= 7) return trendData.slice(-7);
    const out = [...trendData];
    while (out.length < 7) {
      out.unshift({ date: labels[6 - (7 - out.length)], score: 0 });
    }
    // 把 date 用 day 标签覆盖最后 7 个
    return out.map((item, idx) => ({ ...item, date: labels[idx] || item.date }));
  },

  computeAverage(trendDays) {
    const valid = trendDays.filter(d => d.score > 0);
    if (valid.length === 0) return 0;
    return Math.round(valid.reduce((a, b) => a + b.score, 0) / valid.length);
  },

  calcStreak(sessions) {
    if (!sessions.length) return 0;
    let streak = 0;
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      const has = sessions.some(s => (s.created_at || '').slice(0, 10) === key);
      if (has) streak++;
      else if (i > 0) break;
    }
    return streak;
  },

  calcToImprove(stats) {
    return Object.values(stats).filter(s => (s.average_score || 0) < 75).length;
  },

  buildTrendSVG(trendDays) {
    // viewBox 用 340 x 280，rich-text 会按容器宽度自适应
    const w = 340;
    const h = 280;
    const padX = 20;
    const padTop = 30;
    const padBottom = 20;
    const innerW = w - padX * 2;
    const innerH = h - padTop - padBottom;

    // 仅对 score>0 的点画线
    const valid = trendDays.filter(d => d.score > 0);
    if (valid.length === 0) {
      return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="100%" height="100%"></svg>`;
    }

    const points = valid.map(d => {
      const x = padX + (d.xPct / 100) * innerW;
      const y = padTop + (1 - d.yPct / 100) * innerH;
      return { x, y, score: d.score };
    });

    // 折线（圆滑）& 填充区
    const smooth = (pts) => {
      if (pts.length < 2) return '';
      let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i - 1] || pts[i];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = pts[i + 2] || p2;
        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;
        d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)} ${cp2x.toFixed(1)} ${cp2y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
      }
      return d;
    };

    const linePath = smooth(points);
    const last = points[points.length - 1];
    const first = points[0];
    const areaPath = `${linePath} L ${last.x.toFixed(1)} ${(padTop + innerH).toFixed(1)} L ${first.x.toFixed(1)} ${(padTop + innerH).toFixed(1)} Z`;

    const dots = points.map(p => `<g><text x="${p.x.toFixed(1)}" y="${(p.y - 14).toFixed(1)}" font-size="20" font-weight="600" fill="#4f8cff" text-anchor="middle">${p.score}</text><circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="5" fill="#4f8cff" stroke="#cbe0ff" stroke-width="3" /></g>`).join('');

    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="100%" height="100%" preserveAspectRatio="none">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#4f8cff" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#4f8cff" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path d="${areaPath}" fill="url(#trendFill)" />
      <path d="${linePath}" fill="none" stroke="#4f8cff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      ${dots}
    </svg>`;
  },

  async loadRecent() {
    try {
      const range = getWeekRange();
      const sessionsData = await ApiClient.get('/api/sessions', { date_from: range.from, date_to: range.to, limit: 4 }).catch(() => null);
      if (sessionsData && sessionsData.items) {
        const recentSessions = sessionsData.items.slice(0, 4).map(s => {
          const config = EXERCISE_CONFIG[s.exercise] || {};
          const score = Math.round(s.average_score || 0);
          const level = getScoreLevel(score);
          return {
            session_id: s.session_id,
            exercise_name: config.name || s.exercise || '训练',
            icon: config.icon || '🏋️',
            date: formatDate(s.created_at, 'MM-DD HH:mm'),
            score,
            scoreColor: level.color,
            duration: formatDuration(s.duration_seconds || 0),
          };
        });
        this.setData({ recentSessions });
      }
    } catch (err) {
      console.error('Load recent sessions error:', err);
    }
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  goToReports() {
    wx.switchTab({ url: '/pages/reports/reports' });
  },

  handleLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      success: (res) => {
        if (res.confirm) {
          const AuthManager = require('../../utils/auth');
          AuthManager.logout();
          wx.reLaunch({ url: '/pages/login/login' });
        }
      },
    });
  },

  onTapSession(e) {
    // 暂不处理
  },
});
