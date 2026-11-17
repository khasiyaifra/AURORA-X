import type { Category, Product } from '../types'

export const categories: { name: Category; icon: string }[] = [
  { name: 'Electronics', icon: '◉' },
  { name: 'Fashion', icon: '◇' },
  { name: 'Home', icon: '⌂' },
  { name: 'Beauty', icon: '✳' },
  { name: 'Sports', icon: '↗' },
  { name: 'Books', icon: '▤' },
  { name: 'Automotive', icon: '⌁' },
  { name: 'Accessories', icon: '◈' },
]

export const demoProducts: Product[] = [
  {
    id: 'aurora-tv', name: 'Astra 55" 4K QLED Television', category: 'Electronics', price: 42990, originalPrice: 58990,
    rating: 4.8, reviewCount: 284, seller: 'Northstar Living', sellerId: 'northstar', delivery: 'Free delivery · 2 days',
    image: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=960&q=85', badge: 'BESTSELLER',
    description: 'A vivid 4K QLED panel with cinema-grade colour, adaptive brightness and a beautifully minimal frame.', stock: 18,
    specs: { Display: '55-inch QLED · 4K UHD', Warranty: '3 years', Refresh: '120 Hz', Connectivity: 'Wi-Fi 6 · HDMI 2.1' },
  },
  {
    id: 'sonic-headphones', name: 'Sonic Studio Wireless Headphones', category: 'Electronics', price: 8990, originalPrice: 11990,
    rating: 4.7, reviewCount: 193, seller: 'Soundform Atelier', sellerId: 'soundform', delivery: 'Free delivery · Tomorrow',
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=960&q=85', badge: '−25%',
    description: 'Immersive spatial audio and adaptive noise cancellation, tuned for long listening sessions.', stock: 34,
    specs: { Battery: '38 hours', Audio: 'Spatial audio', Weight: '248 g', Warranty: '2 years' },
  },
  {
    id: 'arc-chair', name: 'Arc Lounge Chair in Moss', category: 'Home', price: 18900, originalPrice: 24900,
    rating: 4.9, reviewCount: 86, seller: 'Form & Field', sellerId: 'formfield', delivery: 'Free delivery · 4 days',
    image: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=960&q=85', badge: 'MADE TO ORDER',
    description: 'A sculptural, everyday lounge chair crafted from responsibly sourced ash and woven recycled fabric.', stock: 7,
    specs: { Material: 'Ash wood · recycled weave', Colour: 'Moss', Assembly: 'Tool-free', Warranty: '5 years' },
  },
  {
    id: 'linen-shirt', name: 'Coastline Linen Shirt', category: 'Fashion', price: 3490, originalPrice: 4490,
    rating: 4.6, reviewCount: 124, seller: 'Sunday Assembly', sellerId: 'sunday', delivery: 'Free delivery · 3 days',
    image: 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=960&q=85', badge: '−22%',
    description: 'Easy, breathable European flax linen with a relaxed cut that softens with every wear.', stock: 26,
    specs: { Fabric: '100% European flax linen', Fit: 'Relaxed', Colour: 'Cloud white', Care: 'Machine wash cold' },
  },
  {
    id: 'serum-set', name: 'Night Shift Renewal Serum', category: 'Beauty', price: 2290, originalPrice: 2890,
    rating: 4.8, reviewCount: 212, seller: 'Botanica Lab', sellerId: 'botanica', delivery: 'Free delivery · 2 days',
    image: 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=960&q=85', badge: 'CLEAN FORMULA',
    description: 'A gentle overnight blend of niacinamide and botanical peptides for a calm, hydrated morning.', stock: 41,
    specs: { Volume: '30 ml', Skin: 'All skin types', Formula: 'Vegan · fragrance free', Origin: 'Made in India' },
  },
  {
    id: 'trail-runner', name: 'Ridgeline Trail Runner', category: 'Sports', price: 6790, originalPrice: 8490,
    rating: 4.7, reviewCount: 97, seller: 'Pace Collective', sellerId: 'pace', delivery: 'Free delivery · 3 days',
    image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=960&q=85', badge: '−20%',
    description: 'A grippy all-terrain outsole and responsive cushioning, built for long days beyond the pavement.', stock: 14,
    specs: { Drop: '6 mm', Weight: '268 g', Terrain: 'Road · trail', Upper: 'Recycled mesh' },
  },
  {
    id: 'field-notes', name: 'The Field Notes: India, Vol. 02', category: 'Books', price: 890,
    rating: 4.9, reviewCount: 48, seller: 'Little Atlas Press', sellerId: 'atlas', delivery: 'Free delivery · 4 days',
    image: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=960&q=85', badge: 'EDITOR PICK',
    description: 'A considered collection of essays and photographs on the people shaping a new creative India.', stock: 53,
    specs: { Format: 'Hardcover', Pages: '224', Language: 'English', Publisher: 'Little Atlas Press' },
  },
  {
    id: 'road-kit', name: 'Atlas Compact Roadside Kit', category: 'Automotive', price: 2890, originalPrice: 3690,
    rating: 4.5, reviewCount: 65, seller: 'Motorfolk Supply', sellerId: 'motorfolk', delivery: 'Free delivery · 2 days',
    image: 'https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=960&q=85', badge: '−21%',
    description: 'A compact, thoughtfully organised emergency kit for the small surprises of the open road.', stock: 29,
    specs: { Includes: '18 essentials', Case: 'Water-resistant', Warranty: '1 year', Weight: '1.4 kg' },
  },
  {
    id: 'orbit-bag', name: 'Orbit Everyday Crossbody', category: 'Accessories', price: 4590,
    rating: 4.8, reviewCount: 118, seller: 'Objects of Common', sellerId: 'objects', delivery: 'Free delivery · 3 days',
    image: 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=960&q=85', badge: 'LOW IMPACT',
    description: 'A lightweight crossbody with considered pockets and a recycled shell made for city wandering.', stock: 11,
    specs: { Material: 'Recycled nylon', Capacity: '4.5 L', Colour: 'Ink', Warranty: '2 years' },
  },
  {
    id: 'desk-lamp', name: 'Halo Task Light in Warm Brass', category: 'Home', price: 5490, originalPrice: 6990,
    rating: 4.7, reviewCount: 72, seller: 'Form & Field', sellerId: 'formfield', delivery: 'Free delivery · 3 days',
    image: 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=960&q=85', badge: '−21%',
    description: 'A dimmable, low-glare task lamp with a weighted base and a warm, honest material palette.', stock: 16,
    specs: { Light: 'Warm LED · dimmable', Finish: 'Brushed brass', Power: 'USB-C', Warranty: '3 years' },
  },
  {
    id: 'smartwatch', name: 'Fieldwork Active Watch', category: 'Electronics', price: 12990, originalPrice: 15990,
    rating: 4.6, reviewCount: 153, seller: 'Northstar Living', sellerId: 'northstar', delivery: 'Free delivery · Tomorrow',
    image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=960&q=85', badge: '−19%',
    description: 'A resilient daily watch with precise activity tracking, useful recovery insights and a five-day battery.', stock: 22,
    specs: { Battery: '5 days', Display: 'AMOLED', Water: '5 ATM', Warranty: '2 years' },
  },
  {
    id: 'ceramic-vase', name: 'Tidal Ceramic Vessel', category: 'Home', price: 1890,
    rating: 4.9, reviewCount: 39, seller: 'Clay House Studio', sellerId: 'clayhouse', delivery: 'Free delivery · 5 days',
    image: 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?auto=format&fit=crop&w=960&q=85', badge: 'HAND FINISHED',
    description: 'A hand-finished stoneware vessel shaped in small batches by the Clay House studio.', stock: 9,
    specs: { Material: 'Stoneware', Height: '24 cm', Finish: 'Reactive glaze', Origin: 'Jaipur, India' },
  },
]

export const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`