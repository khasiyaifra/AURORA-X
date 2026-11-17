import { useEffect, useState } from 'react'
import { ArrowRight, Check, CheckCheck, CircleHelp, Languages, MessageCircle, MoreHorizontal, Send, ShieldAlert, UserRound } from 'lucide-react'
import { usePersistentState } from '../hooks/usePersistentState'
import type { Product } from '../types'
import { api } from '../api/client'

type SupportMessage = { id: number; sender: 'buyer' | 'seller' | 'agent'; text: string; time: string }
type SupportTicket = { id: string; subject: string; category: string; priority: 'Urgent' | 'Normal' | 'Low'; status: 'Open' | 'Escalated' | 'Resolved'; agent: string; summary: string }

const initialTickets: SupportTicket[] = [
  { id: 'AX-2048', subject: 'Delivery update needed', category: 'Shipping', priority: 'Urgent', status: 'Escalated', agent: 'Mira Shah', summary: 'Buyer has not received a dispatch scan after the expected ship date.' },
  { id: 'AX-2047', subject: 'Sizing guidance', category: 'Product question', priority: 'Normal', status: 'Open', agent: 'Dev Mehta', summary: 'Buyer asked for a measurement comparison before placing an order.' },
  { id: 'AX-2046', subject: 'Return request', category: 'Returns', priority: 'Low', status: 'Open', agent: 'Unassigned', summary: 'Item arrived in a different colour than the product photos suggested.' },
]
const initialMessages: SupportMessage[] = [
  { id: 1, sender: 'buyer', text: 'Hi, I am considering this for my studio. Is the warm finish closer to brass or copper?', time: '10:24' },
  { id: 2, sender: 'seller', text: 'Hello! It is a soft brushed brass. The product photos are taken in daylight, so the colour is quite true to life.', time: '10:31' },
]

