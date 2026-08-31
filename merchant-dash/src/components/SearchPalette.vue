<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { KeyboardShortcut, toast, useKeyboardShortcut } from 'frappe-ui'
import {
  CommandPalette,
  CommandPaletteEmpty,
  CommandPaletteFooter,
  CommandPaletteGroup,
  CommandPaletteInput,
  CommandPaletteItem,
  CommandPaletteList,
} from 'frappe-ui/experimental'
import { collections, customers, orders, products } from '../data/mock'
import { money } from '../data/format'
import { openSettings } from '../ia/settings'
import { search } from '../ia/search'
import { openImport } from '../data/importFlow'

const LIMIT = 5

const router = useRouter()
const query = ref('')

useKeyboardShortcut({
  combo: 'Mod+K',
  description: 'Search',
  handler: () => (search.open = !search.open),
  allowInInput: true,
})

const needle = computed(() => query.value.trim().toLowerCase())

// Records only appear once there is something to match; with an empty query the
// palette is a short list of what you most likely came for.
function match(haystack) {
  return needle.value && haystack.some((text) => String(text ?? '').toLowerCase().includes(needle.value))
}

const productHits = computed(() =>
  needle.value ? products.filter((p) => match([p.title, p.sku, p.vendor])).slice(0, LIMIT) : [],
)

const orderHits = computed(() =>
  needle.value ? orders.filter((o) => match([o.id, o.customer, o.email])).slice(0, LIMIT) : [],
)

const customerHits = computed(() =>
  needle.value ? customers.filter((c) => match([c.name, c.email, c.city])).slice(0, LIMIT) : [],
)

const collectionHits = computed(() =>
  needle.value ? collections.filter((c) => match([c.title])).slice(0, LIMIT) : [],
)

// Everything reachable by keyboard, including the screens the sidebar does not
// list — stock, prices and product types are reached from the catalogue, but
// they are still real destinations.
const GO_TO = [
  { id: 'go-home', label: 'Overview', icon: 'lucide-layout-dashboard', keywords: ['home', 'dashboard'], run: () => router.push('/') },
  { id: 'go-orders', label: 'Orders', icon: 'lucide-shopping-bag', keywords: ['sales'], run: () => router.push('/orders') },
  { id: 'go-customers', label: 'Customers', icon: 'lucide-users', keywords: ['people', 'buyers'], run: () => router.push('/customers') },
  { id: 'go-products', label: 'Products', icon: 'lucide-package', keywords: ['catalogue', 'catalog'], run: () => router.push('/products') },
  { id: 'go-inventory', label: 'Inventory', icon: 'lucide-boxes', keywords: ['stock', 'warehouse'], run: () => router.push('/inventory') },
  { id: 'go-pricing', label: 'Bulk edit prices', icon: 'lucide-indian-rupee', keywords: ['price', 'margin', 'reprice'], run: () => router.push('/pricing') },
  { id: 'go-types', label: 'Product types', icon: 'lucide-shapes', keywords: ['schema', 'fields'], run: () => router.push('/product-types') },
  { id: 'go-revenue', label: 'Revenue report', icon: 'lucide-banknote', keywords: ['analytics', 'sales', 'refunds'], run: () => router.push('/analytics/revenue') },
  { id: 'go-stock-report', label: 'Inventory report', icon: 'lucide-chart-line', keywords: ['analytics', 'dead stock', 'cover'], run: () => router.push('/analytics/inventory') },
  { id: 'go-storefront-report', label: 'Storefront report', icon: 'lucide-globe', keywords: ['analytics', 'sessions', 'funnel'], run: () => router.push('/analytics/storefront') },
  { id: 'go-theme', label: 'Storefront theme', icon: 'lucide-palette', keywords: ['design', 'brand'], run: () => router.push('/storefront/theme') },
]

const CREATE = [
  { id: 'new-product', label: 'New product', icon: 'lucide-plus', keywords: ['add', 'create'], run: () => toast.info('Pick a product type first') },
  { id: 'import', label: 'Import products from CSV', icon: 'lucide-upload', keywords: ['csv', 'bulk', 'shopify', 'migrate'], run: openImport },
  { id: 'receive', label: 'Receive stock', icon: 'lucide-package-plus', keywords: ['inward', 'grn'], run: () => router.push('/inventory') },
]

const SETTINGS = [
  { id: 'settings', label: 'Open settings', icon: 'lucide-settings', keywords: ['preferences', 'config'], run: () => openSettings('general') },
  { id: 'appearance', label: 'Appearance', icon: 'lucide-sun-moon', keywords: ['theme', 'dark', 'light'], run: () => openSettings('appearance') },
  { id: 'payments', label: 'Payment providers', icon: 'lucide-credit-card', keywords: ['stripe', 'razorpay', 'gateway'], run: () => openSettings('payments') },
  { id: 'apps', label: 'Apps and channels', icon: 'lucide-plug', keywords: ['integrations', 'shiprocket'], run: () => openSettings('apps') },
]

const ALL = [
  { label: 'Go to', commands: GO_TO },
  { label: 'Create', commands: CREATE },
  { label: 'Settings', commands: SETTINGS },
]

// Before you type, the palette is a short menu — the five destinations worth a
// shortcut. Dumping every command into an empty query is what made it a wall.
const SUGGESTED = [
  { label: 'Jump to', commands: GO_TO.slice(0, 5) },
  { label: 'Create', commands: CREATE.slice(0, 2) },
]

