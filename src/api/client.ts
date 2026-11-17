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
      if (response.status === 401) this.setToken(null)
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

  cart() {
    return this.request<unknown>('/cart')
  }

  addCartItem(productId: string, quantity = 1) {
    return this.request<unknown>('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
    })
  }

  updateCartItem(itemId: string, quantity: number) {
    return this.request<unknown>(`/cart/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    })
  }

  removeCartItem(itemId: string) {
    return this.request<unknown>(`/cart/items/${itemId}`, { method: 'DELETE' })
  }

  clearCart() {
    return this.request<unknown>('/cart', { method: 'DELETE' })
  }

  checkout(payload: {
    idempotencyKey: string
    discountCode?: string
    address: {
      recipientName: string
      phone: string
      line1: string
      line2?: string
      city: string
      state: string
      postalCode: string
      country?: string
    }
  }) {
    return this.request<unknown>('/checkout', {
      method: 'POST',
      body: JSON.stringify({
        idempotency_key: payload.idempotencyKey,
        discount_code: payload.discountCode,
        address: {
          recipient_name: payload.address.recipientName,
          phone: payload.address.phone,
          line1: payload.address.line1,
          line2: payload.address.line2 ?? '',
          city: payload.address.city,
          state: payload.address.state,
          postal_code: payload.address.postalCode,
          country: payload.address.country ?? 'India',
        },
      }),
    })
  }

  orders() {
    return this.request<unknown[]>('/orders')
  }

  order(orderId: string) {
    return this.request<unknown>(`/orders/${orderId}`)
  }

  cancelOrder(orderId: string) {
    return this.request<unknown>(`/orders/${orderId}/cancel`, { method: 'POST' })
  }

  sellerOrders() {
    return this.request<unknown[]>('/seller/orders')
  }

  updateSellerOrder(sellerOrderId: string, status: string) {
    return this.request<unknown>(`/seller/orders/${sellerOrderId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  }

  adjustInventory(productId: string, quantityDelta: number, reason: string) {
    return this.request<unknown>(`/seller/products/${productId}/inventory`, {
      method: 'POST',
      body: JSON.stringify({ quantity_delta: quantityDelta, reason }),
    })
  }

  aiSearch(query: string, limit = 20) {
    return this.request<{
      mode: string
      intent: Record<string, unknown>
      results: ApiSearchResult[]
      alternatives: ApiSearchResult[]
    }>('/ai/search', {
      method: 'POST',
      body: JSON.stringify({ q: query, limit, session_key: 'web' }),
    })
  }

  aiCopilot(message: string) {
    return this.request<{
      mode: string
      message: string
      intent: Record<string, unknown>
      products: ApiSearchResult[]
      purchase_executed: boolean
    }>('/ai/copilot', {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  }

  aiCompare(productIds: string[]) {
    return this.request<unknown>('/ai/compare', {
      method: 'POST',
      body: JSON.stringify({ product_ids: productIds }),
    })
  }

  aiSellerTool(payload: {
    tool: 'title' | 'description' | 'keywords' | 'category' | 'pricing' | 'campaign' | 'attributes'
    productName: string
    category?: string
    description?: string
    price?: string
  }) {
    return this.request<unknown>('/ai/seller/tool', {
      method: 'POST',
      body: JSON.stringify({
        tool: payload.tool,
        product_name: payload.productName,
        category: payload.category ?? '',
        description: payload.description ?? '',
        price: payload.price ?? '',
      }),
    })
  }

  personalization(enabled: boolean, preferredCategories: string[] = []) {
    return this.request<unknown>('/ai/personalization', {
      method: 'POST',
      body: JSON.stringify({ enabled, preferred_categories: preferredCategories }),
    })
  }

  recommendations() {
    return this.request<unknown>('/ai/recommendations')
  }

  trustShield() {
    return this.request<unknown>('/ai/trustshield')
  }

  conversations() {
    return this.request<unknown[]>('/conversations')
  }

  createConversation(sellerId: string, orderId?: string, productId?: string) {
    return this.request<unknown>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ seller_id: sellerId, order_id: orderId, product_id: productId }),
    })
  }

  conversationMessages(conversationId: string) {
    return this.request<unknown[]>(`/conversations/${conversationId}/messages`)
  }

  sendConversationMessage(conversationId: string, text: string, clientMessageId: string) {
    return this.request<unknown>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ text, client_message_id: clientMessageId, original_language: 'en' }),
    })
  }

  translate(text: string, targetLanguage: string) {
    return this.request<unknown>('/translation', {
      method: 'POST',
      body: JSON.stringify({ text, source_language: 'auto', target_language: targetLanguage }),
    })
  }

  notifications() {
    return this.request<unknown[]>('/notifications')
  }

  markNotificationRead(notificationId: string) {
    return this.request<unknown>(`/notifications/${notificationId}/read`, { method: 'POST' })
  }

  markAllNotificationsRead() {
    return this.request<unknown>('/notifications/read', { method: 'POST' })
  }

  supportTickets() {
    return this.request<unknown[]>('/support/tickets')
  }

  createSupportTicket(payload: { subject: string; category: string; description: string; priority?: string; orderId?: string }) {
    return this.request<unknown>('/support/tickets', {
      method: 'POST',
      body: JSON.stringify({
        subject: payload.subject,
        category: payload.category,
        description: payload.description,
        priority: payload.priority ?? 'NORMAL',
        order_id: payload.orderId,
      }),
    })
  }

  ticketMessages(ticketId: string) {
    return this.request<unknown[]>(`/support/tickets/${ticketId}/messages`)
  }

  sendTicketReply(ticketId: string, text: string, internal = false) {
    return this.request<unknown>(`/support/tickets/${ticketId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ text, internal }),
    })
  }

  disputes() {
    return this.request<unknown[]>('/disputes')
  }

  platformAnalytics(fromDate?: string, toDate?: string, page = 1, pageSize = 20) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (fromDate) params.set('from_date', fromDate)
    if (toDate) params.set('to_date', toDate)
    return this.request<unknown>(`/admin/analytics?${params}`)
  }

  sellerAnalytics() {
    return this.request<unknown>('/seller/analytics')
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

export type ApiSearchResult = {
  id: string
  name: string
  category: string
  price: string
  description: string
  image_url: string
  quantity: number
  store_name: string
  score: number
  explanation: string[]
  alternative_ids: string[]
}

export const api = new ApiClient()
