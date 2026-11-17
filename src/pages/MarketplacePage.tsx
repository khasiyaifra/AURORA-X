import { ArrowDownRight, ArrowRight, AudioLines, ChevronDown, Sparkles } from 'lucide-react'
import { categories, formatPrice } from '../data/products'
import type { Page, Product } from '../types'
import { ProductCard } from '../components/ProductCard'

export type ProductHandlers = {
  wishlist: string[]
  compared: string[]
  onWishlist: (id: string) => void
  onCompare: (id: string) => void
  onAdd: (id: string) => void
  onOpen: (product: Product) => void
  onSeller?: (product: Product) => void
}

type MarketplacePageProps = ProductHandlers & {
  page: Page
  products: Product[]
  allProducts: Product[]
  recentlyViewed: Product[]
  query: string
  category: string
  sort: string
  onQuery: (value: string) => void
  onSearch: () => void
  onCategory: (value: string) => void
  onSort: (value: string) => void
  onNavigate: (page: Page) => void
}

function ProductGrid({ products, handlers, emptyMessage = 'Try a broader search or clear your filters.' }: { products: Product[]; handlers: ProductHandlers; emptyMessage?: string }) {
  if (products.length === 0) return <div className="empty-results"><span className="empty-orbit">◌</span><strong>No exact matches, yet.</strong><p>{emptyMessage}</p></div>
  return <div className="product-grid">{products.map((product) => <ProductCard key={product.id} product={product} wished={handlers.wishlist.includes(product.id)} compared={handlers.compared.includes(product.id)} onWishlist={() => handlers.onWishlist(product.id)} onCompare={() => handlers.onCompare(product.id)} onAdd={() => handlers.onAdd(product.id)} onOpen={() => handlers.onOpen(product)} onSeller={() => handlers.onSeller?.(product)} />)}</div>
}

