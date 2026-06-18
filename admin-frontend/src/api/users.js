import request from '../utils/request'

export function getUsers(params) {
  return request.get('/api/admin/users', { params })
}

export function updateUser(id, data) {
  return request.put(`/api/admin/users/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/api/admin/users/${id}`)
}