// The palette's own filter is off so the record rows can be ranked by hand;
// the command rows therefore have to filter here.
const commandGroups = computed(() => {
  if (!needle.value) return SUGGESTED
  return ALL.map((group) => ({
    label: group.label,
    commands: group.commands.filter((command) =>
      [command.label, ...command.keywords].some((text) => text.toLowerCase().includes(needle.value)),
    ),
  })).filter((group) => group.commands.length)
})

function onSelect(value) {
  if (value.kind === 'product') return router.push(`/products/${value.id}`)
  if (value.kind === 'order') return router.push(`/orders/${value.id}`)
  if (value.kind === 'customer') return router.push(`/customers/${value.id}`)
  if (value.kind === 'collection') return router.push('/collections')
  ALL.flatMap((group) => group.commands).find((command) => command.id === value.id)?.run()
}
</script>

<template>
  <CommandPalette
    v-model:open="search.open"
    v-model:query="query"
    class="palette"
    :filterable="false"
    title="Search Commera"
    @select="onSelect"
  >
    <CommandPaletteInput placeholder="Search products, orders and customers, or type a command…" />

    <!-- One scroll region, capped: the list never grows past the fold. -->
    <CommandPaletteList class="max-h-[21rem] py-1.5">
      <CommandPaletteGroup v-if="productHits.length" label="Products">
        <CommandPaletteItem
          v-for="product in productHits"
          :key="product.id"
          :value="{ kind: 'product', id: product.id }"
        >
          <template #prefix>
            <span class="mr-2.5 grid size-4 shrink-0 place-content-center text-sm" aria-hidden="true">
              {{ product.thumb }}
            </span>
          </template>
          {{ product.title }}
          <template #suffix>
            <span class="text-sm text-ink-gray-5">{{ product.sku }}</span>
          </template>
        </CommandPaletteItem>
      </CommandPaletteGroup>

      <CommandPaletteGroup v-if="orderHits.length" label="Orders">
        <CommandPaletteItem
          v-for="order in orderHits"
          :key="order.id"
          :value="{ kind: 'order', id: order.slug }"
        >
          <template #prefix>
            <span class="lucide-shopping-bag mr-2.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          </template>
          {{ order.id }} · {{ order.customer }}
          <template #suffix>
            <span class="text-sm text-ink-gray-5 tabular-nums">{{ money(order.total) }}</span>
          </template>
        </CommandPaletteItem>
      </CommandPaletteGroup>

      <CommandPaletteGroup v-if="customerHits.length" label="Customers">
        <CommandPaletteItem
          v-for="customer in customerHits"
          :key="customer.id"
          :value="{ kind: 'customer', id: customer.id }"
        >
          <template #prefix>
            <span class="lucide-user mr-2.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          </template>
          {{ customer.name }}
          <template #suffix>
            <span class="text-sm text-ink-gray-5">{{ customer.city }}</span>
          </template>
        </CommandPaletteItem>
      </CommandPaletteGroup>

      <CommandPaletteGroup v-if="collectionHits.length" label="Collections">
        <CommandPaletteItem
          v-for="collection in collectionHits"
          :key="collection.id"
          :value="{ kind: 'collection', id: collection.id }"
        >
          <template #prefix>
            <span class="lucide-layers mr-2.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          </template>
          {{ collection.title }}
          <template #suffix>
            <span class="text-sm text-ink-gray-5">{{ collection.count }} products</span>
          </template>
        </CommandPaletteItem>
      </CommandPaletteGroup>

      <CommandPaletteGroup v-for="group in commandGroups" :key="group.label" :label="group.label">
        <CommandPaletteItem
          v-for="command in group.commands"
          :key="command.id"
          :value="{ kind: 'command', id: command.id }"
        >
          <template #prefix>
            <span :class="[command.icon, 'mr-2.5 size-4 shrink-0 text-ink-gray-5']" aria-hidden="true" />
          </template>
          {{ command.label }}
        </CommandPaletteItem>
      </CommandPaletteGroup>
    </CommandPaletteList>

    <CommandPaletteEmpty>
      <span class="lucide-search-x mx-auto mb-2 block size-7 text-ink-gray-4" aria-hidden="true" />
      Nothing matches that.
    </CommandPaletteEmpty>

    <CommandPaletteFooter>
      <span class="flex items-center gap-1.5 text-sm text-ink-gray-5">
        <KeyboardShortcut combo="ArrowUp" /><KeyboardShortcut combo="ArrowDown" /> Navigate
      </span>
      <span class="flex items-center gap-1.5 text-sm text-ink-gray-5">
        <KeyboardShortcut combo="Enter" /> Open
      </span>
      <span class="ml-auto flex items-center gap-1.5 text-sm text-ink-gray-5">
        <KeyboardShortcut combo="Esc" /> Close
      </span>
    </CommandPaletteFooter>
  </CommandPalette>
</template>

<style scoped>
/* The parts style themselves now that their source is scanned; this is the one
   place the palette wants to read tighter than the default — group headings
   closer to the rows they title. Styled through `data-slot`, per the library's
   contract; there are no class props to pass. */
.palette :deep([data-slot='command-palette-group']) {
  margin-top: 0.75rem;
  margin-bottom: 0.25rem;
}

.palette :deep([data-slot='command-palette-group-label']) {
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  line-height: 1rem;
}
</style>
