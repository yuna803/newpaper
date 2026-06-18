import axios from 'axios'
import { apiConfig } from '../config/api'

const request = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 15000,
})

request.interceptors.request.use(config => {
  // 尝试从多个来源获取 token
  let token = null
  const storeStr = localStorage.getItem('admin-store')
  if (storeStr) {
    try {
      const data = JSON.parse(storeStr)
      // 兼容多种存储格式: {token:...} / {admin:{token:...}}
      token = data.token || (data.admin && data.admin.token) || null
    } catch {}
  }
  if (token) {
    config.headers.Authorization = token
  }
  return config
})

request.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code === 200) {
      return data
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  error => {
    const status = error.response?.status
    if (status === 401 || status === 403) {
      localStorage.removeItem('admin-store')
      window.location.href = '/login'
    }
    if (status === 422) {
      console.error('请求验证失败(422):', error.response?.data)
    }
    return Promise.reject(error)
  }
)

export default request
