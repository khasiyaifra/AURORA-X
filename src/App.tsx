import { useEffect, useMemo, useState } from 'react'
import { ArrowUp, Check, Compass, Home, ShoppingBag, UserRound } from 'lucide-react'
import { demoProducts } from './data/products'
import type { CartLine, Page, Product, SellerStore } from './types'
import { usePersistentState } from './hooks/usePersistentState'
import { SiteHeader } from './components/SiteHeader'
import { ProductDetailDialog } from './components/ProductCard'
import { MarketplacePage } from './pages/MarketplacePage'
import type { ProductHandlers } from './pages/MarketplacePage'
import { AssistantPage } from './pages/AssistantPage'
import { CommercePage } from './pages/CommercePage'
import { SellerPage } from './pages/SellerPage'
import { SupportPage } from './pages/SupportPage'
import { api, type ApiProduct } from './api/client'
import type { Category } from './types'
import './App.css'

type DemoOrder = { id: string; date: string; total: number; items: number }

const stopWords = new Set(['i', 'need', 'want', 'looking', 'for', 'a', 'an', 'the', 'with', 'and', 'or', 'under', 'below', 'less', 'than', 'maximum', 'max', 'up', 'to', 'within', 'please', 'find', 'me', 'something', 'that', 'has', 'of', 'in', 'on', 'it', 'my', 'is', 'be', 'around', 'about', 'year', 'years'])
const searchSynonyms: Record<string, string> = { tv: 'television', trainers: 'runner', running: 'runner', shoes: 'runner', headphone: 'headphones', earbuds: 'headphones', sofa: 'chair', lamp: 'light', skincare: 'serum' }

function normalizedText(value: string) {
  return value.toLocaleLowerCase().replace(/\byears?\b/g, 'year').replace(/[^\p{L}\p{N}]+/gu, ' ').trim()
}

