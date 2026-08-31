// The product import flow: fixtures and the state one run of it holds. There is
// no backend, so every step reads from here and the timings are simulated.
import { computed, reactive } from 'vue'

export const STEPS = [
  { key: 'source', label: 'Source', icon: 'lucide-plug', hint: 'Where the products live today' },
  { key: 'upload', label: 'Upload', icon: 'lucide-file-up', hint: 'Your spreadsheet' },
  { key: 'map', label: 'Match columns', icon: 'lucide-arrow-left-right', hint: 'Your headings to ours' },
  { key: 'images', label: 'Images', icon: 'lucide-image', hint: 'Photos for each product' },
  { key: 'review', label: 'Review', icon: 'lucide-list-checks', hint: 'Check before saving' },
  { key: 'run', label: 'Import', icon: 'lucide-rocket', hint: 'Create everything' },
]

export const delay = (ms) => ms

export const CSV_COLUMNS = [
  { header: 'Product Name', sample: 'Cotton oversized tee', target: 'item_name', confidence: 'high' },
  { header: 'SKU', sample: 'TEE-OVS-BLK-M', target: 'item_code', confidence: 'high' },
  { header: 'Price (INR)', sample: '1299', target: 'price', confidence: 'high' },
  { header: 'Compare at', sample: '1799', target: 'mrp', confidence: 'medium' },
  { header: 'Qty on hand', sample: '24', target: 'stock', confidence: 'high' },
  { header: 'Category', sample: 'Tops > T-Shirts', target: 'item_group', confidence: 'medium' },
  { header: 'Long description', sample: '100% combed cotton, pre-shrunk', target: 'description', confidence: 'high' },
  { header: 'Image files', sample: 'TEE-OVS-BLK-M-1.jpg', target: 'images', confidence: 'medium' },
  { header: 'Weight (g)', sample: '210', target: 'weight', confidence: 'low' },
  { header: 'Internal notes', sample: 'reorder from Tirupur', target: '', confidence: 'none' },
]

export const TARGET_FIELDS = [
  { label: "Don't import", value: '' },
  { label: 'Product name', value: 'item_name' },
  { label: 'SKU', value: 'item_code' },
  { label: 'Selling price', value: 'price' },
  { label: 'Compare at price', value: 'mrp' },
  { label: 'Stock quantity', value: 'stock' },
  { label: 'Category', value: 'item_group' },
  { label: 'Description', value: 'description' },
  { label: 'Images', value: 'images' },
  { label: 'Weight', value: 'weight' },
  { label: 'Brand', value: 'brand' },
  { label: 'HSN code', value: 'hsn' },
]

export const IMPORT_ROWS = [
  { sku: 'TEE-OVS-BLK-M', name: 'Cotton oversized tee', variant: 'Black / M', group: 'T-Shirts', price: 1299, mrp: 1799, stock: 24, images: 3, icon: 'lucide-shirt' },
  { sku: 'TEE-OVS-SND-L', name: 'Cotton oversized tee', variant: 'Sand / L', group: 'T-Shirts', price: 1299, mrp: 1799, stock: 12, images: 3, icon: 'lucide-shirt' },
  { sku: 'SHT-LIN-WHT-40', name: 'Linen blend shirt', variant: 'White / 40', group: 'Shirts', price: 2499, mrp: 2999, stock: 8, images: 4, icon: 'lucide-shirt' },
  { sku: 'SHT-LIN-OLV-42', name: 'Linen blend shirt', variant: 'Olive / 42', group: 'Shirts', price: 2499, mrp: 2999, stock: 0, images: 4, icon: 'lucide-shirt', issue: { level: 'warning', text: 'Price cell is empty' } },
  { sku: 'DEN-STR-IND-32', name: 'Straight fit denim', variant: 'Indigo / 32', group: 'Jeans', price: 3199, mrp: 3999, stock: 15, images: 5, icon: 'lucide-shopping-bag' },
  { sku: 'DEN-STR-IND-34', name: 'Straight fit denim', variant: 'Indigo / 34', group: 'Jeans', price: 3199, mrp: 3999, stock: 9, images: 5, icon: 'lucide-shopping-bag', issue: { level: 'error', text: 'SKU already used on row 12' } },
  { sku: 'JKT-BMB-NVY-M', name: 'Bomber jacket', variant: 'Navy / M', group: 'Outerwear', price: 4999, mrp: 6499, stock: 6, images: 6, icon: 'lucide-shopping-bag' },
  { sku: 'SNK-LOW-WHT-9', name: 'Low top sneaker', variant: 'White / 9', group: 'Footwear', price: 3899, mrp: 4499, stock: 18, images: 6, icon: 'lucide-footprints' },
  { sku: 'SNK-LOW-WHT-10', name: 'Low top sneaker', variant: 'White / 10', group: 'Footwear', price: 3899, mrp: 4499, stock: 4, images: 6, icon: 'lucide-footprints', issue: { level: 'warning', text: 'Category "Footwear" will be created' } },
  { sku: 'CAP-6PN-BLK', name: 'Six panel cap', variant: 'Black', group: 'Accessories', price: 899, mrp: 1199, stock: 40, images: 2, icon: 'lucide-hard-hat' },
  { sku: 'BLT-LTR-BRN-34', name: 'Leather belt', variant: 'Brown / 34', group: 'Accessories', price: 1499, mrp: 1899, stock: 11, images: 2, icon: 'lucide-circle-dot' },
  { sku: 'DEN-STR-IND-34-2', name: 'Straight fit denim', variant: 'Indigo / 34', group: 'Jeans', price: 3199, mrp: 3999, stock: 9, images: 0, icon: 'lucide-shopping-bag', issue: { level: 'error', text: 'Duplicate of row 6' } },
  { sku: 'SCK-CRW-GRY-3P', name: 'Crew socks, 3 pack', variant: 'Grey', group: 'Accessories', price: 599, mrp: 799, stock: 60, images: 0, icon: 'lucide-circle-dot', issue: { level: 'warning', text: 'No image matched this SKU' } },
  { sku: 'HDY-ZIP-CHR-L', name: 'Zip through hoodie', variant: 'Charcoal / L', group: 'Sweatshirts', price: 2899, mrp: 3499, stock: 7, images: 4, icon: 'lucide-shirt', issue: { level: 'error', text: 'Price "2,899/-" is not a number' } },
]

export const TOTAL_ROWS = 128

export const counts = { errors: 3, warnings: 6, ready: TOTAL_ROWS - 9 }

export const imp = reactive({
  open: false,
  step: 0,
  source: 'csv',
  imagesMode: 'bulk',
  file: null,
  parsing: false,
  parsed: false,
  imagesDone: false,
  running: false,
  finished: false,
  progress: 0,
  log: [],
  reviewFilter: 'all',
  mapping: {},
})

export function resetImport() {
  Object.assign(imp, {
    step: 0,
    source: 'csv',
    imagesMode: 'bulk',
    file: null,
    parsing: false,
    parsed: false,
    imagesDone: false,
    running: false,
    finished: false,
    progress: 0,
    log: [],
    reviewFilter: 'all',
    mapping: Object.fromEntries(CSV_COLUMNS.map((c) => [c.header, c.target])),
  })
}

resetImport()

export function openImport() {
  if (imp.finished) resetImport()
  imp.open = true
}

export function closeImport() {
  imp.open = false
}

export const mappedCount = computed(() => Object.values(imp.mapping).filter(Boolean).length)
