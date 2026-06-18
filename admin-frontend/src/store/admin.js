import { defineStore } from 'pinia'
import { login as loginApi } from '../api/auth'

const STORAGE_KEY = 'admin-store'

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return null
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    token: state.token,
    adminInfo: state.adminInfo,
    isLogin: state.isLogin,
  }))
}

export const useAdminStore = defineStore('admin', {
  state: () => {
    const saved = loadState()
    return {
      token: saved?.token || '',
      adminInfo: saved?.adminInfo || null,
      isLogin: saved?.isLogin || false,
    }
  },

  actions: {
    async login(username, password) {
      const res = await loginApi(username, password)
      if (res.data.userInfo.role !== 'admin') {
        throw new Error('无管理员权限')
      }
      this.token = res.data.token
      this.adminInfo = res.data.userInfo
      this.isLogin = true
      saveState(this.$state)
    },

    logout() {
      this.token = ''
      this.adminInfo = null
      this.isLogin = false
      localStorage.removeItem(STORAGE_KEY)
    },
  },
})
