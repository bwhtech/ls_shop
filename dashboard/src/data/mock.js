// Static mock data for the prototype. No backend — everything here is in-memory
// and reset on reload.
import { reactive } from 'vue'

// One store, one warehouse: stock is a single number per variant, and no
// screen has to ask "where".
export const locations = [{ id: 'loc-1', name: 'Bengaluru warehouse', code: 'BLR' }]

// A ProductType carries the field schema that makes the catalog generic:
// a book and a t-shirt share the core fields and differ only in `fields`.
export const productTypes = [
  {
    id: 'book',
    name: 'Book',
    icon: 'lucide-book-open',
    fields: [
      { key: 'author', label: 'Author', type: 'text' },
      { key: 'isbn', label: 'ISBN', type: 'text' },
      { key: 'publisher', label: 'Publisher', type: 'text' },
      { key: 'pages', label: 'Pages', type: 'number' },
      { key: 'language', label: 'Language', type: 'select', options: ['English', 'Hindi', 'Kannada'] },
    ],
  },
  {
    id: 'apparel',
    name: 'Apparel',
    icon: 'lucide-shirt',
    fields: [
      { key: 'material', label: 'Material', type: 'text' },
      { key: 'fit', label: 'Fit', type: 'select', options: ['Regular', 'Slim', 'Oversized'] },
      { key: 'care', label: 'Care instructions', type: 'textarea' },
    ],
  },
  {
    id: 'digital',
    name: 'Digital',
    icon: 'lucide-cloud-download',
    fields: [
      { key: 'file', label: 'File', type: 'text' },
      { key: 'license', label: 'License', type: 'select', options: ['Personal', 'Commercial'] },
      { key: 'downloads', label: 'Download limit', type: 'number' },
    ],
  },
  {
    id: 'homeware',
    name: 'Homeware',
    icon: 'lucide-lamp',
    fields: [
      { key: 'dimensions', label: 'Dimensions', type: 'text' },
      { key: 'weight', label: 'Weight (g)', type: 'number' },
      { key: 'origin', label: 'Country of origin', type: 'text' },
    ],
  },
]

// Attributes are global and reusable — options on a product point at these.
export const attributes = [
  { id: 'size', name: 'Size', values: ['XS', 'S', 'M', 'L', 'XL'], usedBy: 6 },
  { id: 'color', name: 'Color', values: ['Black', 'White', 'Sand', 'Olive', 'Indigo'], usedBy: 5 },
  { id: 'format', name: 'Format', values: ['Paperback', 'Hardcover', 'Ebook'], usedBy: 3 },
  { id: 'material', name: 'Material', values: ['Cotton', 'Linen', 'Wool'], usedBy: 2 },
  { id: 'volume', name: 'Volume', values: ['250ml', '500ml', '1L'], usedBy: 1 },
]

export const collections = [
  { id: 'col-1', title: 'New arrivals', rule: 'smart', count: 12, condition: 'Created in last 30 days' },
  { id: 'col-2', title: 'Staff picks', rule: 'manual', count: 6, condition: '—' },
  { id: 'col-3', title: 'Under ₹999', rule: 'smart', count: 9, condition: 'Price < 999' },
  { id: 'col-4', title: 'Monsoon edit', rule: 'manual', count: 4, condition: '—' },
  { id: 'col-5', title: 'Clearance', rule: 'smart', count: 7, condition: 'Tagged clearance' },
]

function cartesian(options) {
  return options.reduce(
    (acc, option) => acc.flatMap((combo) => option.values.map((v) => [...combo, { name: option.name, value: v }])),
    [[]],
  )
}

// Deterministic pseudo-random so the prototype looks the same on every reload.
function seeded(seed) {
  let s = seed
  return () => {
    s = (s * 1103515245 + 12345) % 2147483648
    return s / 2147483648
  }
}

