// Report data. The stock figures are derived from the same catalogue the rest
// of the app reads, so a report never disagrees with the screen it links to.
// The time series are static: there is no backend to aggregate.
import { orders, products } from './mock'

export const MONTHS = [
  'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
]

const REVENUE = [
  312000, 358000, 421000, 498000, 366000, 341000, 389000, 412000, 447000, 461000, 455000, 482300,
]
const ORDER_COUNT = [214, 241, 286, 331, 248, 232, 261, 274, 297, 306, 302, 318]

export const revenueByMonth = MONTHS.map((month, i) => {
  const revenue = REVENUE[i]
  const count = ORDER_COUNT[i]
  return {
    month,
    revenue,
    orders: count,
    aov: Math.round(revenue / count),
    // Discounts run with the season; refunds track volume.
    discounts: Math.round(revenue * (0.04 + (i % 4) * 0.012)),
    refunds: Math.round(revenue * (0.02 + (i % 3) * 0.006)),
  }
})

const variants = products.flatMap((p) =>
  p.hasVariants ? p.variants.map((v) => ({ ...v, product: p })) : [{ ...p, product: p, title: '—' }],
)

export const stockValue = variants.reduce((sum, v) => sum + (v.stock ?? 0) * v.price, 0)
export const unitsOnHand = variants.reduce((sum, v) => sum + (v.stock ?? 0), 0)

// The value curve ends on today's real number, so the chart and the stat tile
// above it agree.
export const stockValueByMonth = MONTHS.map((month, i) => ({
  month,
  value: Math.round(stockValue * (0.78 + i * 0.02)),
}))

const soldSkus = new Set(orders.flatMap((o) => o.items.map((item) => item.sku)))
const unitsSoldBySku = orders
  .flatMap((o) => o.items)
  .reduce((acc, item) => acc.set(item.sku, (acc.get(item.sku) ?? 0) + item.qty), new Map())

// Sell-through is what left the shelf against what was on it. Per product, so
// the bars stay readable — per variant it is a hundred bars nobody reads.
export const sellThrough = products.slice(0, 6).map((p) => {
  const units = p.hasVariants ? p.variants : [p]
  const sold = units.reduce((sum, u) => sum + (unitsSoldBySku.get(u.sku) ?? 0), 0)
  const onHand = units.reduce((sum, u) => sum + (u.stock ?? 0), 0)
  return { product: p.title.split(' ').slice(0, 2).join(' '), rate: Math.round((sold / (sold + onHand || 1)) * 100) }
})

export const coverByProduct = sellThrough.map((row) => ({
  product: row.product,
  days: Math.max(6, Math.round(1800 / (row.rate + 4))),
}))

// Nothing sold in the last 30 days, worth the most money. This is the report's
// whole point: capital sitting still.
export const deadStock = variants
  .filter((v) => (v.stock ?? 0) > 0 && !soldSkus.has(v.sku))
  .map((v, i) => ({
    product: v.product.title,
    variant: v.title,
    sku: v.sku,
    stock: v.stock,
    lastSold: 31 + ((i * 13) % 60),
    value: v.stock * v.price,
  }))
  .sort((a, b) => b.value - a.value)
  .slice(0, 6)

const SESSIONS = [
  28400, 31200, 38600, 46100, 33800, 31900, 35700, 37400, 40100, 41800, 42600, 44600,
]

export const sessionsByMonth = MONTHS.map((month, i) => ({ month, sessions: SESSIONS[i] }))

export const channels = [
  { channel: 'Direct', sessions: 15600 },
  { channel: 'Google', sessions: 12800 },
  { channel: 'Instagram', sessions: 8700 },
  { channel: 'WhatsApp', sessions: 4300 },
  { channel: 'Email', sessions: 3200 },
]

export const funnel = [
  { stage: 'Sessions', count: 44600 },
  { stage: 'Product viewed', count: 21400 },
  { stage: 'Added to cart', count: 6380 },
  { stage: 'Checkout started', count: 2920 },
  { stage: 'Paid', count: 1294 },
]

export const topPages = [
  { page: '/', views: 18400, conversion: 3.1 },
  { page: '/collections/new-arrivals', views: 9200, conversion: 4.4 },
  { page: '/products/everyday-linen-shirt', views: 6100, conversion: 6.2 },
  { page: '/collections/books', views: 4800, conversion: 2.7 },
  { page: '/pages/journal', views: 2600, conversion: 0.4 },
]

export const searchTerms = [
  { term: 'linen shirt', searches: 640, results: 12 },
  { term: 'gift wrap', searches: 310, results: 0 },
  { term: 'atomic habits', searches: 288, results: 3 },
  { term: 'coffee filter papers', searches: 194, results: 0 },
  { term: 'socks', searches: 176, results: 8 },
  { term: 'kannada books', searches: 121, results: 0 },
]
