// The product import flow: shared state for one run of it. Upload/Review/Run read and write the
// real ls_shop.api.admin.imports endpoints; Source and Images stay as they were — the spreadsheet
// source is the only one that exists, and bulk photo matching is still out of scope (see
// docs/commera-open-questions.md).
import { reactive } from 'vue'
import { useAdminAction } from './api'

export const STEPS = [
  { key: 'source', label: 'Source', icon: 'lucide-plug', hint: 'Where the products live today' },
  { key: 'upload', label: 'Upload', icon: 'lucide-file-up', hint: 'Your spreadsheet' },
  { key: 'map', label: 'Match columns', icon: 'lucide-arrow-left-right', hint: 'Your headings to ours' },
  { key: 'images', label: 'Images', icon: 'lucide-image', hint: 'Photos for each product' },
  { key: 'review', label: 'Review', icon: 'lucide-list-checks', hint: 'Check before saving' },
  { key: 'run', label: 'Import', icon: 'lucide-rocket', hint: 'Create everything' },
]

// TARGET_FIELDS/REQUIRED mirror ls_shop.api.admin.imports.FIELD_SYNONYMS/REQUIRED_FIELDS field
// for field — a mismatch here means a column that maps cleanly on the server shows the wrong
// label here, not a functional bug, but it would be a confusing one.
export const TARGET_FIELDS = [
  { label: "Don't import", value: '' },
  { label: 'Product title', value: 'title' },
  { label: 'Collection', value: 'collection' },
  { label: 'Colour', value: 'color' },
  { label: 'Size', value: 'size' },
  { label: 'Compare-at price', value: 'compare_at_price' },
  { label: 'Selling price', value: 'sale_price' },
  { label: 'Stock', value: 'stock' },
]

export const REQUIRED_FIELDS = ['title', 'collection', 'color', 'size']

export const imp = reactive({
  open: false,
  step: 0,
  source: 'csv',
  imagesMode: 'bulk',
  file: null,
  fileUrl: null,
  parsing: false,
  parsed: false,
  imagesDone: false,
  running: false,
  finished: false,
  reviewFilter: 'all',
  mapping: {},
  confidence: {},
  headers: [],
  rows: [],
  counts: { total: 0, ready: 0, warnings: 0, errors: 0, products: 0 },
  created: [],
  runRowErrors: [],
})

export function resetImport() {
  Object.assign(imp, {
    step: 0,
    source: 'csv',
    imagesMode: 'bulk',
    file: null,
    fileUrl: null,
    parsing: false,
    parsed: false,
    imagesDone: false,
    running: false,
    finished: false,
    reviewFilter: 'all',
    mapping: {},
    confidence: {},
    headers: [],
    rows: [],
    counts: { total: 0, ready: 0, warnings: 0, errors: 0, products: 0 },
    created: [],
    runRowErrors: [],
  })
}

resetImport()

export function openImport() {
  if (imp.finished || imp.file) resetImport()
  imp.open = true
}

export function closeImport() {
  imp.open = false
}

// One action, shared by the Upload preview, "Use suggestions" in Map, and the final commit — a
// dry run when called from validate_import, a real write when called from run_import (see RunStep).
export const validateImportAction = useAdminAction('imports.validate_import')

export function applyValidation(data) {
  imp.headers = data.headers
  imp.mapping = data.mapping
  imp.confidence = data.confidence
  imp.rows = data.rows
  imp.counts = data.counts
}
