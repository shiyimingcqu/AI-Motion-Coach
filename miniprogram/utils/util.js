// 通用工具函数

/**
 * 格式化日期
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '';
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * 格式化时长（秒 → X分X秒）
 */
function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0秒';
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  if (min === 0) return `${sec}秒`;
  if (sec === 0) return `${min}分钟`;
  return `${min}分${sec}秒`;
}

/**
 * 防抖
 */
function debounce(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

/**
 * 节流
 */
function throttle(fn, interval = 300) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

/**
 * 显示 Toast
 */
function showToast(title, icon = 'none') {
  wx.showToast({ title, icon, duration: 2000 });
}

/**
 * 显示加载中
 */
function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true });
}

function hideLoading() {
  wx.hideLoading();
}

/**
 * 确认弹窗
 */
function showConfirm(title, content) {
  return new Promise((resolve) => {
    wx.showModal({
      title,
      content,
      success(res) {
        resolve(res.confirm);
      }
    });
  });
}

/**
 * 获取当前日期范围（本周）
 */
function getWeekRange() {
  const now = new Date();
  const dayOfWeek = now.getDay() || 7; // 周日 = 7
  const monday = new Date(now);
  monday.setDate(now.getDate() - dayOfWeek + 1);
  monday.setHours(0, 0, 0, 0);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  sunday.setHours(23, 59, 59, 999);
  return {
    from: formatDate(monday, 'YYYY-MM-DD'),
    to: formatDate(sunday, 'YYYY-MM-DD')
  };
}

/**
 * 获取当前日期范围（本月）
 */
function getMonthRange() {
  const now = new Date();
  const first = new Date(now.getFullYear(), now.getMonth(), 1);
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
  return {
    from: formatDate(first, 'YYYY-MM-DD'),
    to: formatDate(last, 'YYYY-MM-DD')
  };
}

module.exports = {
  formatDate,
  formatDuration,
  debounce,
  throttle,
  showToast,
  showLoading,
  hideLoading,
  showConfirm,
  getWeekRange,
  getMonthRange
};
