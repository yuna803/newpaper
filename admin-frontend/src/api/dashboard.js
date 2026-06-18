import request from '../utils/request'

export function getDashboardStats() {
  return request.get('/api/admin/dashboard')
}
