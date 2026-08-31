const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export const money = (n) => inr.format(n ?? 0)

export const shortDate = (iso) =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

export const longDate = (iso) =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

const LABELS = {
  paid: 'Paid',
  pending: 'Payment pending',
  refunded: 'Refunded',
  partially_refunded: 'Partly refunded',
  unfulfilled: 'Unfulfilled',
  fulfilled: 'Fulfilled',
  partial: 'Partly fulfilled',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  active: 'Active',
  draft: 'Draft',
  archived: 'Archived',
  published: 'Published',
}

export const label = (key) => LABELS[key] ?? key

// One lookup for every status pill in the app — colour only where it encodes state.
const THEMES = {
  paid: 'green',
  delivered: 'green',
  fulfilled: 'green',
  active: 'green',
  published: 'green',
  pending: 'orange',
  partial: 'orange',
  partially_refunded: 'orange',
  unfulfilled: 'red',
  cancelled: 'red',
  refunded: 'gray',
  draft: 'gray',
  archived: 'gray',
}

export const statusTheme = (key) => THEMES[key] ?? 'gray'

export function stockTone(qty) {
  if (qty <= 0) return 'text-ink-red-6'
  if (qty <= 5) return 'text-ink-amber-7'
  return 'text-ink-gray-7'
}

// Report figures are read side by side, so they are compacted: ₹4.8L reads at a
// glance where ₹4,82,300 has to be counted.
const inrCompact = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  notation: 'compact',
  maximumFractionDigits: 1,
})

export const compactMoney = (n) => inrCompact.format(n ?? 0)
