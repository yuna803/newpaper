import request from '../utils/request'

export function getCategories() {
  return request.get('/api/admin/categories')
}

export function createCategory(data) {
  return request.post('/api/admin/categories', data)
}

export function updateCategory(id, data) {
  return request.put(`/api/admin/categories/${id}`, data)
}

export function deleteCategory(id) {
  return request.delete(`/api/admin/categories/${id}`)
}