function buildVariants(product) {
  if (!product.options?.length) return []
  const rand = seeded(product.title.length * 977 + product.id.length * 31)
  return cartesian(product.options).map((combo, i) => {
    const suffix = combo.map((c) => c.value.slice(0, 3).toUpperCase()).join('-')
    const stock = Math.round(rand() * 40)
    return {
      id: `${product.id}-v${i + 1}`,
      productId: product.id,
      title: combo.map((c) => c.value).join(' / '),
      combo,
      sku: `${product.sku}-${suffix}`,
      price: product.price + (combo.some((c) => c.value === 'Hardcover') ? 400 : 0) + (combo.some((c) => c.value === 'XL') ? 100 : 0),
      compareAt: product.compareAt,
      stock,
      committed: Math.min(stock, Math.round(rand() * 4)),
      thumb: product.thumb,
      // Photos are per variant: a colour swap is a different picture, and the
      // storefront swaps the image when a shopper picks one.
      images: i === 0 ? 2 : rand() > 0.55 ? 1 : 0,
      barcode: `89${String(9000000 + i * 137 + product.title.length).slice(0, 9)}`,
    }
  })
}

const rawProducts = [
  {
    id: 'p-1', title: 'The Midnight Library', type: 'book', status: 'active', thumb: '📗',
    vendor: 'Canongate', sku: 'BK-MIDLIB', price: 499, compareAt: 699, tags: ['fiction', 'bestseller'],
    collections: ['col-1', 'col-2'], updated: '2026-08-28',
    typeFields: { author: 'Matt Haig', isbn: '9781786892737', publisher: 'Canongate', pages: 288, language: 'English' },
    options: [{ name: 'Format', values: ['Paperback', 'Hardcover', 'Ebook'] }],
    description: 'Between life and death there is a library, and within that library the shelves go on forever.',
  },
  {
    id: 'p-2', title: 'Everyday Linen Shirt', type: 'apparel', status: 'active', thumb: '👕',
    vendor: 'Loom & Co', sku: 'AP-LINSH', price: 2499, compareAt: 2999, tags: ['summer', 'staff-pick'],
    collections: ['col-1', 'col-2', 'col-4'], updated: '2026-08-30',
    typeFields: { material: '100% European linen', fit: 'Regular', care: 'Cold machine wash. Line dry in shade.' },
    options: [
      { name: 'Size', values: ['S', 'M', 'L', 'XL'] },
      { name: 'Color', values: ['White', 'Sand', 'Olive'] },
    ],
    description: 'A breathable everyday shirt cut from washed European linen.',
  },
  {
    id: 'p-3', title: 'Ceramic Pour-Over Set', type: 'homeware', status: 'active', thumb: '☕️',
    vendor: 'Kiln Studio', sku: 'HW-POUR', price: 3200, compareAt: null, tags: ['coffee'],
    collections: ['col-2'], updated: '2026-08-19',
    typeFields: { dimensions: '14 × 12 × 15 cm', weight: 820, origin: 'India' },
    options: [{ name: 'Color', values: ['White', 'Black'] }],
    description: 'Hand-thrown dripper and carafe, fired at 1260°C.',
  },
  {
    id: 'p-4', title: 'Design Systems Handbook (PDF)', type: 'digital', status: 'active', thumb: '📄',
    vendor: 'Self', sku: 'DG-DSHB', price: 899, compareAt: null, tags: ['design'],
    collections: ['col-3'], updated: '2026-08-12',
    typeFields: { file: 'design-systems-handbook-v3.pdf', license: 'Personal', downloads: 3 },
    options: [],
    description: '180 pages on building and maintaining a component library.',
  },
  {
    id: 'p-5', title: 'Heavyweight Cotton Tee', type: 'apparel', status: 'active', thumb: '🧵',
    vendor: 'Loom & Co', sku: 'AP-HWTEE', price: 1299, compareAt: 1599, tags: ['basics'],
    collections: ['col-1', 'col-3'], updated: '2026-08-29',
    typeFields: { material: '240 GSM combed cotton', fit: 'Oversized', care: 'Wash inside out.' },
    options: [
      { name: 'Size', values: ['S', 'M', 'L', 'XL'] },
      { name: 'Color', values: ['Black', 'White', 'Indigo'] },
    ],
    description: 'Boxy, garment-dyed, gets better with every wash.',
  },
  {
    id: 'p-6', title: 'Atomic Habits', type: 'book', status: 'active', thumb: '📙',
    vendor: 'Penguin', sku: 'BK-ATHAB', price: 599, compareAt: null, tags: ['bestseller', 'non-fiction'],
    collections: ['col-1'], updated: '2026-08-27',
    typeFields: { author: 'James Clear', isbn: '9781847941831', publisher: 'Penguin', pages: 320, language: 'English' },
    options: [{ name: 'Format', values: ['Paperback', 'Hardcover'] }],
    description: 'An easy and proven way to build good habits and break bad ones.',
  },
  {
    id: 'p-7', title: 'Brass Reading Lamp', type: 'homeware', status: 'draft', thumb: '💡',
    vendor: 'Kiln Studio', sku: 'HW-LAMP', price: 5400, compareAt: null, tags: [],
    collections: [], updated: '2026-08-31',
    typeFields: { dimensions: '20 × 20 × 42 cm', weight: 1900, origin: 'India' },
    options: [],
    description: 'Solid brass, dimmable, warm 2700K bulb included.',
  },
  {
    id: 'p-8', title: 'Merino Crew Socks', type: 'apparel', status: 'active', thumb: '🧦',
    vendor: 'Loom & Co', sku: 'AP-SOCK', price: 649, compareAt: 799, tags: ['basics', 'clearance'],
    collections: ['col-3', 'col-5'], updated: '2026-08-22',
    typeFields: { material: 'Merino wool blend', fit: 'Regular', care: 'Hand wash.' },
    options: [
      { name: 'Size', values: ['S', 'M', 'L'] },
      { name: 'Color', values: ['Black', 'Sand'] },
    ],
    description: 'Cushioned footbed, seamless toe.',
  },
  {
    id: 'p-9', title: 'Cold Brew Concentrate', type: 'homeware', status: 'active', thumb: '🧊',
    vendor: 'Third Wave', sku: 'HW-CBRW', price: 749, compareAt: null, tags: ['coffee'],
    collections: ['col-4'], updated: '2026-08-25',
    typeFields: { dimensions: '8 × 8 × 22 cm', weight: 1100, origin: 'India' },
    options: [{ name: 'Volume', values: ['250ml', '500ml', '1L'] }],
    description: '18-hour steep, 1:4 dilution.',
  },
  {
    id: 'p-10', title: 'Sapiens', type: 'book', status: 'archived', thumb: '📕',
    vendor: 'Vintage', sku: 'BK-SAPNS', price: 699, compareAt: null, tags: ['non-fiction'],
    collections: [], updated: '2026-07-30',
    typeFields: { author: 'Yuval Noah Harari', isbn: '9780099590088', publisher: 'Vintage', pages: 512, language: 'English' },
    options: [],
    description: 'A brief history of humankind.',
  },
  {
    id: 'p-11', title: 'Canvas Weekender Bag', type: 'apparel', status: 'active', thumb: '🎒',
    vendor: 'Loom & Co', sku: 'AP-WKND', price: 4200, compareAt: 4800, tags: ['travel', 'staff-pick'],
    collections: ['col-2', 'col-4'], updated: '2026-08-26',
    typeFields: { material: '18oz waxed canvas', fit: 'Regular', care: 'Spot clean only.' },
    options: [{ name: 'Color', values: ['Olive', 'Black'] }],
    description: 'Waxed canvas, leather straps, 38L.',
  },
  {
    id: 'p-12', title: 'Icon Pack — 400 line icons', type: 'digital', status: 'active', thumb: '🗂️',
    vendor: 'Self', sku: 'DG-ICON', price: 1499, compareAt: null, tags: ['design'],
    collections: ['col-1'], updated: '2026-08-18',
    typeFields: { file: 'iconpack-line-v2.zip', license: 'Commercial', downloads: 10 },
    options: [],
    description: 'SVG + Figma library, 24px grid.',
  },
]

