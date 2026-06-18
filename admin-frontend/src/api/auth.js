import request from '../utils/request'

export function login(username, password) {
  return request.post('/api/user/login', { username, password })
}
