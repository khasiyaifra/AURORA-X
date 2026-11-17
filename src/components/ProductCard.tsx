import { ArrowRight, Heart, Scale, ShoppingBag, Star } from 'lucide-react'
import type { Product } from '../types'
import { formatPrice } from '../data/products'
import './ProductCard.css'

type ProductCardProps = {
  product: Product
  wished: boolean
  compared: boolean
  onWishlist: () => void
  onCompare: () => void
  onAdd: () => void
  onOpen: () => void
  onSeller?: () => void
}

export function ProductCard({ product, wished, compared, onWishlist, onCompare, onAdd, onOpen, onSeller }: ProductCardProps) {
  const discount = product.originalPrice
    ? Math.round((1 - product.price / product.originalPrice) * 100)
    : null

  return (
    <article className="product-card">
      <div className="product-image-wrap">
        <button className="product-image-open" onClick={onOpen} aria-label={`View details for ${product.name}`}>
          <img src={product.image} alt={product.name} loading="lazy" onError={(event) => { event.currentTarget.style.opacity = '0' }} />
          {product.badge && <span className="product-badge">{product.badge}</span>}
        </button>
        <div className="image-actions">
          <button className={`icon-button ${wished ? 'is-active' : ''}`} onClick={(event) => { event.stopPropagation(); onWishlist() }} aria-label={wished ? 'Remove from wishlist' : 'Add to wishlist'} title={wished ? 'Remove from wishlist' : 'Add to wishlist'}>
            <Heart size={16} fill={wished ? 'currentColor' : 'none'} />
          </button>
          <button className={`icon-button ${compared ? 'is-active' : ''}`} onClick={(event) => { event.stopPropagation(); onCompare() }} aria-label={compared ? 'Remove from comparison' : 'Add to comparison'} title={compared ? 'Remove from comparison' : 'Compare product'}>
            <Scale size={16} />
          </button>
        </div>
      </div>
      <div className="product-card-content">
        <div className="product-meta-row"><span>{product.category}</span><span className="rating"><Star size={12} fill="currentColor" /> {product.rating}</span></div>
        <button className="product-title" onClick={onOpen}>{product.name}</button>
        <button className="seller-link" onClick={onSeller ?? onOpen}>by {product.seller} <span>↗</span></button>
        <div className="product-price-row">
          <strong>{formatPrice(product.price)}</strong>
          {product.originalPrice && <del>{formatPrice(product.originalPrice)}</del>}
          {discount && <span className="discount">-{discount}%</span>}
        </div>
        <div className="product-delivery">{product.delivery}</div>
        <div className="product-card-footer">
          <span>{product.stock < 10 ? `Only ${product.stock} left` : 'In stock'}</span>
          <button className="add-button" onClick={onAdd} aria-label={`Add ${product.name} to cart`} title="Add to cart"><ShoppingBag size={15} /></button>
        </div>
      </div>
    </article>
  )
}

export function ProductDetailDialog({ product, related, wished, onClose, onAdd, onWishlist, onRelated, onSeller }: {
  product: Product
  related: Product[]
  wished: boolean
  onClose: () => void
  onAdd: () => void
  onWishlist: () => void
  onRelated: (product: Product) => void
  onSeller: () => void
}) {
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="product-dialog" role="dialog" aria-modal="true" aria-label={`${product.name} details`}>
        <button className="icon-button modal-close" onClick={onClose} aria-label="Close product details">×</button>
        <div className="dialog-product-layout">
          <div className="dialog-image"><img src={product.image} alt={product.name} onError={(event) => { event.currentTarget.style.opacity = '0' }} /></div>
          <div className="dialog-copy">
            <div className="eyebrow">{product.category} · INDEPENDENT SELLER</div>
            <h2>{product.name}</h2>
            <div className="dialog-rating"><Star size={15} fill="currentColor" /> {product.rating} <span>({product.reviewCount} reviews)</span></div>
            <p>{product.description}</p>
            <div className="dialog-price">{formatPrice(product.price)} {product.originalPrice && <del>{formatPrice(product.originalPrice)}</del>}</div>
            <div className="detail-specs">{Object.entries(product.specs).map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
            <div className="seller-trust"><span className="trust-dot" /><span><strong>{product.seller}</strong> · demo seller profile <i className="simulated-label">SIMULATED</i></span><span className="trust-score">4.8 <Star size={11} fill="currentColor" /></span></div>
            <button className="storefront-link" onClick={onSeller}>Visit seller storefront <ArrowRight size={13} /></button>
            <p className="delivery-note">{product.delivery} · {product.stock} available</p>
            <div className="dialog-actions"><button className="button button-primary" onClick={onAdd}><ShoppingBag size={16} /> Add to bag</button><button className={`button button-secondary ${wished ? 'is-active' : ''}`} onClick={onWishlist}><Heart size={16} fill={wished ? 'currentColor' : 'none'} /> {wished ? 'Saved' : 'Save'}</button></div>
          </div>
        </div>
        {related.length > 0 && <div className="related-row"><span>MORE FROM THIS WORLD</span>{related.map((item) => <button key={item.id} onClick={() => onRelated(item)}>{item.name} <span>{formatPrice(item.price)}</span></button>)}</div>}
      </section>
    </div>
  )
}