// Reactive so an edit on the product screen — an option added, a price set in
// the variant matrix — is visible everywhere that product is read.
export const products = reactive(
  rawProducts.map((p) => {
    const variants = buildVariants(p)
    const stock = variants.length ? variants.reduce((s, v) => s + v.stock, 0) : Math.round(30 + p.title.length * 3)
    return { ...p, variants, stock, hasVariants: variants.length > 0 }
  }),
)

// Options are the axes; variants are every combination of them. Changing an
// axis rebuilds the matrix, so the two can never drift apart.
export function regenerateVariants(product) {
  const variants = buildVariants(product)
  product.variants = variants
  product.hasVariants = variants.length > 0
  if (variants.length) product.stock = variants.reduce((s, v) => s + v.stock, 0)
}

export const customers = [
  { id: 'c-1', name: 'Aarti Mehta', email: 'aarti@example.com', city: 'Bengaluru', orders: 7, spend: 24800, since: '2025-02-11' },
  { id: 'c-2', name: 'Devansh Rao', email: 'devansh@example.com', city: 'Pune', orders: 3, spend: 8100, since: '2025-11-02' },
  { id: 'c-3', name: 'Farida Sheikh', email: 'farida@example.com', city: 'Mumbai', orders: 12, spend: 51200, since: '2024-08-19' },
  { id: 'c-4', name: 'Nikhil Nair', email: 'nikhil@example.com', city: 'Kochi', orders: 1, spend: 1299, since: '2026-07-04' },
  { id: 'c-5', name: 'Sana Kapoor', email: 'sana@example.com', city: 'Delhi', orders: 5, spend: 17600, since: '2025-06-23' },
  { id: 'c-6', name: 'Rohit Bhatia', email: 'rohit@example.com', city: 'Jaipur', orders: 2, spend: 5600, since: '2026-01-30' },
  { id: 'c-7', name: 'Meera Iyer', email: 'meera@example.com', city: 'Chennai', orders: 9, spend: 33400, since: '2024-12-01' },
  { id: 'c-8', name: 'Zoya Ahmed', email: 'zoya@example.com', city: 'Hyderabad', orders: 4, spend: 12250, since: '2025-09-14' },
]

