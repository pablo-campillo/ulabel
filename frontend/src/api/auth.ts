import { request } from './client'
import type { User } from '../types/api'

export function login(username: string): Promise<User> {
  return request<User>('/token', {
    method: 'POST',
    body: JSON.stringify({ username }),
  })
}
