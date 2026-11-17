import { Headphones, Heart, LayoutDashboard, Search, ShoppingBag, Sparkles } from 'lucide-react'
import type { Page } from '../types'

const primaryLinks: { page: Page; label: string }[] = [
  { page: 'home', label: 'Home' },
  { page: 'explore', label: 'Explore' },
  { page: 'categories', label: 'Categories' },
  { page: 'assistant', label: 'AI stylist' },
]

export function SiteHeader({ page, onNavigate, cartCount, wishlistCount }: {
  page: Page
  onNavigate: (page: Page) => void
  cartCount: number
  wishlistCount: number
}) {
  return (
    <>
      <div className="announcement-bar"><span className="live-dot" /> A new kind of marketplace <span className="announcement-sep">/</span> Independent by nature, together by design <span className="announcement-right">AURORA X · PREVIEW 01</span></div>
      <header className="site-header">
        <button className="brand-lockup" onClick={() => onNavigate('home')} aria-label="Aurora X home"><span className="brand-mark"><span /></span><span>AURORA<span className="brand-x">X</span></span></button>
        <nav className="main-nav" aria-label="Main navigation">{primaryLinks.map((item) => <button key={item.page} className={page === item.page ? 'active' : ''} onClick={() => onNavigate(item.page)}>{item.label}{item.page === 'assistant' && <Sparkles size={12} />}</button>)}</nav>
        <div className="header-actions">
          <button className="header-icon search-shortcut" onClick={() => onNavigate('explore')} aria-label="Search" title="Explore"><Search size={18} /></button>
          <button className={`header-icon ${page === 'wishlist' ? 'active' : ''}`} onClick={() => onNavigate('wishlist')} aria-label={`Wishlist${wishlistCount ? `, ${wishlistCount} items` : ''}`} title="Wishlist"><Heart size={18} />{wishlistCount > 0 && <i>{wishlistCount}</i>}</button>
          <button className={`header-icon ${page === 'cart' ? 'active' : ''}`} onClick={() => onNavigate('cart')} aria-label={`Shopping bag${cartCount ? `, ${cartCount} items` : ''}`} title="Shopping bag"><ShoppingBag size={18} />{cartCount > 0 && <i>{cartCount}</i>}</button>
          <button className="header-icon support-shortcut" onClick={() => onNavigate('support')} aria-label="Support centre" title="Support"><Headphones size={18} /></button>
          <button className="seller-entry" onClick={() => onNavigate('seller')}><LayoutDashboard size={15} /> <span>For sellers</span></button>
        </div>
      </header>
    </>
  )
}