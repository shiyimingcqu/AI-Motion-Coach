// 训练结果 / 评估报告页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDuration, formatDate } = require('../../utils/util');

const AI_ADVICE_POLL_INTERVAL_MS = 2000;
const AI_ADVICE_POLL_TIMEOUT_MS = 90000;

const SEVERITY_TONE = {
  high: 'critical',
  error: 'critical',
  medium: 'warning',
  warning: 'warning',
  low: 'minor',
  info: 'positive',
};

const POSITIVE_LABEL = '不错';

function briefText(text, maxLen = 28) {
  if (!text) return '';
  const normalized = String(text).replace(/\s+/g, ' ').trim();
  const firstPart = normalized.split(/[。；;！!？?\n]/)[0].trim();
  const candidate = firstPart || normalized;
  if (candidate.length <= maxLen) return candidate;
  return `${candidate.slice(0, maxLen)}…`;
}

Page({
  data: {
    statusBarHeight: 44,
    exerciseConfig: {},
    exerciseName: '',
    averageScore: 0,
    durationText: '',
    finishedAt: '',
    totalCount: 0,
    validCount: 0,
    errorCount: 0,
    validRate: 0,
    levelLabel: '优秀',
    gradeLabel: '',
    evaluationSummary: '',
    stars: [1, 2, 3, 4, 5],
    scorePercent: 0,
    scoreColor: '#3b82f6',
    radar: { completion: 85, stability: 82, standard: 90, tempo: 80, speed: 88 },
    radarSVG: '',
    dimensionList: [],
    issues: [],
    suggestions: [],
    feedbackItems: [],
    displayFeedbackItems: [],
    feedbackStats: { critical: 0, warning: 0, minor: 0, positive: 0 },
    hasRealFeedback: false,
    strengths: [],
    weaknesses: [],
    recommendations: [],
    nextSteps: [],
    showDimensionDetail: false,
    dimensionPreview: [],
    aiAdvice: '',
    aiAdvicePreview: '',
    showAiAdvice: true,
    aiAdvicePending: false,
    aiAdviceFailed: false,
    reportLoading: false,
    hasBackendReport: false,
    resultData: null,
    recordSaved: false,
    savedSessionId: '',
    replayKey: '',
    showSharePreview: false,
    sharePosterUrl: '',
    sharePosterLoading: false,
  },

  onLoad(options) {
    let data = {};
    if (options.key) {
      try {
        data = wx.getStorageSync(options.key) || {};
        wx.removeStorageSync(options.key);
      } catch (e) {
        console.error('Read result cache error:', e);
      }
    } else if (options.data) {
      try { data = JSON.parse(decodeURIComponent(options.data)); }
      catch (e) { console.error('Parse result data error:', e); }
    }

    try {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 });
    } catch (e) {}

    this._aiAdvicePollTimer = null;
    this._aiAdvicePollStartedAt = 0;
    this._bootstrapStarted = false;
    this._aiAdviceDirectStarted = false;
    this.applyLocalResult(data);
    this.bootstrapReport(data);
  },

  onReady() {
    this.scheduleSharePoster();
  },

  onUnload() {
    this.clearAiAdvicePoll();
  },

  applyLocalResult(data) {
    const exerciseKey = data.exercise_key || 'squat';
    const exerciseConfig = EXERCISE_CONFIG[exerciseKey] || {};
    const score = Math.round(data.average_score || 0);
    const level = getScoreLevel(score);
    const scoreVisual = this.buildScoreVisual(score);
    const totalCount = data.total_count || 0;
    const validCount = data.valid_count || 0;
    const validRate = totalCount > 0 ? Math.round((validCount / totalCount) * 100) : 0;

    const realIssues = data.issues || [];
    const realSuggestions = data.suggestions || [];

    const radar = this.buildRadarData(score, data);

    const dimensionList = this.buildDimensionListFromRadar(radar);

    this.setData({
      exerciseConfig,
      exerciseName: exerciseConfig.name || '',
      averageScore: score,
      durationText: formatDuration(data.duration_seconds || 0),
      finishedAt: formatDate(Date.now(), 'YYYY-MM-DD HH:mm'),
      totalCount,
      validCount,
      errorCount: data.error_count || 0,
      validRate,
      levelLabel: level.label,
      gradeLabel: level.label,
      scorePercent: scoreVisual.scorePercent,
      scoreColor: scoreVisual.scoreColor,
      stars: this.getStarList(level.label),
      radar,
      radarSVG: this.buildRadarSVG(radar),
      dimensionList,
      dimensionPreview: this.buildDimensionPreview(dimensionList),
      resultData: Object.assign({}, data, {
        issues: realIssues,
        suggestions: realSuggestions,
      }),
      savedSessionId: data.session_id || '',
      replayKey: data.replay_key || '',
      displayFeedbackItems: [],
      feedbackStats: { critical: 0, warning: 0, minor: 0, positive: 0 },
      hasRealFeedback: false,
      hasBackendReport: false,
      reportLoading: Boolean(data.session_id),
      aiAdvice: '',
      aiAdvicePreview: '',
      showAiAdvice: Boolean(data.session_id),
      aiAdvicePending: Boolean(data.session_id),
      aiAdviceFailed: false,
      nextSteps: [],
      strengths: [],
      weaknesses: [],
      recommendations: [],
      evaluationSummary: '',
      showDimensionDetail: false,
    });

    this.applyPrefetchFromSession(data);
  },

  applyPrefetchFromSession(data) {
    const summaryRaw = data.feedback_summary;
    if (!summaryRaw) return;

    const summary = this.parseFeedbackSummary(summaryRaw);
    const exerciseKey = data.exercise_key || 'squat';
    const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;
    const apiItems = this.normalizeSummaryItems(summary, exerciseKey);

    if (apiItems.length > 0) {
      const displayFeedbackItems = this.buildDisplayFeedbackItems(apiItems, {
        exerciseName,
        time: '--:--',
      });
      this.setData({
        displayFeedbackItems,
        feedbackStats: this.buildFeedbackStats(displayFeedbackItems),
        hasRealFeedback: true,
        hasBackendReport: true,
      });
    }

    const sessionId = data.session_id || '';
    if (sessionId) {
      this.loadAiAdviceFromSession({ session_id: sessionId, feedback_summary: summaryRaw });
    }
  },

  async bootstrapReport(data) {
    if (this._bootstrapStarted) return;
    this._bootstrapStarted = true;

    const hasPrefetch = this.data.hasBackendReport;
    if (!hasPrefetch) {
      this.setData({ reportLoading: true });
    }

    try {
      const resultData = Object.assign({}, data, this.data.resultData || {});
      let sessionId = resultData.session_id || this.data.savedSessionId || '';

      if (!sessionId) {
        sessionId = await this.createSessionFromResult(resultData);
        if (sessionId) {
          resultData.session_id = sessionId;
          this.setData({
            resultData,
            savedSessionId: sessionId,
            recordSaved: true,
          });
        }
      }

      const replayKey = resultData.replay_key || this.data.replayKey;
      if (sessionId && replayKey) {
        await this.uploadReplaySilently(sessionId, replayKey);
      }

      if (sessionId) {
        await this.loadBackendReport(sessionId);
      } else {
        this.setData({
          aiAdvicePending: false,
          aiAdviceFailed: true,
          aiAdvice: '未获取到训练记录，无法生成 AI 建议。',
        });
      }
    } catch (e) {
      console.warn('[Result] 自动同步报告失败:', e);
    } finally {
      this.setData({ reportLoading: false });
    }
  },

  async createSessionFromResult(data) {
    const session = await ApiClient.post('/api/sessions', {
      exercise: data.exercise_key || 'squat',
      duration_seconds: Number(data.duration_seconds || 0),
      total_count: Number(data.total_count || 0),
      valid_count: Number(data.valid_count || 0),
      error_count: Number(data.error_count || 0),
      average_score: Math.round(Number(data.average_score || 0)),
      issues: data.issues || [],
      suggestions: data.suggestions || [],
    });
    return (session && session.session_id) || '';
  },

  async uploadReplaySilently(sessionId, replayKey) {
    let replayFrames = [];
    try {
      replayFrames = wx.getStorageSync(replayKey) || [];
    } catch (e) {
      return;
    }

    const uploadReplayFrames = this.prepareReplayFramesForUpload(replayFrames);
    if (!uploadReplayFrames.length) return;

    try {
      await ApiClient.put(`/api/sessions/${sessionId}/replay`, {
        pose_replay: uploadReplayFrames,
        pose_replay_meta: {
          schema_version: 1,
          source: 'miniprogram_realtime',
          sample_interval_ms: 140,
          frame_count: uploadReplayFrames.length,
          original_frame_count: replayFrames.length,
        },
      });
      try { wx.removeStorageSync(replayKey); } catch (e) {}
      this.setData({ replayKey: '' });
    } catch (e) {
      console.warn('[Replay] 自动上传回放失败:', e);
    }
  },

  async loadBackendReport(sessionId) {
    if (!sessionId) return;

    this.setData({ reportLoading: true, savedSessionId: sessionId });

    try {
      const [reportRes, feedbackRes, sessionRes] = await Promise.all([
        ApiClient.get(`/api/reports/${sessionId}`).catch(() => null),
        ApiClient.get('/api/feedback', { session_id: sessionId, limit: 50 }).catch(() => null),
        ApiClient.get(`/api/sessions/${sessionId}`).catch(() => null),
      ]);

      this.applyBackendReport(reportRes, feedbackRes, sessionRes);
    } catch (e) {
      console.warn('[Result] 加载后端报告失败:', e);
    } finally {
      this.setData({ reportLoading: false });
    }
  },

  applyBackendReport(reportRes, feedbackRes, sessionRes) {
    const updates = { hasBackendReport: true };
    const exerciseKey = (sessionRes && sessionRes.exercise)
      || (reportRes && reportRes.exercise)
      || (this.data.resultData && this.data.resultData.exercise_key)
      || 'squat';
    const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;
    const feedbackTime = sessionRes && sessionRes.created_at
      ? String(sessionRes.created_at).slice(11, 19)
      : '--:--';

    if (reportRes) {
      const evaluation = reportRes.evaluation || {};
      const score = Math.round(reportRes.average_score || this.data.averageScore || 0);
      const level = getScoreLevel(score);

      updates.averageScore = score;
      updates.totalCount = reportRes.total_count != null ? reportRes.total_count : this.data.totalCount;
      updates.validCount = reportRes.valid_count != null ? reportRes.valid_count : this.data.validCount;
      updates.errorCount = reportRes.error_count != null ? reportRes.error_count : this.data.errorCount;
      updates.validRate = evaluation.valid_rate != null
        ? Math.round(evaluation.valid_rate)
        : (updates.totalCount > 0 ? Math.round((updates.validCount / updates.totalCount) * 100) : 0);
      updates.levelLabel = level.label;
      updates.gradeLabel = evaluation.grade_label || level.label;
      const scoreVisual = this.buildScoreVisual(score);
      updates.scorePercent = scoreVisual.scorePercent;
      updates.scoreColor = scoreVisual.scoreColor;
      updates.stars = this.getStarList(updates.gradeLabel || level.label);
      updates.evaluationSummary = evaluation.summary || '';
      updates.strengths = evaluation.strengths || [];
      updates.weaknesses = evaluation.weaknesses || [];
      updates.recommendations = evaluation.recommendations || [];

      const dimensionScores = evaluation.dimension_scores || {};
      const dimensionList = Object.keys(dimensionScores).map((label) => ({
        label,
        value: Math.round(Number(dimensionScores[label]) || 0),
      }));

      if (dimensionList.length > 0) {
        updates.dimensionList = dimensionList;
        const radar = this.buildRadarFromDimensions(dimensionList);
        updates.radar = radar;
        updates.radarSVG = this.buildRadarSVG(radar);
      }
    }

    let apiItems = (feedbackRes && feedbackRes.items) || [];
    if (sessionRes && sessionRes.feedback_summary) {
      const summaryItems = this.normalizeSummaryItems(
        this.parseFeedbackSummary(sessionRes.feedback_summary),
        exerciseKey,
      );
      if (summaryItems.length > 0) {
        apiItems = summaryItems;
      }
    }

    const displayFeedbackItems = this.buildDisplayFeedbackItems(apiItems, {
      exerciseName,
      time: feedbackTime,
    });

    const weaknesses = updates.weaknesses != null ? updates.weaknesses : this.data.weaknesses;
    const recommendations = updates.recommendations != null ? updates.recommendations : this.data.recommendations;
    const mergedFeedbackItems = this.mergeEvaluationWeaknesses(
      displayFeedbackItems,
      weaknesses,
      exerciseName,
      feedbackTime,
    );

    updates.exerciseName = exerciseName;
    updates.feedbackStats = this.buildFeedbackStats(mergedFeedbackItems);

    if (mergedFeedbackItems.length > 0) {
      updates.displayFeedbackItems = mergedFeedbackItems;
      updates.feedbackItems = this.mapFeedbackItems(apiItems);
      updates.hasRealFeedback = true;
      updates.issues = [];
      updates.suggestions = [];
    }

    updates.nextSteps = this.buildNextSteps([], recommendations, mergedFeedbackItems);

    if (updates.dimensionList && updates.dimensionList.length > 0) {
      updates.dimensionPreview = this.buildDimensionPreview(updates.dimensionList);
    } else if (this.data.dimensionList.length > 0) {
      updates.dimensionPreview = this.buildDimensionPreview(this.data.dimensionList);
    }

    if (sessionRes) {
      if (sessionRes.average_score != null) {
        updates.averageScore = Math.round(sessionRes.average_score);
      }
    }

    this.setData(updates, () => {
      if (sessionRes) {
        this.loadAiAdviceFromSession(sessionRes);
      } else if (!this.data.aiAdvice) {
        this.fetchAiAdviceDirectly();
      }
      this.scheduleSharePoster();
    });
  },

  parseFeedbackSummary(raw) {
    if (!raw) return {};
    if (typeof raw === 'object') return raw;
    try {
      return JSON.parse(raw);
    } catch (e) {
      return {};
    }
  },

  normalizeSummaryItems(summary, exercise) {
    const structured = summary.items || [];
    if (structured.length > 0) {
      return structured.map((entry, index) => ({
        id: `summary-${index}`,
        exercise,
        issue: entry.issue || '',
        suggestion: entry.suggestion || '',
        severity: entry.severity || 'warning',
      }));
    }

    const issues = summary.issues || [];
    const suggestions = summary.suggestions || [];
    if (!issues.length) return [];

    return issues.map((issue, index) => ({
      exercise,
      issue,
      suggestion: suggestions[index] || '',
      severity: index === 0 ? 'high' : index === 1 ? 'medium' : 'low',
    }));
  },

  getSeverityTypeLabel(severity) {
    if (severity === 'high' || severity === 'error') return '严重';
    if (severity === 'medium' || severity === 'warning') return '警告';
    if (severity === 'low') return '轻微';
    if (severity === 'info') return POSITIVE_LABEL;
    return '提示';
  },

  buildFeedbackStats(items) {
    const stats = { critical: 0, warning: 0, minor: 0, positive: 0 };
    (items || []).forEach((item) => {
      if (item.tone && stats[item.tone] != null) {
        stats[item.tone] += 1;
      }
    });
    return stats;
  },

  buildNextSteps(_weaknesses, recommendations, displayFeedbackItems) {
    const issueSet = new Set(
      (displayFeedbackItems || [])
        .map((item) => String(item.problem || '').trim())
        .filter(Boolean),
    );

    const steps = [];
    (recommendations || []).forEach((text) => {
      const normalized = String(text || '').trim();
      if (!normalized || issueSet.has(normalized)) return;
      steps.push({ text: normalized, type: 'recommend' });
    });

    return steps.slice(0, 4);
  },

  mergeEvaluationWeaknesses(displayItems, weaknesses, exerciseName, time) {
    const genericSkip = new Set([
      '暂无明显问题，建议维持当前训练节奏',
      '动作规范性有待提升',
    ]);
    const existing = new Set(
      (displayItems || []).map((item) => String(item.problem || '').trim()).filter(Boolean),
    );
    const merged = [...(displayItems || [])];

    (weaknesses || []).forEach((raw) => {
      const text = briefText(raw, 28);
      if (!text || genericSkip.has(String(raw).trim()) || genericSkip.has(text)) return;

      let duplicated = existing.has(text);
      if (!duplicated) {
        existing.forEach((problem) => {
          if (problem.includes(text) || text.includes(problem)) duplicated = true;
        });
      }
      if (duplicated) return;

      existing.add(text);
      merged.push({
        kind: 'error',
        tone: 'warning',
        exercise: exerciseName || '训练',
        type: '警告',
        problem: text,
        time: time || '--:--',
      });
    });

    return merged;
  },

  buildDimensionPreview(dimensionList) {
    return (dimensionList || []).slice(0, 3);
  },

  buildDisplayFeedbackItems(items, options = {}) {
    const exerciseName = options.exerciseName || '训练';
    const time = options.time || '--:--';
    const mapped = this.mapFeedbackItems(items);
    const errorItems = mapped.filter((item) => item.issue && item.severity !== 'info');
    const infoItems = mapped.filter((item) => item.severity === 'info' || (!item.issue && item.suggestion));

    const positiveNotes = [];
    infoItems.forEach((item) => {
      const note = briefText(item.suggestion || item.issue || '', 24);
      if (note) positiveNotes.push(note);
    });

    const displayItems = [];
    [...new Set(positiveNotes)].forEach((note) => {
      displayItems.push({
        kind: 'positive',
        tone: 'positive',
        exercise: exerciseName,
        type: POSITIVE_LABEL,
        problem: note,
        time,
      });
    });

    errorItems.forEach((item) => {
      const tone = SEVERITY_TONE[item.severity] || 'minor';
      displayItems.push({
        kind: 'error',
        tone,
        exercise: exerciseName,
        type: this.getSeverityTypeLabel(item.severity),
        problem: briefText(item.issue, 28),
        time,
      });
    });

    return displayItems;
  },

  mapFeedbackItems(items) {
    return (items || [])
      .filter((item) => item && (item.issue || item.suggestion))
      .map((item) => {
        const severity = item.severity || 'medium';
        const tone = SEVERITY_TONE[severity] || 'minor';

        return {
          issue: item.issue || '',
          suggestion: item.suggestion || '',
          severity,
          severityLabel: this.getSeverityTypeLabel(severity),
          tone,
          level: tone === 'critical' ? 'major' : tone === 'positive' ? 'positive' : 'minor',
        };
      });
  },

  loadAiAdviceFromSession(session) {
    const sessionId = session && session.session_id;
    const raw = session && session.feedback_summary;
    const summary = raw ? this.parseFeedbackSummary(raw) : {};
    const text = typeof summary.ai_advice === 'string' ? summary.ai_advice.trim() : '';

    if (text) {
      this.applyAiAdviceText(text);
      return;
    }

    if (summary.ai_advice_status === 'failed') {
      this.setData({
        aiAdvice: 'AI 建议生成失败，请稍后刷新重试。',
        aiAdvicePreview: '',
        aiAdvicePending: false,
        aiAdviceFailed: true,
        showAiAdvice: true,
      });
      return;
    }

    if (!sessionId) {
      this.fetchAiAdviceDirectly();
      return;
    }

    this.setData({ aiAdvicePending: true, aiAdviceFailed: false, aiAdvice: '', showAiAdvice: true });
    this.fetchAiAdviceDirectly();
    this.startAiAdvicePoll(sessionId);
  },

  buildAiAdvicePayload() {
    const data = this.data.resultData || {};
    const exercise = data.exercise_key || 'squat';
    const errors = [];
    const feedbacks = [];

    const pushUnique = (arr, value) => {
      const text = String(value || '').trim();
      if (text && !arr.includes(text)) arr.push(text);
    };

    (data.issues || []).forEach((item) => {
      pushUnique(errors, typeof item === 'string' ? item : (item.title || item.issue));
    });
    (data.suggestions || []).forEach((item) => {
      pushUnique(feedbacks, typeof item === 'string' ? item : (item.desc || item.suggestion));
    });

    (this.data.feedbackItems || []).forEach((item) => {
      pushUnique(errors, item.issue);
      pushUnique(feedbacks, item.suggestion);
    });

    if (!errors.length && !feedbacks.length) {
      pushUnique(errors, '本次训练暂无明显问题记录');
    }

    return { exercise, errors, feedbacks };
  },

  async fetchAiAdviceDirectly() {
    if (this._aiAdviceDirectStarted || this.data.aiAdvice) return;
    this._aiAdviceDirectStarted = true;

    const payload = this.buildAiAdvicePayload();
    this.setData({ aiAdvicePending: true, aiAdviceFailed: false, aiAdvice: '', showAiAdvice: true });

    try {
      const res = await ApiClient.post('/api/ai/advice', payload);
      const text = (res && res.text ? String(res.text) : '').trim();
      if (text) {
        this.clearAiAdvicePoll();
        this.applyAiAdviceText(text);
      }
    } catch (e) {
      console.warn('[Result] 直连 AI 建议失败:', e);
    }
  },

  startAiAdvicePoll(sessionId) {
    this.clearAiAdvicePoll();
    this._aiAdvicePollStartedAt = Date.now();

    const pollOnce = async () => {
      if (Date.now() - this._aiAdvicePollStartedAt > AI_ADVICE_POLL_TIMEOUT_MS) {
        this.clearAiAdvicePoll();
        if (!this.data.aiAdvice) {
          this.setData({
            aiAdvicePending: false,
            aiAdviceFailed: true,
            aiAdvice: 'AI 建议生成超时，请稍后刷新重试。',
          });
        }
        return;
      }

      try {
        const session = await ApiClient.get(`/api/sessions/${sessionId}`);
        const raw = session && session.feedback_summary;
        if (!raw) return;

        const summary = this.parseFeedbackSummary(raw);
        const text = typeof summary.ai_advice === 'string' ? summary.ai_advice.trim() : '';

        if (text) {
          this.clearAiAdvicePoll();
          this.applyAiAdviceText(text);
          return;
        }

        if (summary.ai_advice_status === 'failed') {
          this.clearAiAdvicePoll();
          this.setData({
            aiAdvice: 'AI 建议生成失败，请稍后刷新重试。',
            aiAdvicePreview: '',
            aiAdvicePending: false,
            aiAdviceFailed: true,
            showAiAdvice: true,
          });
        }
      } catch (e) {
        const msg = (e && e.message) || '';
        console.warn('[Result] AI 建议轮询失败:', msg);
        if (/401|403|404/.test(msg)) {
          this.clearAiAdvicePoll();
          this.setData({
            aiAdvicePending: false,
            aiAdviceFailed: true,
            aiAdvice: msg.includes('401')
              ? '请先登录后再查看 AI 建议'
              : '无法读取训练记录，请重新登录后重试',
          });
        }
      }
    };

    pollOnce();
    this._aiAdvicePollTimer = setInterval(pollOnce, AI_ADVICE_POLL_INTERVAL_MS);
  },

  clearAiAdvicePoll() {
    if (this._aiAdvicePollTimer) {
      clearInterval(this._aiAdvicePollTimer);
      this._aiAdvicePollTimer = null;
    }
  },

  formatAdviceText(text) {
    return String(text)
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/^#+\s*/gm, '')
      .replace(/^[-*]\s*/gm, '• ')
      .trim();
  },

  buildDimensionListFromRadar(radar) {
    return [
      { label: '动作完成度', value: radar.completion },
      { label: '稳定性', value: radar.stability },
      { label: '标准度', value: radar.standard },
      { label: '节奏控制', value: radar.tempo },
      { label: '移动速度', value: radar.speed },
    ];
  },

  buildRadarFromDimensions(dimensionList) {
    const values = dimensionList.map((item) => item.value);
    const avg = values.length
      ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
      : 80;

    return {
      completion: values[0] != null ? values[0] : avg,
      stability: values[1] != null ? values[1] : avg,
      standard: values[2] != null ? values[2] : avg,
      tempo: values[3] != null ? values[3] : avg,
      speed: values[4] != null ? values[4] : avg,
      axisLabels: dimensionList.map((item) => item.label),
    };
  },

  buildRadarSVG(radar) {
    const w = 500;
    const h = 460;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = 160;

    const labels = radar.axisLabels || ['动作完成度', '稳定性', '标准度', '节奏控制', '移动速度'];
    const values = [radar.completion, radar.stability, radar.standard, radar.tempo, radar.speed];
    const count = labels.length;
    const angleStep = 360 / count;

    const axes = labels.map((label, index) => ({
      label,
      angle: -90 + index * angleStep,
      value: values[index] != null ? values[index] : 0,
    }));

    const layers = [0.2, 0.4, 0.6, 0.8, 1.0].map((scale) => {
      const pts = axes.map((axis) => {
        const r = maxR * scale;
        const rad = (axis.angle * Math.PI) / 180;
        return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
      }).join(' ');
      return `<polygon points="${pts}" fill="none" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    const axisLines = axes.map((axis) => {
      const rad = (axis.angle * Math.PI) / 180;
      return `<line x1="${cx}" y1="${cy}" x2="${(cx + maxR * Math.cos(rad)).toFixed(1)}" y2="${(cy + maxR * Math.sin(rad)).toFixed(1)}" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    const dataPts = axes.map((axis) => {
      const r = (axis.value / 100) * maxR;
      const rad = (axis.angle * Math.PI) / 180;
      return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
    }).join(' ');

    const dataDots = axes.map((axis) => {
      const r = (axis.value / 100) * maxR;
      const rad = (axis.angle * Math.PI) / 180;
      return `<circle cx="${(cx + r * Math.cos(rad)).toFixed(1)}" cy="${(cy + r * Math.sin(rad)).toFixed(1)}" r="5" fill="#4f8cff" stroke="#fff" stroke-width="2" />`;
    }).join('');

    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="100%" height="100%">
      ${layers}
      ${axisLines}
      <polygon points="${dataPts}" fill="rgba(79,140,255,0.18)" stroke="#4f8cff" stroke-width="2" stroke-linejoin="round" />
      ${dataDots}
    </svg>`;
  },

  buildRadarData(score, data) {
    const base = score || 80;
    const accuracy = data.total_count > 0 ? (data.valid_count / data.total_count) * 100 : base;
    return {
      completion: Math.round(accuracy || base),
      stability: Math.round(Math.max(40, Math.min(100, base))),
      standard: Math.round(Math.max(40, Math.min(100, base))),
      tempo: Math.round(Math.max(40, Math.min(100, base))),
      speed: Math.round(Math.max(40, Math.min(100, base))),
      axisLabels: ['动作完成度', '稳定性', '标准度', '节奏控制', '移动速度'],
    };
  },

  getStarList(label) {
    const map = { '优秀': 5, '良好': 4, '一般': 3, '需改进': 2, '合格': 3 };
    const n = map[label] || 3;
    return Array.from({ length: n }, (_, i) => i + 1);
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  buildScoreVisual(score) {
    const level = getScoreLevel(Math.round(Number(score) || 0));
    return {
      scorePercent: Math.min(100, Math.max(0, Math.round(Number(score) || 0))),
      scoreColor: level.color,
    };
  },

  buildAiAdvicePreview(text) {
    const normalized = String(text || '').replace(/\s+/g, ' ').trim();
    if (!normalized) return '';
    if (normalized.length <= 72) return normalized;
    return `${normalized.slice(0, 72)}…`;
  },

  applyAiAdviceText(text) {
    const formatted = this.formatAdviceText(text);
    this.setData({
      aiAdvice: formatted,
      aiAdvicePreview: this.buildAiAdvicePreview(formatted),
      aiAdvicePending: false,
      aiAdviceFailed: false,
      showAiAdvice: false,
    });
  },

  toggleAiAdvice() {
    this.setData({ showAiAdvice: !this.data.showAiAdvice });
  },

  toggleDimensionDetail() {
    this.setData({ showDimensionDetail: !this.data.showDimensionDetail });
  },

  goTrainAgain() {
    const exerciseKey = (this.data.resultData && this.data.resultData.exercise_key)
      || (this.data.exerciseConfig && this.data.exerciseConfig.key)
      || 'squat';
    wx.redirectTo({
      url: `/pages/training/training?exercise=${exerciseKey}`,
    });
  },

  onShareTap() {
    if (this.data.sharePosterLoading) return;

    this.setData({ sharePosterLoading: true });
    wx.showLoading({ title: '生成分享卡片...', mask: true });
    this.generateSharePoster((url) => {
      wx.hideLoading();
      if (url) {
        this.setData({
          showSharePreview: true,
          sharePosterUrl: url,
          sharePosterLoading: false,
        });
      } else {
        this.setData({ sharePosterLoading: false });
        wx.showToast({ title: '卡片生成失败，请重试', icon: 'none' });
      }
    });
  },

  closeSharePreview() {
    this.setData({ showSharePreview: false });
  },

  saveSharePoster() {
    const filePath = this.data.sharePosterUrl || this._shareImagePath;
    if (!filePath) return;

    wx.saveImageToPhotosAlbum({
      filePath,
      success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
      fail: () => {
        wx.showModal({
          title: '保存失败',
          content: '请在设置中允许保存到相册后重试',
          showCancel: false,
        });
      },
    });
  },

  onShareAppMessage() {
    const exerciseName = this.data.exerciseName || '训练';
    const score = this.data.averageScore || 0;
    const meta = this.getShareScoreMeta(score);
    const payload = {
      title: `${meta.emoji} ${exerciseName} ${score}分 · ${meta.mood}，一起来运动吧！`,
      path: '/pages/dashboard/dashboard',
    };
    if (this._shareImagePath) {
      payload.imageUrl = this._shareImagePath;
    }
    return payload;
  },

  getShareScoreMeta(score) {
    const value = Math.round(Number(score) || 0);
    if (value >= 90) {
      return { emoji: '🏆', mood: '表现卓越', band: '90-100分', label: '优秀', color: '#22c55e', bg: '#ecfdf3' };
    }
    if (value >= 75) {
      return { emoji: '🔥', mood: '状态火热', band: '75-89分', label: '良好', color: '#3b82f6', bg: '#eff6ff' };
    }
    if (value >= 60) {
      return { emoji: '💪', mood: '继续加油', band: '60-74分', label: '一般', color: '#f59e0b', bg: '#fffbeb' };
    }
    return { emoji: '🎯', mood: '潜力无限', band: '0-59分', label: '需改进', color: '#ef4444', bg: '#fef2f2' };
  },

  scheduleSharePoster() {
    if (this._sharePosterTimer) {
      clearTimeout(this._sharePosterTimer);
    }
    this._sharePosterTimer = setTimeout(() => {
      this.generateSharePoster();
    }, 600);
  },

  generateSharePoster(done) {
    const width = 500;
    const height = 560;
    const score = Math.round(this.data.averageScore || 0);
    const percent = Math.min(100, Math.max(0, this.data.scorePercent || score));
    const meta = this.getShareScoreMeta(score);
    const ringColor = meta.color;
    const exerciseName = this.data.exerciseName || '训练';
    const grade = this.data.gradeLabel || this.data.levelLabel || meta.label;
    const validRate = this.data.validRate != null ? this.data.validRate : 0;
    const totalCount = this.data.totalCount || 0;
    const validCount = this.data.validCount || 0;
    const durationText = this.data.durationText || '0:00';
    const finishedAt = (this.data.finishedAt || '').split(' ')[0] || '';

    const ctx = wx.createCanvasContext('sharePoster', this);

    ctx.setFillStyle(meta.bg);
    ctx.fillRect(0, 0, width, height);

    ctx.setFillStyle(ringColor);
    ctx.fillRect(0, 0, width, 120);

    ctx.setFillStyle('rgba(255,255,255,0.18)');
    ctx.beginPath();
    ctx.arc(width - 40, 20, 70, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(30, 100, 50, 0, 2 * Math.PI);
    ctx.fill();

    this._fillRoundRect(ctx, 24, 28, width - 48, height - 56, 20, '#ffffff');

    ctx.setFillStyle('#64748b');
    ctx.setFontSize(13);
    ctx.setTextAlign('left');
    ctx.fillText('运动姿态评估', 44, 58);
    if (finishedAt) {
      ctx.setTextAlign('right');
      ctx.fillText(finishedAt, width - 44, 58);
    }

    ctx.setTextAlign('center');
    ctx.setFontSize(46);
    ctx.fillText(meta.emoji, width / 2, 108);

    this._fillRoundRect(ctx, width / 2 - 68, 124, 136, 30, 15, meta.bg);
    ctx.setFillStyle(ringColor);
    ctx.setFontSize(16);
    ctx.fillText(exerciseName, width / 2, 145);

    const cx = width / 2;
    const cy = 228;
    const radius = 52;

    ctx.setLineWidth(10);
    ctx.setStrokeStyle('#eef2f7');
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
    ctx.stroke();

    ctx.setStrokeStyle(ringColor);
    ctx.setLineCap('round');
    ctx.beginPath();
    ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + (2 * Math.PI * percent) / 100);
    ctx.stroke();

    ctx.setFillStyle('#0f172a');
    ctx.setFontSize(40);
    ctx.fillText(String(score), cx - 6, cy + 12);
    ctx.setFontSize(14);
    ctx.setFillStyle('#94a3b8');
    ctx.fillText('分', cx + 30, cy + 4);

    this._fillRoundRect(ctx, cx - 42, cy + radius + 14, 84, 26, 13, ringColor);
    ctx.setFillStyle('#ffffff');
    ctx.setFontSize(15);
    ctx.fillText(grade, cx, cy + radius + 33);

    ctx.setFillStyle(ringColor);
    ctx.setFontSize(17);
    ctx.fillText(meta.mood, cx, cy + radius + 62);
    ctx.setFillStyle('#64748b');
    ctx.setFontSize(13);
    ctx.fillText(`${meta.band} · ${meta.label}`, cx, cy + radius + 84);

    const stats = [
      { label: '总次数', value: String(totalCount) },
      { label: '有效', value: String(validCount) },
      { label: '正确率', value: `${validRate}%` },
      { label: '时长', value: durationText },
    ];
    const boxW = 98;
    const boxH = 54;
    const gap = 8;
    const startX = (width - boxW * 4 - gap * 3) / 2;
    const boxY = 356;

    stats.forEach((item, index) => {
      const x = startX + index * (boxW + gap);
      this._fillRoundRect(ctx, x, boxY, boxW, boxH, 10, '#f8fafc');
      ctx.setFillStyle('#0f172a');
      ctx.setFontSize(18);
      ctx.setTextAlign('center');
      ctx.fillText(item.value, x + boxW / 2, boxY + 28);
      ctx.setFillStyle('#94a3b8');
      ctx.setFontSize(11);
      ctx.fillText(item.label, x + boxW / 2, boxY + 46);
    });

    ctx.setFillStyle('#cbd5e1');
    ctx.fillRect(44, 428, width - 88, 1);

    ctx.setFillStyle('#475569');
    ctx.setFontSize(14);
    ctx.fillText('扫码进入小程序，一起来挑战！', width / 2, 456);

    ctx.setFillStyle(ringColor);
    ctx.setFontSize(12);
    ctx.fillText('AI 姿态评估 · 科学训练', width / 2, height - 36);

    ctx.draw(false, () => {
      setTimeout(() => {
        wx.canvasToTempFilePath({
          canvasId: 'sharePoster',
          x: 0,
          y: 0,
          width,
          height,
          destWidth: width * 2,
          destHeight: height * 2,
          fileType: 'png',
          success: (res) => {
            this._shareImagePath = res.tempFilePath;
            if (typeof done === 'function') done(res.tempFilePath);
          },
          fail: (err) => {
            console.warn('[Share] 生成分享卡片失败:', err);
            if (typeof done === 'function') done('');
          },
        }, this);
      }, 500);
    });
  },

  _fillRoundRect(ctx, x, y, w, h, r, fillStyle) {
    ctx.setFillStyle(fillStyle);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.arc(x + w - r, y + r, r, -Math.PI / 2, 0);
    ctx.lineTo(x + w, y + h - r);
    ctx.arc(x + w - r, y + h - r, r, 0, Math.PI / 2);
    ctx.lineTo(x + r, y + h);
    ctx.arc(x + r, y + h - r, r, Math.PI / 2, Math.PI);
    ctx.lineTo(x, y + r);
    ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
    ctx.closePath();
    ctx.fill();
  },

  prepareReplayFramesForUpload(frames) {
    if (!Array.isArray(frames) || frames.length === 0) return [];

    const maxFrames = 12000;
    const step = Math.max(1, Math.ceil(frames.length / maxFrames));
    return frames
      .filter((_, index) => index % step === 0)
      .slice(0, maxFrames)
      .map((frame, index) => ({
        timestamp_ms: Number(frame.timestamp_ms != null ? frame.timestamp_ms : index * 140) || 0,
        landmarks: Array.isArray(frame.landmarks)
          ? frame.landmarks.slice(0, 33).map((point) => ({
              x: Number((Number(point && point.x) || 0).toFixed(4)),
              y: Number((Number(point && point.y) || 0).toFixed(4)),
              z: Number((Number(point && point.z) || 0).toFixed(4)),
              visibility: Number((point && point.visibility != null ? Number(point.visibility) : 1).toFixed(3)),
            }))
          : [],
      }))
      .filter((frame) => frame.landmarks.length >= 33);
  },
});
