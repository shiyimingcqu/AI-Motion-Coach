// HTTP 请求封装 + JWT 拦截
const { API_BASE_URL } = require('./constants');
const Storage = require('./storage');

class ApiClient {
  /**
   * 通用请求方法
   */
  static request(options) {
    const token = Storage.get(Storage.KEYS.TOKEN);

    return new Promise((resolve, reject) => {
      wx.request({
        url: API_BASE_URL + options.url,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': options.isForm ? 'application/x-www-form-urlencoded' : 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.header
        },
        success(res) {
          if (res.statusCode === 401) {
            // token 过期，跳转登录
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
            const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
            reject(new Error(`HTTP ${res.statusCode}: ${message}`));
          }
        },
        fail(err) {
          reject(new Error('网络请求失败: ' + (err.errMsg || '未知错误')));
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

  static post(url, data = {}) {
    return this.request({ url, method: 'POST', data });
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

    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: API_BASE_URL + url,
        filePath: filePath,
        name: 'file',
        formData: formData,
        header: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        success(res) {
          if (res.statusCode === 401) {
            Storage.remove(Storage.KEYS.TOKEN);
            wx.reLaunch({ url: '/pages/login/login' });
            reject(new Error('登录已过期'));
            return;
          }
          try {
            resolve(JSON.parse(res.data));
          } catch (e) {
            resolve(res.data);
          }
        },
        fail(err) {
          reject(new Error('上传失败: ' + (err.errMsg || '未知错误')));
        }
      });
    });
  }
}

module.exports = ApiClient;