const paymentStates = ['paid', 'paid', 'paid', 'pending', 'refunded', 'partially_refunded']
const fulfillStates = ['unfulfilled', 'fulfilled', 'fulfilled', 'partial', 'delivered', 'cancelled']

function buildOrders() {
  const rand = seeded(42)
  const out = []
  for (let i = 0; i < 24; i++) {
    const customer = customers[Math.floor(rand() * customers.length)]
    const lineCount = 1 + Math.floor(rand() * 3)
    const items = []
    for (let j = 0; j < lineCount; j++) {
      const product = products[Math.floor(rand() * products.length)]
      const variant = product.variants.length
        ? product.variants[Math.floor(rand() * product.variants.length)]
        : null
      const qty = 1 + Math.floor(rand() * 2)
      items.push({
        productId: product.id,
        title: product.title,
        variantTitle: variant?.title ?? null,
        sku: variant?.sku ?? product.sku,
        thumb: product.thumb,
        qty,
        price: variant?.price ?? product.price,
      })
    }
    const subtotal = items.reduce((s, it) => s + it.price * it.qty, 0)
    const shipping = subtotal > 3000 ? 0 : 79
    const tax = Math.round(subtotal * 0.05)
    const payment = paymentStates[Math.floor(rand() * paymentStates.length)]
    // An unpaid order has not shipped: keep the two states coherent so the
    // order page can read one progression out of them.
    const settled = ['paid', 'refunded', 'partially_refunded'].includes(payment)
    const fulfillment = settled
      ? fulfillStates[Math.floor(rand() * fulfillStates.length)]
      : rand() > 0.85
        ? 'cancelled'
        : 'unfulfilled'
    const day = 31 - Math.floor(i * 1.2)
    out.push({
      id: `#${1420 - i}`,
      slug: String(1420 - i),
      customerId: customer.id,
      customer: customer.name,
      email: customer.email,
      date: `2026-08-${String(Math.max(1, day)).padStart(2, '0')}`,
      time: `${String(9 + (i % 11)).padStart(2, '0')}:${String((i * 7) % 60).padStart(2, '0')}`,
      payment,
      fulfillment,
      channel: rand() > 0.75 ? 'POS' : 'Online store',
      location: locations[0].name,
      items,
      subtotal,
      shipping,
      tax,
      total: subtotal + shipping + tax,
      address: { line1: '4th Cross, Indiranagar', city: customer.city, pin: '560038', country: 'India' },
      tags: rand() > 0.7 ? ['priority'] : [],
      note: rand() > 0.8 ? 'Customer asked for gift wrap.' : '',
    })
  }
  return out
}

