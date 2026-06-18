import request from '../utils/request'

export function getNewsList(params) {
  return request.get('/api/admin/news', { params })
}

export function getNewsDetail(id) {
  return request.get(`/api/admin/news/${id}`)
}

export function createNews(data) {
  return request.post('/api/admin/news', data)
}

export function updateNews(id, data) {
  return request.put(`/api/admin/news/${id}`, data)
}

export function deleteNews(id) {
  return request.delete(`/api/admin/news/${id}`)
}

export function importNews(items) {
  return request.post('/api/admin/news/import', items)
}

export function approveNews(id) {
  return request.put(`/api/admin/news/${id}/approve`)
}

export function rejectNews(id) {
  return request.delete(`/api/admin/news/${id}/reject`)
}

export function scrapeNews(params) {
  return request.post('/api/admin/news/scrape', null, { params })
}

export function batchApproveNews(ids) {
  return request.post('/api/admin/news/batch-approve', ids)
}

export function batchRejectNews(ids) {
  return request.post('/api/admin/news/batch-reject', ids)
}
