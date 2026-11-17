const baseURL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/$/, '')

export type ApiError = Error & { status: number; details?: unknown }

export class ApiClient {
  private token: string | null
  private readonly baseUrl: string

  constructor(baseUrl = baseURL) {
    this.baseUrl = baseUrl
    this.token = window.localStorage.getItem('aurora-api-token')
  }

  setToken(token: string | null) {
    this.token = token
    if (token) window.localStorage.setItem('aurora-api-token', token)
    else window.localStorage.removeItem('aurora-api-token')
  }

  getToken() {
    return this.token
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers)
    if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json')
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`)

    let response: Response
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers })
    } catch {
      throw Object.assign(new Error('The AURORA X API is unavailable. The demo catalogue remains available.'), {
        status: 0,
      }) as ApiError
    }

    if (!response.ok) {
      let details: unknown
      try {
        details = await response.json()
      } catch {
        details = null
      }
      const message = typeof details === 'object' && details !== null && 'detail' in details
        ? String((details as { detail: unknown }).detail)
        : `Request failed (${response.status})`
      throw Object.assign(new Error(message), { status: response.status, details }) as ApiError
    }

    if (response.status === 204) return undefined as T
    return response.json() as Promise<T>
  }

  register(payload: { email: string; password: string; displayName: string; role: 'buyer' | 'seller' }) {
    return this.request<unknown>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
        display_name: payload.displayName,
        role: payload.role,
      }),
    })
  }

  async login(email: string, password: string) {
    const result = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(result.access_token)
    return result
  }

  async logout() {
    await this.request<undefined>('/auth/logout', { method: 'POST' })
    this.setToken(null)
  }

  me() {
    return this.request<unknown>('/auth/me')
  }

  products() {
    return this.request<ApiProduct[]>('/products')
  }
}

export type ApiProduct = {
  id: string
  store_id: string
  store_name: string
  category: string
  name: string
  description: string
  price: number
  image_url: string
  quantity: number
  is_active: boolean
}

export const api = new ApiClient()