export const orders = buildOrders()

// One cancelled order so that path of the progress tracker is visible in the
// prototype rather than left to chance in the seed.
Object.assign(orders[7], { payment: 'refunded', fulfillment: 'cancelled' })

export const inventory = products.flatMap((p) =>
  (p.hasVariants ? p.variants : [{ id: `${p.id}-v0`, productId: p.id, title: '—', sku: p.sku, stock: p.stock, committed: 2, thumb: p.thumb, price: p.price }]).flatMap(
    (v, idx) =>
      locations.map((loc, li) => ({
        id: `${v.id}-${loc.id}`,
        productId: p.id,
        productTitle: p.title,
        variantId: v.id,
        variantTitle: v.title,
        sku: v.sku,
        thumb: p.thumb,
        locationId: loc.id,
        location: loc.name,
        onHand: li === 0 ? v.stock : Math.max(0, Math.round(v.stock / 3) - idx),
        committed: li === 0 ? v.committed ?? 0 : 0,
      })),
  ),
)

export const adjustments = [
  { id: 'adj-1', date: '2026-08-30', sku: 'AP-LINSH-M-SAN', product: 'Everyday Linen Shirt', delta: +24, reason: 'Received', by: 'Aarti' },
  { id: 'adj-2', date: '2026-08-29', sku: 'BK-ATHAB-PAP', product: 'Atomic Habits', delta: -3, reason: 'Damaged', by: 'Devansh' },
  { id: 'adj-3', date: '2026-08-28', sku: 'AP-HWTEE-L-BLA', product: 'Heavyweight Cotton Tee', delta: +50, reason: 'Received', by: 'Aarti' },
  { id: 'adj-4', date: '2026-08-27', sku: 'HW-POUR-WHI', product: 'Ceramic Pour-Over Set', delta: -2, reason: 'Stock count', by: 'Meera' },
  { id: 'adj-5', date: '2026-08-25', sku: 'AP-SOCK-M-BLA', product: 'Merino Crew Socks', delta: +100, reason: 'Received', by: 'Aarti' },
]

export const storefrontMenus = [
  {
    id: 'main',
    name: 'Main navigation',
    items: [
      { id: 'm1', label: 'Shop', target: '/collections/all', children: [
        { id: 'm1a', label: 'New arrivals', target: '/collections/new-arrivals' },
        { id: 'm1b', label: 'Books', target: '/collections/books' },
        { id: 'm1c', label: 'Apparel', target: '/collections/apparel' },
      ] },
      { id: 'm2', label: 'Collections', target: '/collections', children: [] },
      { id: 'm3', label: 'Journal', target: '/pages/journal', children: [] },
      { id: 'm4', label: 'About', target: '/pages/about', children: [] },
    ],
  },
  {
    id: 'footer',
    name: 'Footer',
    items: [
      { id: 'f1', label: 'Shipping policy', target: '/policies/shipping', children: [] },
      { id: 'f2', label: 'Returns', target: '/policies/returns', children: [] },
      { id: 'f3', label: 'Contact', target: '/pages/contact', children: [] },
    ],
  },
]

