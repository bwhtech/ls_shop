// Commera sits on top of ERPNext. Company, tax and accounting records live
// there and are read-only here — the merchant never has to learn ERPNext, but
// where the full record matters we hand off to it rather than re-implement it.
const ERPNEXT_URL = 'https://erp.kirana.co'

export const company = {
  name: 'Kirana & Co',
  abbr: 'KC',
  currency: 'INR',
  country: 'India',
  gstin: '29AABCU9603R1ZM',
  email: 'hello@kirana.co',
  phone: '+91 80 4123 9000',
  address: '4th Cross, Indiranagar, Bengaluru 560038',
  fiscalYear: '2026-2027',
  defaultWarehouse: 'Bengaluru warehouse - KC',
}

export function erpnextLink(doctype, name) {
  const slug = doctype.toLowerCase().replace(/\s+/g, '-')
  return `${ERPNEXT_URL}/app/${slug}/${encodeURIComponent(name)}`
}
