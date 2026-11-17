import { ArrowRight, AudioLines, Bot, Check, Clock3, Sparkles } from 'lucide-react'
import { useState } from 'react'
import type { Product } from '../types'
import { ProductCard } from '../components/ProductCard'
import type { ProductHandlers } from './MarketplacePage'
import { api } from '../api/client'

export function AssistantPage({ products, handlers, onAsk }: { products: Product[]; handlers: ProductHandlers; onAsk: (prompt: string) => void }) {
  const [prompt, setPrompt] = useState('')
  const [asked, setAsked] = useState(false)
  const [aiMessage, setAiMessage] = useState('')
  const [aiMode, setAiMode] = useState('Deterministic local search')
  const send = (value: string) => {
    if (!value.trim()) return
    setPrompt(value)
    setAsked(true)
    onAsk(value)
    if (api.getToken()) {
      void api.aiCopilot(value).then((response) => {
        setAiMessage(response.message)
        setAiMode(response.mode)
      }).catch((error) => setAiMessage(error instanceof Error ? error.message : 'The assistant is unavailable'))
    }
  }

  return (
    <main className="page-content assistant-page">
      <div className="assistant-topline"><div><div className="eyebrow">AURORA INTELLIGENCE · CATALOGUE MODE</div><h1>Your personal<br /><span>shopping orbit.</span></h1><p>A thoughtful starting point for actual catalogue items.</p></div><div className="assistant-status"><span className="status-ring"><Sparkles size={20} /></span><span>{aiMode.toUpperCase()}<br /><strong>Ready to explore</strong></span></div></div>
      <div className="assistant-layout">
        <section className="assistant-chat">
          <div className="chat-header"><span className="assistant-avatar"><Bot size={18} /></span><div><strong>Aurora Stylist</strong><small>Shopping assistant · demo</small></div><span className="demo-chip">DEMO</span></div>
          <div className="assistant-thread">
            <div className="assistant-message"><span className="message-avatar"><Sparkles size={13} /></span><div><p>Hi, I can help you explore our demo catalogue. Tell me what you need, what matters most, or what you'd like to spend.</p><small>Suggestions use local product data only.</small></div></div>
            {asked && <div className="buyer-message"><span>{prompt}</span></div>}
            {asked && <div className="assistant-message"><span className="message-avatar"><Sparkles size={13} /></span><div><p>{aiMessage || 'I matched your request against actual catalogue products. These are the closest options; compare their details before deciding.'}</p><small><Check size={12} /> Catalogue checked just now · {aiMode}</small></div></div>}
            {!asked && <div className="suggestion-list"><span>START WITH A PROMPT</span>{['A thoughtful gift under ₹5,000', 'A 4K TV under ₹50,000', 'Something comfortable for a long run'].map((idea) => <button key={idea} onClick={() => send(idea)}>{idea}<ArrowRight size={13} /></button>)}</div>}
          </div>
          <form className="assistant-composer" onSubmit={(event) => { event.preventDefault(); send(prompt) }}><input value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Tell me what you're looking for..." aria-label="Ask the shopping assistant" /><button type="button" className="voice-button" title="Voice input demo" onClick={() => setPrompt('A thoughtful gift under ₹5,000')}><AudioLines size={17} /></button><button className="composer-send" aria-label="Send message"><ArrowRight size={16} /></button></form>
          <div className="assistant-disclaimer"><Clock3 size={12} /> {aiMode.includes('fallback') ? 'Deterministic local fallback is active; no external AI provider is configured.' : 'AI provider mode: external provider; no autonomous purchase is performed.'}</div>
        </section>
        <aside className="assistant-brief"><div className="eyebrow">HOW IT HELPS</div><h2>Less scrolling.<br />More finding.</h2><p>Describe what matters. The stylist can search and rank products already in the demo catalogue.</p><div className="brief-row"><span>01</span><div><strong>Understands intent</strong><small>Category, budget and key details</small></div></div><div className="brief-row"><span>02</span><div><strong>Explains the match</strong><small>Based on product data we have</small></div></div><div className="brief-row"><span>03</span><div><strong>Keeps it transparent</strong><small>No live web or AI connection</small></div></div><div className="brief-note"><Sparkles size={15} /> Try “55-inch 4K TV, under ₹50,000, 3-year warranty.”</div></aside>
      </div>
      {asked && <section className="section-block assistant-results"><div className="section-heading"><div><div className="eyebrow">LOCAL CATALOGUE MATCHES</div><h2>Closest finds for you.</h2></div><span className="result-count">{products.length} matching products</span></div>{products.length ? <div className="product-grid">{products.slice(0, 4).map((product) => <ProductCard key={product.id} product={product} wished={handlers.wishlist.includes(product.id)} compared={handlers.compared.includes(product.id)} onWishlist={() => handlers.onWishlist(product.id)} onCompare={() => handlers.onCompare(product.id)} onAdd={() => handlers.onAdd(product.id)} onOpen={() => handlers.onOpen(product)} onSeller={() => handlers.onSeller?.(product)} />)}</div> : <div className="empty-results"><strong>No close matches in the demo catalogue.</strong><p>Try a broader category or budget.</p></div>}</section>}
    </main>
  )
}