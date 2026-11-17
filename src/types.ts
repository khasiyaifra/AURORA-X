export type Category =
  | 'Electronics'
  | 'Fashion'
  | 'Home'
  | 'Beauty'
  | 'Sports'
  | 'Books'
  | 'Automotive'
  | 'Accessories'

export type Product = {
  id: string
  name: string
  category: Category
  price: number
  originalPrice?: number
  rating: number
  reviewCount: number
  seller: string
  sellerId: string
  delivery: string
  image: string
  badge?: string
  description: string
  stock: number
  specs: Record<string, string>
}

export type SellerStore = {
  id: string
  name: string
  category: Category
  description: string
  personality: string
  accent: string
  published: boolean
}

export type CartLine = { productId: string; quantity: number }

export type Page =
  | 'home'
  | 'explore'
  | 'categories'
  | 'assistant'
  | 'compare'
  | 'cart'
  | 'wishlist'
  | 'seller'
  | 'creator'
  | 'store'
  | 'support'
  | 'account'
  | 'orders'
  | 'confirmation'