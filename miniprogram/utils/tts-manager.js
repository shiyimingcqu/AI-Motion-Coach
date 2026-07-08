// TTS 语音播报管理器
// 基于后端 edge-tts 接口，实现实时语音播报
// 支持：队列播报、打断播报、去重节流、静音开关、预缓存

const { API_BASE_URL } = require('./constants')

// 表扬话术池（高评分完成动作时随机选择）
const PRAISE_POOL = [
  '完美！动作标准',
  '太棒了！继续保持',
  '优秀！姿态准确',
  '漂亮！就是这样',
  '很好！动作规范',
]

// 鼓励话术池（低评分完成动作时随机选择）
const ENCOURAGE_POOL = [
  '再试一次，注意调整姿势',
  '没关系，继续加油',
  '调整呼吸，再来一次',
]

// 预缓存短语（首次合成后缓存音频URL，减少延迟）
const PRECACHE_PHRASES = [
  ...PRAISE_POOL,
  ...ENCOURAGE_POOL,
  '注意保持',
  '开始训练',
  '训练结束',
]

// 去重节流间隔（毫秒）
const DEDUP_INTERVAL = 5000

// 同一 issue 的冷却间隔（毫秒）— 避免重复播报同一个问题
const ISSUE_COOLDOWN = 15000

// 同一 issue 在一次训练中最多播报次数
const ISSUE_MAX_REPEAT = 3

class TTSManager {
  constructor() {
    this._audioContext = null
    this._queue = []
    this._isPlaying = false
    this._isFetching = false
    this._enabled = true
    this._lastSpokenText = ''
    this._lastSpokenTime = 0
    this._cache = new Map() // text -> audioUrl(API url)
    this._precaching = false
    // issue 播报控制
    this._issueCooldowns = new Map() // issueText -> lastSpokenTimestamp
    this._issueRepeatCounts = new Map() // issueText -> repeat count this session
  }

  /**
   * 启用/禁用语音
   */
  setEnabled(enabled) {
    this._enabled = !!enabled
    if (!this._enabled) {
      this.stop()
    }
  }

  isEnabled() {
    return this._enabled
  }

  /**
   * 队列播报（不打断当前播报，按顺序排）
   * 适用于：错误纠正反馈
   */
  speak(text) {
    if (!this._enabled || !text) return
    text = String(text).trim()
    if (!text) return

    // 去重节流
    if (this._shouldDedup(text)) return

    this._queue.push(text)
    if (!this._isPlaying && !this._isFetching) {
      this._processQueue()
    }
  }

  /**
   * 立即播报（打断当前播报，清空队列）
   * 适用于：表扬夸赞
   */
  speakImmediately(text) {
    if (!this._enabled || !text) return
    text = String(text).trim()
    if (!text) return

    // 停止当前播放
    this.stop()

    // 清空队列，只播报这条
    this._queue = [text]
    this._processQueue()
  }

  /**
   * 播报表扬话术（随机选择一条）
   */
  speakPraise() {
    const text = PRAISE_POOL[Math.floor(Math.random() * PRAISE_POOL.length)]
    this.speakImmediately(text)
  }

  /**
   * 播报鼓励话术（随机选择一条）
   */
  speakEncourage() {
    const text = ENCOURAGE_POOL[Math.floor(Math.random() * ENCOURAGE_POOL.length)]
    this.speakImmediately(text)
  }

