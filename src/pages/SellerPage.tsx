import { useState } from 'react'
import { ArrowRight, BarChart3, Check, ChevronDown, Eye, Lightbulb, Plus, Rocket, ShieldAlert, Sparkles, Store, Trash2, Upload, WandSparkles } from 'lucide-react'
import { categories, formatPrice } from '../data/products'
import type { Category, Page, Product, SellerStore } from '../types'
import { usePersistentState } from '../hooks/usePersistentState'
import './SellerPage.css'

type SellerOrder = { id: string; buyer: string; item: string; total: number; status: 'Processing' | 'Ready to ship' | 'Shipped' }
const sampleOrders: SellerOrder[] = [
  { id: 'AX-1988', buyer: 'Riya K.', item: 'Astra 55" 4K QLED Television', total: 42990, status: 'Ready to ship' },
  { id: 'AX-1986', buyer: 'Sam D.', item: 'Fieldwork Active Watch', total: 12990, status: 'Processing' },
  { id: 'AX-1982', buyer: 'Nina P.', item: 'Halo Task Light in Warm Brass', total: 5490, status: 'Shipped' },
]

type SellerPageProps = {
  page: Page
  products: Product[]
  store: SellerStore | null
  storeId: string
  onStore: (store: SellerStore) => void
  onAddProduct: (product: Product) => void
  onUpdateProduct: (product: Product) => void
  onDeleteProduct: (id: string) => void
  onNavigate: (page: Page) => void
}

const accentOptions = [
  { label: 'Electric violet', value: '#9b7bff' },
  { label: 'Citrus', value: '#dbef72' },
  { label: 'Lagoon', value: '#68d7c3' },
  { label: 'Coral', value: '#ff8876' },
]

const seedStore: SellerStore = { id: 'northstar', name: 'Northstar Living', category: 'Electronics', description: 'Thoughtful technology for the everyday, chosen for a life well lived.', personality: 'Considered', accent: '#9b7bff', published: true }