function App() {
  const [page, setPage] = useState<Page>('home')
  const [apiStatus, setApiStatus] = useState<'loading' | 'connected' | 'demo'>('loading')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [sort, setSort] = useState('relevance')
  const [products, setProducts] = usePersistentState<Product[]>('aurora-products', demoProducts)
  const [cart, setCart] = usePersistentState<CartLine[]>('aurora-cart', [])
  const [wishlist, setWishlist] = usePersistentState<string[]>('aurora-wishlist', [])
  const [compared, setCompared] = useState<string[]>([])
  const [recentlyViewed, setRecentlyViewed] = usePersistentState<string[]>('aurora-recent', [])
  const [store, setStore] = usePersistentState<SellerStore | null>('aurora-store', null)
  const [storeViewId, setStoreViewId] = useState('northstar')
  const [customerName, setCustomerName] = usePersistentState('aurora-customer-name', 'Aurora Guest')
  const [orders, setOrders] = usePersistentState<DemoOrder[]>('aurora-orders', [])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [confirmationId, setConfirmationId] = useState('')
  const [notice, setNotice] = useState('')
  const cartCount = cart.reduce((total, item) => total + item.quantity, 0)

  const rankedProducts = useMemo(() => {
    let budget: number | null = null
    const budgetMatch = query.match(/\b(?:under|below|less than|max(?:imum)?|up to|within)\s*(?:₹|rs\.?\s*)?([\d,]+)(\s*[kK])?/i) ?? query.match(/₹\s*([\d,]+)(\s*[kK])?/i)
    if (budgetMatch) budget = Number(budgetMatch[1].replace(/,/g, '')) * (budgetMatch[2] ? 1000 : 1)
    const searchQuery = budgetMatch ? query.replace(budgetMatch[0], ' ') : query
    const tokens = normalizedText(searchQuery).split(' ').filter((token) => token && !stopWords.has(token) && !/^\d+$/.test(token)).map((token) => searchSynonyms[token] ?? token)

    const results = products.filter((product) => category === 'All' || product.category === category).map((product) => {
      const searchable = normalizedText(`${product.name} ${product.category} ${product.seller} ${product.description} ${Object.entries(product.specs).map(([key, value]) => `${key} ${value}`).join(' ')}`)
      const hits = tokens.filter((token) => searchable.includes(token) || searchable.includes(`${token}s`)).length
      return { product, score: tokens.length ? hits / tokens.length : 1, hits }
    }).filter(({ product, hits }) => (!budget || product.price <= budget) && (tokens.length === 0 || hits >= Math.max(1, Math.ceil(tokens.length * 0.4))))

    results.sort((left, right) => {
      if (sort === 'price-low') return left.product.price - right.product.price
      if (sort === 'price-high') return right.product.price - left.product.price
      if (sort === 'rating') return right.product.rating - left.product.rating || right.product.reviewCount - left.product.reviewCount
      return right.score - left.score || right.product.rating - left.product.rating
    })
    return results.map(({ product }) => product)
  }, [products, category, query, sort])

  const viewedProducts = recentlyViewed.map((id) => products.find((product) => product.id === id)).filter((product): product is Product => Boolean(product)).slice(0, 4)
  const wishlistProducts = wishlist.map((id) => products.find((product) => product.id === id)).filter((product): product is Product => Boolean(product))
  const sellerCount = new Set(products.map((product) => product.sellerId)).size

  const notify = (message: string) => {
    setNotice(message)
    window.setTimeout(() => setNotice(''), 2600)
  }
  const navigate = (nextPage: Page) => {
    setPage(nextPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const addToCart = (id: string) => {
    const product = products.find((item) => item.id === id)
    setCart((current) => {
      const existing = current.find((item) => item.productId === id)
      return existing
        ? current.map((item) => item.productId === id ? { ...item, quantity: Math.min(item.quantity + 1, product?.stock ?? 99) } : item)
        : [...current, { productId: id, quantity: 1 }]
    })
    notify('Added to your bag')
  }
  const toggleWishlist = (id: string) => setWishlist((current) => {
    const exists = current.includes(id)
    notify(exists ? 'Removed from saved finds' : 'Saved to your wishlist')
    return exists ? current.filter((item) => item !== id) : [...current, id]
  })
  const toggleCompare = (id: string) => setCompared((current) => {
    if (current.includes(id)) return current.filter((item) => item !== id)
    if (current.length >= 3) { notify('Compare up to three products at a time'); return current }
    notify('Added to compare')
    return [...current, id]
  })
  const openProduct = (product: Product) => {
    setSelectedProduct(product)
    setRecentlyViewed((current) => [product.id, ...current.filter((id) => id !== product.id)].slice(0, 8))
  }
  const openStore = (product: Product) => {
    setStoreViewId(product.sellerId)
    navigate('store')
  }
  const startSearch = () => { setCategory('All'); setSort('relevance'); navigate('explore') }
  const updateQuantity = (id: string, quantity: number) => {
    const product = products.find((item) => item.id === id)
    setCart((current) => quantity <= 0
      ? current.filter((item) => item.productId !== id)
      : current.map((item) => item.productId === id ? { ...item, quantity: Math.min(quantity, product?.stock ?? 99) } : item))
  }
  const checkout = () => {
    const total = cart.reduce((sum, line) => sum + (products.find((product) => product.id === line.productId)?.price ?? 0) * line.quantity, 0)
    if (!cart.length) return
    const id = `AX-${Date.now().toString().slice(-6)}`
    setOrders((current) => [{ id, date: new Date().toISOString(), total, items: cart.reduce((count, item) => count + item.quantity, 0) }, ...current])
    setConfirmationId(id)
    setCart([])
    navigate('confirmation')
  }

  useEffect(() => {
    document.title = page === 'home' ? 'AURORA X — One search. Every store.' : `${page[0].toUpperCase()}${page.slice(1)} · AURORA X`
  }, [page])

  useEffect(() => {
    let active = true
    api.products()
      .then((remoteProducts: ApiProduct[]) => {
        if (!active) return
        setApiStatus('connected')
        if (remoteProducts.length > 0) {
          const categories = new Set<Category>([
            'Electronics', 'Fashion', 'Home', 'Beauty', 'Sports', 'Books', 'Automotive', 'Accessories',
          ])
          setProducts(remoteProducts.map((product) => ({
            id: product.id,
            name: product.name,
            category: categories.has(product.category as Category) ? product.category as Category : 'Accessories',
            price: product.price,
            rating: 5,
            reviewCount: 0,
            seller: product.store_name,
            sellerId: product.store_id,
            delivery: 'Seller delivery details',
            image: product.image_url || 'https://images.unsplash.com/photo-1490312278390-ab64016e0aa9?auto=format&fit=crop&w=960&q=85',
            description: product.description,
            stock: product.quantity,
            specs: { Category: product.category, Condition: 'New' },
          })))
        }
      })
      .catch(() => {
        if (active) setApiStatus('demo')
      })
    return () => { active = false }
  }, [setProducts])

  const handlers: ProductHandlers = { wishlist, compared, onWishlist: toggleWishlist, onCompare: toggleCompare, onAdd: addToCart, onOpen: openProduct, onSeller: openStore }

  return <div className="app-shell">
    <SiteHeader page={page} onNavigate={navigate} cartCount={cartCount} wishlistCount={wishlist.length} />
    <div className="context-rail"><div><span className="context-live" /> {apiStatus === 'loading' ? 'Loading the marketplace API' : apiStatus === 'connected' ? 'Live API catalogue connected' : 'Curated local catalogue'} <span className="context-dot">·</span> {sellerCount} independent {apiStatus === 'demo' ? 'demo' : ''} sellers <span className="context-dot">·</span> {apiStatus === 'demo' ? 'No live internet search' : 'Backend integration active'}</div><div><button onClick={() => navigate('compare')}>Compare {compared.length > 0 && <span>{compared.length}</span>}</button><span className="context-separator" /><button onClick={() => navigate('account')}><UserRound size={14} /> {customerName || 'Account'}</button></div></div>
    {['home', 'explore', 'categories'].includes(page) && <MarketplacePage page={page} products={rankedProducts} allProducts={products} recentlyViewed={viewedProducts} query={query} category={category} sort={sort} onQuery={setQuery} onSearch={startSearch} onCategory={setCategory} onSort={setSort} onNavigate={navigate} {...handlers} />}
    {page === 'assistant' && <AssistantPage products={rankedProducts} handlers={handlers} onAsk={(prompt) => { setQuery(prompt); setCategory('All'); setSort('relevance') }} />}
    {['compare', 'cart', 'wishlist', 'confirmation', 'orders', 'account'].includes(page) && <CommercePage page={page} products={page === 'wishlist' ? wishlistProducts : rankedProducts} allProducts={products} cart={cart} orders={orders} customerName={customerName} confirmationId={confirmationId} onQuantity={updateQuantity} onRemove={(id) => updateQuantity(id, 0)} onCheckout={checkout} onNavigate={navigate} onName={setCustomerName} {...handlers} />}
    {['seller', 'creator', 'store'].includes(page) && <SellerPage page={page} products={products} store={store} storeId={storeViewId} onStore={(value) => { setStore(value); setStoreViewId(value.id); setProducts((current) => current.map((product) => product.id.startsWith('seller-') ? { ...product, seller: value.name, sellerId: value.id } : product)); navigate('store') }} onAddProduct={(product) => { setProducts((current) => [...current, product]); notify('Product added to your catalogue') }} onUpdateProduct={(product) => setProducts((current) => current.map((item) => item.id === product.id ? product : item))} onDeleteProduct={(id) => { setProducts((current) => current.filter((product) => product.id !== id)); notify('Product removed') }} onNavigate={navigate} />}
    {page === 'support' && <SupportPage products={products} />}
    <div className="mobile-dock" aria-label="Quick navigation"><button className={page === 'home' ? 'active' : ''} onClick={() => navigate('home')} aria-label="Home"><Home size={18} /><span>Home</span></button><button className={page === 'explore' ? 'active' : ''} onClick={() => navigate('explore')} aria-label="Explore"><Compass size={18} /><span>Explore</span></button><button className={page === 'assistant' ? 'active' : ''} onClick={() => navigate('assistant')} aria-label="AI stylist"><span className="dock-sparkle">✳</span><span>Stylist</span></button><button className={page === 'cart' ? 'active' : ''} onClick={() => navigate('cart')} aria-label="Bag"><span className="dock-bag"><ShoppingBag size={16} />{cartCount > 0 && <i>{cartCount}</i>}</span><span>Bag</span></button><button className={page === 'account' ? 'active' : ''} onClick={() => navigate('account')} aria-label="Account"><UserRound size={18} /><span>Account</span></button></div>
    {selectedProduct && <ProductDetailDialog product={selectedProduct} related={products.filter((item) => item.category === selectedProduct.category && item.id !== selectedProduct.id).slice(0, 2)} wished={wishlist.includes(selectedProduct.id)} onClose={() => setSelectedProduct(null)} onAdd={() => addToCart(selectedProduct.id)} onWishlist={() => toggleWishlist(selectedProduct.id)} onRelated={(product) => openProduct(product)} onSeller={() => { openStore(selectedProduct); setSelectedProduct(null) }} />}
    {notice && <div className="toast-message"><span><Check size={14} /></span>{notice}<button onClick={() => navigate('cart')}>View bag</button></div>}
    <button className="back-to-top" title="Back to top" aria-label="Back to top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}><ArrowUp size={15} /></button>
  </div>
}

export default App