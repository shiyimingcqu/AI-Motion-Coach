// 训练报告页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDate, formatDuration, getWeekRange, getMonthRange } = require('../../utils/util');

Page({
  data: {
    timeRanges: [
      { label: '本周', value: 'week' },
      { label: '本月', value: 'month' },
      { label: '全部', value: 'all' }
    ],
    timeRange: 'week',
    summary: {
      totalSessions: 0,
      averageScore: 0,
      totalDuration: 0,
      accuracy: 0
    },
    exerciseStats: [],
    sessions: [],
    loading: true
  },

  onShow() {
    this.loadData();
  },

  switchTimeRange(e) {
    this.setData({ timeRange: e.currentTarget.dataset.value });
    this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });

    try {
      let dateFrom, dateTo;

      if (this.data.timeRange === 'week') {
        const range = getWeekRange();
        dateFrom = range.from;
        dateTo = range.to;
      } else if (this.data.timeRange === 'month') {
        const range = getMonthRange();
        dateFrom = range.from;
        dateTo = range.to;
      }

      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      // 获取报告和个人统计
      const [reportData, sessionsData] = await Promise.all([
        ApiClient.get('/api/reports/personal', params).catch(() => null),
        ApiClient.get('/api/sessions', { ...params, limit: 50 }).catch(() => null),
      ]);

      // 处理汇总
      if (reportData) {
        const total = reportData.total_sessions || 0;
        const valid = reportData.total_valid || 0;
        this.setData({
          summary: {
            totalSessions: total,
            averageScore: Math.round(reportData.average_score || 0),
            totalDuration: reportData.total_duration_minutes || 0,
            accuracy: total > 0 ? Math.round((valid / Math.max(total, 1)) * 100) : 0,
          }
        });

        // 各项运动表现
        if (reportData.exercise_stats) {
          const stats = Object.entries(reportData.exercise_stats).map(([key, data]) => {
            const config = EXERCISE_CONFIG[key];
            const score = Math.round(data.average_score || 0);
            const level = getScoreLevel(score);
            return {
              key,
              name: config ? config.name : key,
              score,
              color: level.color,
              sessions: data.total || 0
            };
          });
          this.setData({ exerciseStats: stats });
        }
      }

      // 处理训练历史
      if (sessionsData && sessionsData.items) {
        const sessions = sessionsData.items.map(s => {
          const config = EXERCISE_CONFIG[s.exercise];
          const score = Math.round(s.average_score || 0);
          const level = getScoreLevel(score);
          return {
            session_id: s.session_id,
            exercise_name: config ? config.name : (s.exercise || '未知'),
            date: formatDate(s.created_at, 'MM-DD HH:mm'),
            score,
            scoreColor: level.color,
            duration: formatDuration(s.duration_seconds || 0),
          };
        });
        this.setData({ sessions });
      }
    } catch (err) {
      console.error('Load reports error:', err);
    } finally {
      this.setData({ loading: false });
    }
  }
});