export function SellerPage({ page, products, store, storeId, onStore, onAddProduct, onUpdateProduct, onDeleteProduct, onNavigate }: SellerPageProps) {
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [formName, setFormName] = useState('')
  const [formCategory, setFormCategory] = useState<Category>('Accessories')
  const [formPrice, setFormPrice] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [generated, setGenerated] = useState(false)
  const [draftName, setDraftName] = useState(store?.name ?? '')
  const [draftCategory, setDraftCategory] = useState<Category>(store?.category ?? 'Accessories')
  const [draftDescription, setDraftDescription] = useState(store?.description ?? '')
  const [personality, setPersonality] = useState(store?.personality ?? 'Considered')
  const [accent, setAccent] = useState(store?.accent ?? accentOptions[0].value)
  const [previewing, setPreviewing] = useState(false)
  const [demoSession, setDemoSession] = usePersistentState('aurora-seller-session', true)
  const [formStock, setFormStock] = useState('12')
  const [sellerOrders, setSellerOrders] = usePersistentState<SellerOrder[]>('aurora-seller-orders', sampleOrders)
  const [sellerSuggestion, setSellerSuggestion] = useState('A cross-category bundle could be worth testing with your top-rated product.')
  if (!demoSession && page === 'seller') return <main className="page-content seller-page seller-access-page"><div className="seller-access-mark"><Store size={23} /></div><div className="eyebrow">AURORA STUDIO · SELLER ACCESS</div><h1>Your shop,<br /><span>your point of view.</span></h1><p>Open the preloaded seller workspace or create a store with your own demo profile. No account is created and no personal details are collected.</p><div className="seller-access-actions"><button className="button button-primary" onClick={() => setDemoSession(true)}>Sign in to demo dashboard <ArrowRight size={15} /></button><button className="button button-secondary" onClick={() => onNavigate('creator')}>Register a demo store <Store size={15} /></button></div><small>Demo sign-in uses a local session only.</small></main>

  const sellerProducts = products.filter((product) => product.sellerId === (store?.id ?? 'northstar'))
  const openNewProduct = () => { setEditing(null); setFormName(''); setFormCategory('Accessories'); setFormPrice(''); setFormStock('12'); setFormDescription(''); setGenerated(false); setFormOpen(true) }
  const openEditProduct = (product: Product) => { setEditing(product); setFormName(product.name); setFormCategory(product.category); setFormPrice(String(product.price)); setFormStock(String(product.stock)); setFormDescription(product.description); setGenerated(false); setFormOpen(true) }
  const generateCopy = () => {
    if (!formName.trim()) setFormName(`${formCategory} essential`)
    setFormDescription(`${formName.trim() || formCategory} — thoughtfully selected for everyday use. Designed with care, made to last, and ready to become part of your routine.`)
    setGenerated(true)
  }
  const suggestPrice = () => {
    const comparables = products.filter((product) => product.category === formCategory)
    const average = comparables.length ? comparables.reduce((sum, product) => sum + product.price, 0) / comparables.length : Number(formPrice) || 2500
    const suggested = Math.round(average * 0.95 / 50) * 50
    setSellerSuggestion(`Local ${formCategory.toLowerCase()} demo listings average ${formatPrice(Math.round(average))}. Consider testing ${formatPrice(suggested)} as a launch price.`)
  }
  const suggestCampaign = () => setSellerSuggestion('Try a 48-hour launch offer with free shipping, then compare visits and saves before extending it. Demo suggestion only.')
  const saveProduct = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const price = Number(formPrice)
    const stock = Number(formStock)
    if (!formName.trim() || !price || price < 1 || !Number.isInteger(stock) || stock < 0) return
    const product: Product = {
      id: editing?.id ?? `seller-${Date.now()}`, name: formName.trim(), category: formCategory, price,
      rating: editing?.rating ?? 5, reviewCount: editing?.reviewCount ?? 0, seller: store?.name || 'Northstar Living', sellerId: store?.id || 'northstar',
      delivery: 'Ships in 3–5 days', image: editing?.image ?? 'https://images.unsplash.com/photo-1490312278390-ab64016e0aa9?auto=format&fit=crop&w=960&q=85',
      description: formDescription.trim() || 'A thoughtful find from an independent seller.', stock,
      specs: editing?.specs ?? { Category: formCategory, Condition: 'New', Seller: store?.name || 'Your new store' },
    }
    if (editing) onUpdateProduct(product)
    else onAddProduct(product)
    setFormOpen(false)
  }

  if (page === 'creator') {
    const previewStore: SellerStore = { id: store?.id ?? 'your-store', name: draftName || 'Your Store Name', category: draftCategory, description: draftDescription || 'Your story, told your way.', personality, accent, published: false }
    return <main className="page-content seller-page creator-page">
      <div className="seller-breadcrumb"><button onClick={() => onNavigate('seller')}>Seller studio</button><span>/</span><strong>Store creator</strong></div>
      <div className="creator-heading"><div><div className="eyebrow">AURORA STUDIO · STORE BUILDER</div><h1>Your corner<br />of the <span>universe.</span></h1><p>Set the tone. We'll bring the bones. Preview it all before you publish.</p></div><div className="creator-step"><span>01</span><i /><span>02</span><i /><span>03</span></div></div>
      <div className="creator-layout"><form className="creator-form" onSubmit={(event) => { event.preventDefault(); if (!draftName.trim()) return; onStore({ ...previewStore, id: store?.id ?? `store-${Date.now()}`, published: true }); setPreviewing(false); onNavigate('store') }}>
        <div className="form-section-title"><span>01</span><div><h2>The essentials</h2><p>Start with the story people will remember.</p></div></div>
        <label className="field-label">Store name<input value={draftName} onChange={(event) => setDraftName(event.target.value)} placeholder="e.g. Sunday Assembly" required /></label>
        <label className="field-label">Business category<select value={draftCategory} onChange={(event) => setDraftCategory(event.target.value as Category)}>{categories.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}</select><ChevronDown size={14} /></label>
        <label className="field-label">Your store story<textarea value={draftDescription} onChange={(event) => setDraftDescription(event.target.value)} placeholder="What do you make, and why should it exist?" rows={4} maxLength={240} /><small>{draftDescription.length}/240</small></label>
        <div className="form-section-title form-section-spaced"><span>02</span><div><h2>Make it yours</h2><p>A little personality goes a long way.</p></div></div>
        <label className="field-label">Brand personality<select value={personality} onChange={(event) => setPersonality(event.target.value)}><option>Considered</option><option>Playful</option><option>Minimal</option><option>Artisan</option><option>Bold</option></select><ChevronDown size={14} /></label>
        <div className="field-label"><span>Brand accent</span><div className="swatch-row">{accentOptions.map((option) => <button key={option.value} type="button" title={option.label} aria-label={option.label} className={`color-swatch ${accent === option.value ? 'selected' : ''}`} style={{ backgroundColor: option.value }} onClick={() => setAccent(option.value)} />)}</div></div>
        <div className="creator-actions"><button className="button button-secondary" type="button" onClick={() => { setPreviewing(!previewing); window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }) }}><Eye size={15} /> Preview store</button><button className="button button-primary" type="submit"><Rocket size={15} /> Publish demo store <ArrowRight size={14} /></button></div>
        <small className="demo-helper">Publishing creates a local demo storefront in this browser. No real seller account is created.</small>
      </form>
      <aside className="creator-preview"><div className="preview-window-bar"><span /><span /><span /><small>YOUR STOREFRONT PREVIEW</small></div><div className="store-preview-banner" style={{ '--store-accent': previewStore.accent } as React.CSSProperties}><span className="eyebrow">{previewStore.category.toUpperCase()} · INDEPENDENT STUDIO</span><strong>{previewStore.name}</strong><p>{previewStore.description}</p><div className="preview-brand-chip"><i style={{ backgroundColor: previewStore.accent }} /> {previewStore.personality} by nature</div></div><div className="store-preview-content"><div className="preview-store-header"><span>THE COLLECTION</span><span>{sellerProducts.length || '01'} FINDS</span></div><div className="preview-sample-product"><div className="preview-product-art" style={{ backgroundColor: `${previewStore.accent}25` }}><Store size={23} /></div><div><strong>{sellerProducts[0]?.name ?? 'Your first product'}</strong><small>{sellerProducts.length ? formatPrice(sellerProducts[0].price) : 'Add a product from your dashboard'}</small></div><ArrowRight size={14} /></div><div className="preview-disclaimer">Live store pages are not yet publicly hosted.</div></div><div className="preview-footnote"><Sparkles size={14} /> Store branding is generated from your choices. Product photography and catalogue are yours to add.</div></aside></div>
      {previewing && <div className="preview-toast"><Check size={14} /> Preview updated with your latest changes.</div>}
    </main>
  }

  if (page === 'store') {
    const activeStore = store?.id === storeId ? store : products.some((product) => product.sellerId === storeId)
      ? { ...seedStore, id: storeId, name: products.find((product) => product.sellerId === storeId)?.seller ?? seedStore.name, category: products.find((product) => product.sellerId === storeId)?.category ?? seedStore.category }
      : seedStore
    const storeProducts = products.filter((product) => product.sellerId === activeStore.id)
    return <main className="page-content store-page"><button className="text-link store-back" onClick={() => onNavigate('explore')}>← Back to the marketplace</button><section className="store-hero" style={{ '--store-accent': activeStore.accent } as React.CSSProperties}><span className="eyebrow">INDEPENDENT STUDIO · {activeStore.category.toUpperCase()}</span><div className="store-avatar">{activeStore.name.slice(0, 1)}</div><h1>{activeStore.name}</h1><p>{activeStore.description}</p><span className="store-demo-mark"><span /> AURORA X SELLER · DEMO PROFILE</span></section><div className="store-stats"><span><strong>{storeProducts.length}</strong> curated finds</span><span><strong>4.8</strong> community rating</span><span><strong>96%</strong> on-time dispatch <i className="simulated-label">SIMULATED</i></span></div><div className="section-heading"><div><div className="eyebrow">THE COLLECTION</div><h2>Made with intention.</h2></div></div>{storeProducts.length ? <div className="store-product-list">{storeProducts.map((product) => <article key={product.id}><img src={product.image} alt={product.name} /><div><span className="eyebrow">{product.category}</span><strong>{product.name}</strong><p>{product.description}</p></div><b>{formatPrice(product.price)}</b></article>)}</div> : <div className="empty-results"><Store size={22} /><strong>Your collection is getting started.</strong><p>Add products from the Seller Studio.</p><button className="text-link" onClick={() => onNavigate('seller')}>Open Seller Studio <ArrowRight size={14} /></button></div>}<div className="trust-explainer"><ShieldAlert size={16} /><span>Seller ratings and fulfilment metrics shown in this prototype are simulated demo data, not verified claims.</span></div></main>
  }

  const dashboardProducts = products.filter((product) => product.sellerId === (store?.id ?? 'northstar'))
  const revenue = dashboardProducts.reduce((sum, product) => sum + product.price * Math.min(product.stock, 8), 0)
  return <main className="page-content seller-page dashboard-page">
    <div className="dashboard-topline"><div><div className="eyebrow">AURORA STUDIO · DEMO WORKSPACE</div><h1>Seller <span>studio.</span></h1><p>A quiet place to run your corner of the market.</p></div><div className="dashboard-tools"><span className="demo-chip">DEMO ACCOUNT</span><button className="button button-secondary" onClick={() => onNavigate('creator')}><WandSparkles size={15} /> Store creator</button><button className="button button-secondary" onClick={() => setDemoSession(false)}>Sign out</button></div></div>
    <div className="seller-tabs"><button className="selected">Overview</button><button onClick={() => document.getElementById('inventory')?.scrollIntoView({ behavior: 'smooth' })}>Products</button><button onClick={() => onNavigate('support')}>Messages <span>2</span></button><button onClick={() => onNavigate('store')}>View storefront <ArrowRight size={13} /></button></div>
    <div className="seller-welcome"><div><span className="welcome-eyebrow">YOUR BUSINESS, AT A GLANCE</span><h2>{store?.name || 'Northstar Living'}<span className="store-live-dot" /></h2><p>{store ? store.description : 'Thoughtful technology for the everyday, chosen for a life well lived.'}</p><button className="text-link" onClick={() => onNavigate('store')}>Visit your storefront <ArrowRight size={14} /></button></div><div className="welcome-mark"><Store size={25} /><span>INDEPENDENT<br />BY DESIGN</span></div></div>
    <div className="seller-stats-grid"><div className="seller-stat-card"><span>DEMO REVENUE</span><strong>{formatPrice(revenue)}</strong><small><BarChart3 size={12} /> Illustrative inventory estimate</small></div><div className="seller-stat-card"><span>PRODUCTS LIVE</span><strong>{dashboardProducts.length}</strong><small><span className="stat-green-dot" /> Catalogue items</small></div><div className="seller-stat-card"><span>ORDERS THIS MONTH</span><strong>24</strong><small><span className="simulated-label">SIMULATED</span> Demo activity</small></div><div className="seller-stat-card"><span>STORE VISITS</span><strong>1,284</strong><small><span className="simulated-label">SIMULATED</span> Demo activity</small></div></div>
    <div className="seller-main-grid"><section className="seller-panel" id="inventory"><div className="panel-heading"><div><div className="eyebrow">YOUR CATALOGUE</div><h2>Products</h2></div><button className="button button-primary button-small" onClick={openNewProduct}><Plus size={15} /> Add product</button></div>{formOpen && <form className="product-editor" onSubmit={saveProduct}><div className="editor-heading"><strong>{editing ? 'Edit product' : 'New product'}</strong><button type="button" className="icon-button" aria-label="Close product form" onClick={() => setFormOpen(false)}>×</button></div><label className="field-label">Product title<input value={formName} onChange={(event) => setFormName(event.target.value)} placeholder="Name this find" required /></label><div className="editor-fields"><label className="field-label">Category<select value={formCategory} onChange={(event) => setFormCategory(event.target.value as Category)}>{categories.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}</select><ChevronDown size={13} /></label><label className="field-label">Price (₹)<input type="number" min="1" value={formPrice} onChange={(event) => setFormPrice(event.target.value)} placeholder="2500" required /></label><label className="field-label">Inventory units<input type="number" min="0" step="1" value={formStock} onChange={(event) => setFormStock(event.target.value)} required /></label></div><label className="field-label">Description<textarea value={formDescription} onChange={(event) => setFormDescription(event.target.value)} rows={3} placeholder="A few words about what makes it special" /></label><button className="ai-copy-button" type="button" onClick={generateCopy}><WandSparkles size={14} /> {generated ? 'Regenerate demo copy' : 'Draft with AI seller assistant'}</button>{generated && <small className="demo-helper">Generated from your product details using a local template. No AI service is connected.</small>}<div className="editor-actions"><button className="button button-primary button-small" type="submit">Save product</button><button className="text-link" type="button" onClick={() => setFormOpen(false)}>Cancel</button></div></form>}
      {dashboardProducts.length ? dashboardProducts.map((product) => <article className="seller-product-row" key={product.id}><img src={product.image} alt={product.name} /><div><strong>{product.name}</strong><span>{product.category} · {product.stock} in stock</span></div><b>{formatPrice(product.price)}</b><span className="inventory-status">Live</span><button className="row-icon-button" title="Edit product" aria-label={`Edit ${product.name}`} onClick={() => openEditProduct(product)}><Eye size={15} /></button><button className="row-icon-button danger" title="Delete product" aria-label={`Delete ${product.name}`} onClick={() => onDeleteProduct(product.id)}><Trash2 size={15} /></button></article>) : <div className="empty-inventory"><Store size={20} /><span>No products yet. Add your first find to get started.</span></div>}</section>
      <aside className="seller-side-column"><section className="trustshield-panel"><div className="trustshield-heading"><span className="trustshield-icon"><ShieldAlert size={17} /></span><div><div className="eyebrow">AURORA TRUSTSHIELD</div><strong>Seller signals</strong></div><span className="simulated-label">SIMULATED</span></div><p>Illustrative trust indicators for this demo seller profile. No real verification is performed.</p><div className="trust-metric"><span>Profile completeness</span><strong>92%</strong><i><b style={{ width: '92%' }} /></i></div><div className="trust-metric"><span>Fulfilment on time</span><strong>96%</strong><i><b style={{ width: '96%' }} /></i></div><div className="trust-metric"><span>Open complaints</span><strong>1</strong><small>Demo data</small></div><div className="risk-indicator"><Check size={14} /> No simulated listing flags</div></section><section className="seller-insight"><div className="eyebrow"><Lightbulb size={13} /> SELLER ASSISTANT · LOCAL DEMO</div><h3>Ideas for your next move.</h3><p>{sellerSuggestion}</p><div className="seller-suggestion-actions"><button onClick={suggestPrice}>Suggest a price</button><button onClick={suggestCampaign}>Plan a promotion</button></div><button className="text-link" onClick={() => setFormOpen(true)}>Work on a listing <ArrowRight size={13} /></button></section></aside></div>
    <section className="seller-panel seller-orders-panel"><div className="panel-heading"><div><div className="eyebrow">ORDER DESK · SIMULATED</div><h2>Recent orders</h2></div><span className="simulated-label">DEMO DATA</span></div><div className="seller-order-list">{sellerOrders.map((order) => <article key={order.id}><div><span className="eyebrow">{order.id} · {order.buyer}</span><strong>{order.item}</strong></div><b>{formatPrice(order.total)}</b><select aria-label={`Order status for ${order.id}`} value={order.status} onChange={(event) => setSellerOrders((current) => current.map((item) => item.id === order.id ? { ...item, status: event.target.value as SellerOrder['status'] } : item))}><option>Processing</option><option>Ready to ship</option><option>Shipped</option></select></article>)}</div></section>
    <div className="seller-footer-note"><Upload size={14} /> Images, inventory and sales are local demo data. Storefront publishing does not create a public website.</div>
  </main>
}