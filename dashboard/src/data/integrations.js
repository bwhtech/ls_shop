// Payment gateways and the other services a store plugs in. `brand` is the
// vendor's own colour — the one place in the app where non-semantic colour is
// correct, because it is the thing being recognised. No blurbs, fees or
// coverage claims: the merchant already chose the provider, this screen only
// connects it.
export const paymentGateways = [
  {
    id: 'stripe',
    name: 'Stripe',
    mark: 'S',
    brand: '#635BFF',
    connected: true,
    mode: 'live',
    fields: [
      { key: 'publishable', label: 'Publishable key', placeholder: 'pk_live_…' },
      { key: 'secret', label: 'Secret key', placeholder: 'sk_live_…', secret: true },
      { key: 'webhook', label: 'Webhook signing secret', placeholder: 'whsec_…', secret: true },
    ],
  },
  {
    id: 'razorpay',
    name: 'Razorpay',
    mark: 'R',
    brand: '#0C2451',
    connected: true,
    mode: 'live',
    fields: [
      { key: 'keyId', label: 'Key ID', placeholder: 'rzp_live_…' },
      { key: 'keySecret', label: 'Key secret', placeholder: '••••••••', secret: true },
      { key: 'webhook', label: 'Webhook secret', placeholder: '••••••••', secret: true },
    ],
  },
  {
    id: 'paypal',
    name: 'PayPal',
    mark: 'P',
    brand: '#003087',
    connected: false,
    mode: 'test',
    fields: [
      { key: 'clientId', label: 'Client ID', placeholder: 'A21AA…' },
      { key: 'clientSecret', label: 'Client secret', placeholder: '••••••••', secret: true },
    ],
  },
  {
    id: 'payu',
    name: 'PayU',
    mark: 'U',
    brand: '#A6C307',
    connected: false,
    mode: 'test',
    fields: [
      { key: 'merchantKey', label: 'Merchant key', placeholder: 'gtKFFx' },
      { key: 'salt', label: 'Merchant salt', placeholder: '••••••••', secret: true },
    ],
  },
  {
    id: 'cashfree',
    name: 'Cashfree',
    mark: 'C',
    brand: '#6933FF',
    connected: false,
    mode: 'test',
    fields: [
      { key: 'appId', label: 'App ID', placeholder: 'CF…' },
      { key: 'secretKey', label: 'Secret key', placeholder: '••••••••', secret: true },
    ],
  },
  {
    id: 'paytm',
    name: 'Paytm',
    mark: 'P',
    brand: '#00BAF2',
    connected: false,
    mode: 'test',
    fields: [
      { key: 'mid', label: 'Merchant ID', placeholder: 'KiranaCo123' },
      { key: 'merchantKey', label: 'Merchant key', placeholder: '••••••••', secret: true },
    ],
  },
  {
    id: 'cod',
    name: 'Cash on delivery',
    mark: '₹',
    brand: '#4B5563',
    connected: true,
    mode: 'live',
    fields: [
      { key: 'maxValue', label: 'Maximum order value', placeholder: '5000' },
      { key: 'pincodes', label: 'Serviceable pin codes', placeholder: '560001, 560038, 400001' },
    ],
  },
]

export const appIntegrations = [
  { id: 'shiprocket', name: 'Shiprocket', mark: 'S', brand: '#7B2CBF', category: 'Shipping', blurb: 'Rate shopping and label printing across couriers.', connected: true },
  { id: 'delhivery', name: 'Delhivery', mark: 'D', brand: '#E2231A', category: 'Shipping', blurb: 'Pickup scheduling and tracking webhooks.', connected: false },
  { id: 'ga4', name: 'Google Analytics 4', mark: 'G', brand: '#E37400', category: 'Analytics', blurb: 'Purchase and view-item events from the storefront.', connected: true },
  { id: 'meta', name: 'Meta Pixel', mark: 'M', brand: '#0866FF', category: 'Analytics', blurb: 'Conversions API for Instagram and Facebook ads.', connected: false },
  { id: 'tally', name: 'Tally', mark: 'T', brand: '#1A73E8', category: 'Accounting', blurb: 'Nightly export of invoices and credit notes.', connected: false },
]
