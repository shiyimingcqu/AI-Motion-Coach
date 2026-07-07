// HTTP 请求封装 + JWT 拦截
const { getApiBaseUrl } = require('./constants');
const Storage = require('./storage');

function formatApiDetail(detail, fallback = '请求失败') {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (!item) return '';
      if (typeof item === 'string') return item;
      return item.msg || item.message || JSON.stringify(item);
    }).filter(Boolean).join('；') || fallback;
  }
  if (typeof detail === 'object') {
    return detail.message || detail.msg || JSON.stringify(detail);
  }
  return String(detail);
}

class ApiClient {
  /**
   * 通用请求方法
   */
  static request(options) {
    const token = Storage.get(Storage.KEYS.TOKEN);
    const baseUrl = getApiBaseUrl();

    return new Promise((resolve, reject) => {
      wx.request({
        url: baseUrl + options.url,
        method: options.method || 'GET',
        data: options.data || {},
        timeout: options.timeout || 120000,
        header: {
          'Content-Type': options.isForm ? 'application/x-www-form-urlencoded' : 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.header
        },
        success(res) {
          if (res.statusCode === 401) {
            Storage.remove(Storage.KEYS.TOKEN);
            Storage.remove(Storage.KEYS.USER_INFO);
            wx.reLaunch({ url: '/pages/login/login' });
            reject(new Error('登录已过期，请重新登录'));
            return;
          }
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            const detail = res.data && res.data.detail ? res.data.detail : '请求失败';
            reject(new Error(`HTTP ${res.statusCode}: ${formatApiDetail(detail)}`));
          }
        },
        fail(err) {
          reject(new Error('网络请求失败: ' + (err.errMsg || '未知错误') + ` @ ${baseUrl}`));
        }
      });
    });
  }

  static get(url, params = {}) {
    const query = Object.keys(params)
      .filter(k => params[k] !== undefined && params[k] !== null)
      .map(k => `${k}=${encodeURIComponent(params[k])}`)
      .join('&');
    const fullUrl = query ? `${url}?${query}` : url;
    return this.request({ url: fullUrl, method: 'GET' });
  }

  static post(url, data = {}, options = {}) {
    return this.request({ url, method: 'POST', data, ...options });
  }

  static postForm(url, data = {}) {
    return this.request({ url, method: 'POST', data, isForm: true });
  }

  static put(url, data = {}) {
    return this.request({ url, method: 'PUT', data });
  }

  static delete(url) {
    return this.request({ url, method: 'DELETE' });
  }

  /**
   * 上传文件
   */
  static upload(url, filePath, formData = {}) {
    const token = Storage.get(Storage.KEYS.TOKEN);
    const baseUrl = getApiBaseUrl();

    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: baseUrl + url,
        filePath: filePath,
        name: 'file',
        formData: formData,
        timeout: 300000,
        header: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        success(res) {
          if (res.statusCode === 401) {
            Storage.remove(Storage.KEYS.TOKEN);
            Storage.remove(Storage.KEYS.USER_INFO);
            wx.reLaunch({ url: '/pages/login/login' });
            reject(new Error('登录已过期，请先登录'));
            return;
          }
          if (res.statusCode < 200 || res.statusCode >= 300) {
            let detail = '上传失败';
            try {
              const parsed = JSON.parse(res.data || '{}');
              detail = formatApiDetail(parsed.detail || parsed.message, detail);
            } catch (e) {
              detail = res.data || detail;
            }
            reject(new Error(`HTTP ${res.statusCode}: ${detail}`));
            return;
          }
          try {
            resolve(JSON.parse(res.data));
          } catch (e) {
            resolve(res.data);
          }
        },
        fail(err) {
          reject(new Error('上传失败: ' + (err.errMsg || '未知错误') + ` @ ${baseUrl}`));
        }
      });
    });
  }
}

module.exports = ApiClient;