export function MarketplacePage(props: MarketplacePageProps) {
  const handlers: ProductHandlers = props
  const isHome = props.page === 'home'
  const isCategories = props.page === 'categories'
  const featured = props.allProducts[0]
  const categoryCount = (name: string) => {
    const count = props.allProducts.filter((product) => product.category === name).length
    return `${count} ${count === 1 ? 'find' : 'finds'}`
  }
  const deals = [...props.allProducts].filter((product) => product.originalPrice).sort((a, b) => (b.originalPrice! - b.price) / b.originalPrice! - (a.originalPrice! - a.price) / a.originalPrice!).slice(0, 4)
  const searchBar = (large = false) => (
    <form className={`universal-search ${large ? 'search-large' : ''}`} onSubmit={(event) => { event.preventDefault(); props.onSearch() }}>
      <Sparkles size={17} className="search-spark" />
      <input value={props.query} onChange={(event) => props.onQuery(event.target.value)} placeholder="Describe what you're looking for..." aria-label="Search the product catalogue" />
      <button type="button" className="voice-button" title="Voice search demo" aria-label="Voice search demo" onClick={() => { props.onQuery('55-inch 4K television under ₹50,000 with 3-year warranty'); props.onSearch() }}><AudioLines size={17} /></button>
      <button className="search-submit" type="submit"><span>{large ? 'Find my match' : 'Search'}</span><ArrowRight size={16} /></button>
    </form>
  )

  if (isHome) return (
    <main className="page-content home-page">
      <section className="hero-section">
        <div className="hero-copy">
          <div className="hero-kicker"><span className="kicker-line" /> THE MARKETPLACE, REIMAGINED</div>
          <h1>One search.<br /><span>Every good find.</span></h1>
          <p>Discover independent makers, cult favourites and the right deal, all in one considered place.</p>
          {searchBar(true)}
          <div className="hero-search-hint"><span>TRY</span><button onClick={() => { props.onQuery('55-inch 4K television under ₹50,000 with 3-year warranty'); props.onSearch() }}>“A 4K TV under ₹50,000 with a 3-year warranty” <ArrowRight size={13} /></button></div>
          <div className="hero-proof"><div className="avatar-stack"><i>R</i><i>A</i><i>M</i><i>+</i></div><span>Made for curious people.<br /><strong>Built around independent shops.</strong></span></div>
        </div>
        <div className="hero-art">
          <div className="hero-image" style={{ backgroundImage: `url("${featured.image}")` }} role="img" aria-label={featured.name} />
          <div className="hero-image-wash" />
          <span className="hero-side-label">OBJECTS WITH A POINT OF VIEW <span>— 01 / 04</span></span>
          <div className="hero-product-note"><div><span>THE WEEK'S FIND</span><strong>{featured.name}</strong><small>by {featured.seller}</small></div><div><span>FROM</span><strong>{formatPrice(featured.price)}</strong><ArrowDownRight size={17} /></div></div>
          <div className="hero-coordinate">19°04′ N &nbsp; 72°52′ E</div>
        </div>
        <div className="hero-index"><span>01</span><i /><span>04</span></div>
      </section>

      <section className="trust-ribbon"><div><span className="trust-icon">✳</span> Independent sellers, one shared universe</div><div>Thoughtfully found <span className="ribbon-dot">·</span> Fairly priced <span className="ribbon-dot">·</span> Ready to ship</div><button onClick={() => props.onNavigate('explore')}>Explore the marketplace <ArrowRight size={14} /></button></section>

      <section className="section-block category-section">
        <div className="section-heading"><div><div className="eyebrow">A PLACE FOR EVERY INTEREST</div><h2>Follow your curiosity.</h2></div><button className="text-link" onClick={() => props.onNavigate('categories')}>All categories <ArrowRight size={15} /></button></div>
        <div className="category-grid">{categories.map((category, index) => <button key={category.name} className="category-tile" onClick={() => { props.onQuery(''); props.onCategory(category.name); props.onNavigate('explore') }}><span className={`category-glyph glyph-${index}`}>{category.icon}</span><span className="category-name">{category.name}</span><span className="category-count">{categoryCount(category.name)}</span><ArrowRight size={14} className="category-arrow" /></button>)}</div>
      </section>

      <section className="section-block product-section">
        <div className="section-heading"><div><div className="eyebrow">THE GOOD STUFF, RIGHT NOW</div><h2>Picked for your orbit.</h2><p>Small-batch finds. Big main-character energy.</p></div><button className="text-link" onClick={() => props.onNavigate('explore')}>See everything <ArrowRight size={15} /></button></div>
        <ProductGrid products={props.allProducts.slice(0, 4)} handlers={handlers} />
      </section>

      <section className="promo-band"><div className="promo-graphic"><div className="promo-ring ring-one" /><div className="promo-ring ring-two" /><span>3<span>%</span></span></div><div className="promo-copy"><div className="eyebrow">A BETTER WAY TO SELL</div><h2>More room for the<br />people behind the product.</h2><p>Open your own corner of the marketplace. No storefront code required.</p><button className="button button-light" onClick={() => props.onNavigate('creator')}>Build your store <ArrowRight size={15} /></button></div><div className="promo-mark">AURORA<br />SELLER STUDIO</div></section>

      <section className="section-block product-section">
        <div className="section-heading"><div><div className="eyebrow">A LITTLE MOMENTUM</div><h2>Trending across the market.</h2><p>Well-loved things, finding new homes.</p></div><button className="text-link" onClick={() => props.onNavigate('explore')}>Shop all trending <ArrowRight size={15} /></button></div>
        <ProductGrid products={props.allProducts.slice(4, 8)} handlers={handlers} />
      </section>

      <section className="section-block product-section"><div className="section-heading"><div><div className="eyebrow">GOOD THINGS, BETTER PRICES</div><h2>Deals worth a closer look.</h2><p>Current markdowns from independent demo shops.</p></div><button className="text-link" onClick={() => props.onNavigate('explore')}>Explore all deals <ArrowRight size={15} /></button></div><ProductGrid products={deals} handlers={handlers} /></section>

      <section className="editorial-strip"><div className="editorial-image" /><div className="editorial-copy"><span className="eyebrow">THE INDEPENDENT EDIT · 04 MIN READ</span><h2>Good things,<br />closer to home.</h2><p>Meet the small studios making everyday objects feel anything but ordinary.</p><button className="text-link" onClick={() => props.onNavigate('explore')}>Meet the makers <ArrowRight size={15} /></button></div><div className="editorial-number">01 <span>/</span> 03</div></section>

      <section className="section-block product-section">
        <div className="section-heading"><div><div className="eyebrow">A GOOD PLACE TO START</div><h2>Best sellers, no guesswork.</h2></div><button className="text-link" onClick={() => props.onNavigate('explore')}>Browse the bestsellers <ArrowRight size={15} /></button></div>
        <ProductGrid products={[...props.allProducts].sort((a, b) => b.reviewCount - a.reviewCount).slice(0, 4)} handlers={handlers} />
      </section>

      {props.recentlyViewed.length > 0 && <section className="section-block product-section recently-viewed"><div className="section-heading"><div><div className="eyebrow">PICKING UP WHERE YOU LEFT OFF</div><h2>Back in your orbit.</h2></div></div><ProductGrid products={props.recentlyViewed} handlers={handlers} /></section>}
      <footer className="site-footer"><div className="footer-brand">AURORA<span>X</span></div><span>One search. Every store. The right deal.</span><div>Made for the curious <span>© 2026 AURORA X · DEMO MARKETPLACE</span></div></footer>
    </main>
  )

  if (isCategories) return (
    <main className="page-content catalog-page">
      <div className="page-intro"><div><div className="eyebrow">THE MARKETPLACE DIRECTORY</div><h1>Find your next<br /><span>favourite thing.</span></h1></div><p>Eight corners of the market, thousands of thoughtful finds.<br />Everything here is part of our local demo catalogue.</p></div>
      <div className="category-grid category-grid-large">{categories.map((item, index) => <button key={item.name} className="category-tile" onClick={() => { props.onQuery(''); props.onCategory(item.name); props.onNavigate('explore') }}><span className={`category-glyph glyph-${index}`}>{item.icon}</span><span className="category-name">{item.name}</span><span className="category-count">{categoryCount(item.name)} to explore</span><ArrowRight size={14} className="category-arrow" /></button>)}</div>
      <div className="category-note"><Sparkles size={16} /><span>Looking for something specific? Tell our local search what matters to you.</span><button className="text-link" onClick={() => props.onNavigate('assistant')}>Ask the stylist <ArrowRight size={14} /></button></div>
    </main>
  )

  return (
    <main className="page-content catalog-page explore-page">
      <div className="catalog-heading"><div><div className="eyebrow">THE AURORA X MARKETPLACE</div><h1>{props.query ? <>Results for <span>“{props.query.length > 36 ? `${props.query.slice(0, 36)}…` : props.query}”</span></> : <>A little bit of<br /><span>everything good.</span></>}</h1><p>Searching our curated demo catalogue. Independent sellers, considered finds.</p></div>{searchBar()}</div>
      <div className="filter-toolbar"><div className="filter-categories"><button className={props.category === 'All' ? 'selected' : ''} onClick={() => props.onCategory('All')}>All finds</button>{categories.map((item) => <button key={item.name} className={props.category === item.name ? 'selected' : ''} onClick={() => props.onCategory(item.name)}>{item.name}</button>)}</div><label className="sort-select"><span>{props.products.length} finds</span><select value={props.sort} onChange={(event) => props.onSort(event.target.value)} aria-label="Sort products"><option value="relevance">Relevance</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option><option value="rating">Top rated</option></select><ChevronDown size={14} /></label></div>
      {props.query && <div className="search-interpretation"><Sparkles size={14} /><span>Local catalogue match</span><i /> Matching name, category and product specifications{props.query.match(/\d/) && <><i /> Budget and size clues included</>}</div>}
      <ProductGrid products={props.products} handlers={handlers} emptyMessage="We only search this curated demo catalogue. Try a category or adjust the wording." />
      <div className="catalog-bottom"><span>Showing {props.products.length} of {props.allProducts.length} demo products</span><button className="text-link" onClick={() => props.onNavigate('assistant')}>Need a hand? Talk to the AI stylist <ArrowRight size={14} /></button></div>
    </main>
  )
}