export const storefrontPages = [
  { id: 'sp-1', title: 'Home', slug: '/', status: 'published', sections: ['Hero', 'Featured collection', 'Editorial', 'Newsletter'], updated: '2026-08-30' },
  { id: 'sp-2', title: 'About', slug: '/pages/about', status: 'published', sections: ['Rich text', 'Image with text'], updated: '2026-08-11' },
  { id: 'sp-3', title: 'Journal', slug: '/pages/journal', status: 'published', sections: ['Post list'], updated: '2026-08-20' },
  { id: 'sp-4', title: 'Shipping policy', slug: '/policies/shipping', status: 'published', sections: ['Rich text'], updated: '2026-06-02' },
  { id: 'sp-5', title: 'Size guide', slug: '/pages/size-guide', status: 'draft', sections: ['Rich text', 'Table'], updated: '2026-08-29' },
  { id: 'sp-6', title: 'Returns', slug: '/policies/returns', status: 'published', sections: ['Rich text'], updated: '2026-05-18' },
  { id: 'sp-7', title: 'Privacy policy', slug: '/policies/privacy', status: 'published', sections: ['Rich text'], updated: '2026-04-02' },
  { id: 'sp-8', title: 'Terms of service', slug: '/policies/terms', status: 'published', sections: ['Rich text'], updated: '2026-04-02' },
  { id: 'sp-9', title: 'Contact', slug: '/pages/contact', status: 'published', sections: ['Form', 'Map'], updated: '2026-07-21' },
  { id: 'sp-10', title: 'Store locator', slug: '/pages/stores', status: 'published', sections: ['Map', 'Rich text'], updated: '2026-07-09' },
  { id: 'sp-11', title: 'Gift cards', slug: '/pages/gift-cards', status: 'draft', sections: ['Hero', 'Rich text'], updated: '2026-08-26' },
  { id: 'sp-12', title: 'Wholesale', slug: '/pages/wholesale', status: 'draft', sections: ['Form', 'Rich text'], updated: '2026-08-14' },
  { id: 'sp-13', title: 'Care guide', slug: '/pages/care', status: 'published', sections: ['Rich text', 'Image with text'], updated: '2026-06-27' },
  { id: 'sp-14', title: 'Diwali edit', slug: '/pages/diwali', status: 'draft', sections: ['Hero', 'Featured collection'], updated: '2026-08-31' },
]

export const kpis = [
  { key: 'revenue', label: 'Revenue', value: '₹4,82,300', delta: '+12.4%', trend: 'up' },
  { key: 'orders', label: 'Orders', value: '318', delta: '+6.1%', trend: 'up' },
  { key: 'aov', label: 'Avg. order value', value: '₹1,516', delta: '-2.3%', trend: 'down' },
  { key: 'conversion', label: 'Conversion', value: '2.8%', delta: '+0.4pt', trend: 'up' },
]

export const salesSeries = [
  22, 31, 28, 44, 39, 52, 47, 61, 55, 49, 63, 71, 66, 58, 74, 81, 69, 77, 85, 92, 79, 88, 96, 104, 91, 99, 87, 112, 105, 118, 124,
]

// Analytics and accounting services the prototype shows but does not yet talk to.
// Shipping carriers used to live here too. They are real now and come from the server
// (see data/integrations.js), so listing them here as well would contradict the Shipping
// tab, which reads the site's actual carriers.
export const appIntegrations = [
  { id: 'ga4', name: 'Google Analytics 4', mark: 'G', brand: '#E37400', category: 'Analytics', blurb: 'Purchase and view-item events from the storefront.', connected: false },
  { id: 'meta', name: 'Meta Pixel', mark: 'M', brand: '#0866FF', category: 'Analytics', blurb: 'Conversions API for Instagram and Facebook ads.', connected: false },
  { id: 'tally', name: 'Tally', mark: 'T', brand: '#1A73E8', category: 'Accounting', blurb: 'Nightly export of invoices and credit notes.', connected: false },
]