  /**
   * 播报错误纠正（带冷却和次数限制）
   * 同一 issue 在 ISSUE_COOLDOWN 内不重复播报
   * 同一 issue 在一次训练中最多播报 ISSUE_MAX_REPEAT 次
   * @param {string} issueText - 错误描述
   * @param {string} [feedbackText] - 对应的纠正建议（可选，交替播报）
   */
  speakIssue(issueText, feedbackText) {
    if (!this._enabled || !issueText) return
    issueText = String(issueText).trim()
    if (!issueText) return

    const now = Date.now()

    // 检查播报次数
    const repeatCount = this._issueRepeatCounts.get(issueText) || 0
    if (repeatCount >= ISSUE_MAX_REPEAT) return

    // 检查冷却
    const lastTime = this._issueCooldowns.get(issueText) || 0
    if (now - lastTime < ISSUE_COOLDOWN) return

    // 更新记录
    this._issueCooldowns.set(issueText, now)
    this._issueRepeatCounts.set(issueText, repeatCount + 1)

    // 交替播报 issue 和 feedback：第一次播 issue，之后播 feedback（更具体）
    let text
    if (repeatCount === 0 && feedbackText) {
      // 第一次：播报完整反馈建议
      text = feedbackText
    } else if (feedbackText && repeatCount % 2 === 1) {
      // 奇数次：播报纠正建议
      text = feedbackText
    } else {
      // 偶数次：播报问题名称
      text = issueText
    }
    this.speak(text)
  }

  /**
   * 重置 issue 追踪（训练开始时调用）
   */
  resetIssueTracking() {
    this._issueCooldowns.clear()
    this._issueRepeatCounts.clear()
  }

  /**
   * 停止当前播报
   */
  stop() {
    if (this._audioContext) {
      try {
        this._audioContext.stop()
        this._audioContext.destroy()
      } catch (e) {}
      this._audioContext = null
    }
    this._isPlaying = false
    this._isFetching = false
  }

  /**
   * 销毁管理器，释放资源
   */
  destroy() {
    this.stop()
    this._queue = []
    this._cache.clear()
    this._issueCooldowns.clear()
    this._issueRepeatCounts.clear()
  }

  /**
   * 预缓存高频短语
   * 在训练开始前调用，提前标记为已缓存（实际音频按需获取）
   */
  precache() {
    if (this._precaching) return
    this._precaching = true

    // 后端已有缓存，这里只做标记，不预拉取音频
    // 实际播放时自动缓存 URL
    const phrases = [...new Set(PRECACHE_PHRASES)]
    phrases.forEach((text) => {
      if (!this._cache.has(text)) {
        this._cache.set(text, this._buildTTSUrl(text))
      }
    })
    this._precaching = false
  }

  // ========== 内部方法 ==========

  /**
   * 构建后端 TTS 接口 URL
   */
  _buildTTSUrl(text) {
    const encoded = encodeURIComponent(text.slice(0, 100))
    return `${API_BASE_URL}/api/tts?text=${encoded}`
  }

  /**
   * 去重判断：相同内容 3 秒内不重复
   */
  _shouldDedup(text) {
    const now = Date.now()
    if (text === this._lastSpokenText && now - this._lastSpokenTime < DEDUP_INTERVAL) {
      return true
    }
    this._lastSpokenText = text
    this._lastSpokenTime = now
    return false
  }

  /**
   * 处理消息队列
   */
  _processQueue() {
    if (this._queue.length === 0) {
      this._isPlaying = false
      return
    }

    const text = this._queue.shift()

    // 获取音频 URL（有缓存直接用，无缓存构建）
    const url = this._cache.has(text) ? this._cache.get(text) : this._buildTTSUrl(text)
    if (!this._cache.has(text)) {
      this._cache.set(text, url)
    }

    this._playAudio(url, text)
  }

  /**
   * 播放音频
   */
  _playAudio(audioUrl, text) {
    this._isPlaying = true

    // 销毁旧的 audioContext
    if (this._audioContext) {
      try {
        this._audioContext.destroy()
      } catch (e) {}
    }

    const ctx = wx.createInnerAudioContext({
      useWebAudioImplement: true,
    })
    ctx.src = audioUrl
    this._audioContext = ctx

    ctx.onEnded(() => {
      this._isPlaying = false
      try {
        ctx.destroy()
      } catch (e) {}
      this._audioContext = null
      // 处理队列中的下一条
      this._processQueue()
    })

    ctx.onError((err) => {
      console.warn('[TTS] 播放错误:', err)
      this._isPlaying = false
      try {
        ctx.destroy()
      } catch (e) {}
      this._audioContext = null
      this._processQueue()
    })

    ctx.play()
  }
}

module.exports = TTSManager