export function SupportPage({ products }: { products: Product[] }) {
  const [messages, setMessages] = usePersistentState<SupportMessage[]>('aurora-chat-messages', initialMessages)
  const [tickets, setTickets] = usePersistentState<SupportTicket[]>('aurora-support-tickets', initialTickets)
  const [message, setMessage] = useState('')
  const [language, setLanguage] = useState('English')
  const [translated, setTranslated] = useState(false)
  const [linkedProduct, setLinkedProduct] = useState(products[0]?.id ?? '')
  const [backendMode, setBackendMode] = useState(false)
  useEffect(() => {
    if (!api.getToken()) return
    void api.supportTickets().then((rows) => {
      setBackendMode(true)
      const realRows = rows as { id: string; subject: string; category: string; priority: 'Urgent' | 'Normal' | 'Low'; status: 'Open' | 'Escalated' | 'Resolved'; resolution_summary: string }[]
      setTickets(realRows.map((row) => ({
        id: row.id,
        subject: row.subject,
        category: row.category,
        priority: row.priority,
        status: row.status,
        agent: 'Assigned agent',
        summary: row.resolution_summary || 'Persistent support ticket',
      })))
    }).catch(() => setBackendMode(false))
  }, [setTickets])
  const selectedProduct = products.find((product) => product.id === linkedProduct)

  const sendMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!message.trim()) return
    setMessages((current) => [...current, { id: Date.now(), sender: 'buyer', text: message.trim(), time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
    setMessage('')
  }
  const updateTicket = (id: string, key: 'priority' | 'status', value: string) => setTickets((current) => current.map((ticket) => ticket.id === id ? { ...ticket, [key]: value } as SupportTicket : ticket))

  return <main className="page-content support-page"><div className="support-heading"><div><div className="eyebrow">{backendMode ? 'AURORA CARE · CONNECTED' : 'AURORA CARE · DEMO DISPATCH'}</div><h1>People helping<br /><span>people.</span></h1><p>One conversation, shared context, and a human when it matters.</p></div><div className="support-active"><span className="live-dot" /> {backendMode ? `${tickets.length} PERSISTENT REQUESTS` : '3 DEMO REQUESTS IN QUEUE'}</div></div>
    <div className="support-layout"><section className="buyer-seller-chat"><div className="chat-header"><span className="chat-person-icon"><UserRound size={17} /></span><div><strong>Studio conversation</strong><small>{selectedProduct?.seller ?? 'Independent seller'} · product inquiry</small></div><button className="icon-button" title="More chat options" aria-label="More chat options"><MoreHorizontal size={17} /></button></div><div className="chat-product-link">{selectedProduct && <><img src={selectedProduct.image} alt="" /><div><span>ABOUT THIS FIND</span><strong>{selectedProduct.name}</strong></div><select value={linkedProduct} onChange={(event) => setLinkedProduct(event.target.value)} aria-label="Change linked product">{products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}</select></>}</div><div className="message-thread">{messages.map((item) => <div key={item.id} className={`message-row ${item.sender}`}><div className="message-author">{item.sender === 'buyer' ? 'You' : item.sender === 'seller' ? 'Seller' : 'Aurora care'} <span>{item.time}</span></div><div className="message-bubble">{translated && item.sender !== 'buyer' ? `[Demo ${language} translation] ${item.text}` : item.text}</div>{item.sender === 'buyer' && <CheckCheck size={13} className="message-seen" />}</div>)}<div className="seller-suggested"><span>SELLER SUGGESTIONS</span><button onClick={() => setMessage('Thanks for checking. I can share a close-up photo if that helps.')}>Offer more detail</button><button onClick={() => setMessage('I can confirm this finish is hand-applied in small batches.')}>Confirm finish</button></div></div><form className="chat-composer" onSubmit={sendMessage}><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Write a message..." aria-label="Write a message" /><button className="composer-send" aria-label="Send message"><Send size={15} /></button></form><div className="chat-controls"><label><Languages size={14} /> Translate demo<select value={language} onChange={(event) => setLanguage(event.target.value)}><option>English</option><option>Hindi</option><option>Tamil</option><option>French</option></select></label><button className={translated ? 'translation-active' : ''} onClick={() => setTranslated(!translated)}>{translated ? 'Show original' : 'Translate messages'}</button></div><div className="translation-disclaimer">Translation preview is a clearly-labelled demo. No translation API is connected.</div></section>
      <aside className="dispatch-panel"><div className="dispatch-title"><div><div className="eyebrow">HUMAN AGENT DISPATCH</div><h2>On the radar.</h2></div><button className="icon-button" aria-label="Support info" title="Demo support queue"><CircleHelp size={16} /></button></div><div className="dispatch-summary"><span>OPEN CASES <strong>{tickets.filter((ticket) => ticket.status !== 'Resolved').length}</strong></span><span>AVG RESPONSE <strong>8 min</strong></span></div><div className="ticket-list">{tickets.map((ticket) => <article key={ticket.id} className={`ticket-card ticket-${ticket.status.toLowerCase()}`}><div className="ticket-topline"><span>{ticket.id}</span><span className={`priority priority-${ticket.priority.toLowerCase()}`}>{ticket.priority}</span></div><h3>{ticket.subject}</h3><p>{ticket.summary}</p><div className="ticket-meta"><span>{ticket.category}</span><span>Agent: {ticket.agent}</span></div><div className="ticket-actions"><select value={ticket.priority} onChange={(event) => updateTicket(ticket.id, 'priority', event.target.value)} aria-label={`Priority for ${ticket.id}`}><option>Urgent</option><option>Normal</option><option>Low</option></select><select value={ticket.status} onChange={(event) => updateTicket(ticket.id, 'status', event.target.value)} aria-label={`Status for ${ticket.id}`}><option>Open</option><option>Escalated</option><option>Resolved</option></select></div><div className={`ticket-status status-${ticket.status.toLowerCase()}`}>{ticket.status === 'Escalated' ? <ShieldAlert size={12} /> : <Check size={12} />}{ticket.status === 'Escalated' ? 'Escalated for follow-up' : ticket.status === 'Resolved' ? 'Marked resolved' : 'Awaiting agent response'}</div></article>)}</div><div className="dispatch-disclaimer"><MessageCircle size={14} /> Queue, assignments and response times are simulated for this prototype.      </div><button className="dispatch-create" onClick={() => {
        if (backendMode) {
          void api.createSupportTicket({
            subject: 'New buyer request',
            category: 'Other',
            description: 'A buyer created a support request from the AURORA X support centre.',
            priority: 'NORMAL',
          }).then(() => api.supportTickets()).then((rows) => {
            const realRows = rows as { id: string; subject: string; category: string; priority: 'Urgent' | 'Normal' | 'Low'; status: 'Open' | 'Escalated' | 'Resolved'; resolution_summary: string }[]
            setTickets(realRows.map((row) => ({ id: row.id, subject: row.subject, category: row.category, priority: row.priority, status: row.status, agent: 'Assigned agent', summary: row.resolution_summary || 'Persistent support ticket' })))
          }).catch(() => undefined)
        } else {
          setTickets((current) => [{ id: `AX-${2050 + current.length}`, subject: 'New buyer request', category: 'General', priority: 'Normal', status: 'Open', agent: 'Unassigned', summary: 'A new demo support request is ready for an agent.' }, ...current])
        }
      }}>{backendMode ? 'Create support request' : 'Create demo request'} <ArrowRight size={14} /></button></aside></div>
  </main>
}