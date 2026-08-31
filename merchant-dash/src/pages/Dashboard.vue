<script setup>
import { computed } from 'vue'
import { Avatar, Button } from 'frappe-ui'
import { LineChart } from 'frappe-ui/charts'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import StatusBadge from '../components/StatusBadge.vue'
import Thumb from '../components/Thumb.vue'
import { inventory, kpis, orders, products } from '../data/mock'
import { revenueByMonth } from '../data/analytics'
import { compactMoney, money, shortDate } from '../data/format'
import { ia } from '../ia/store'

const unfulfilled = computed(() => orders.filter((o) => o.fulfillment === 'unfulfilled').length)
const unpaid = computed(() => orders.filter((o) => o.payment === 'pending').length)
const lowStock = computed(() => inventory.filter((row) => row.onHand <= 4).length)
const draftCount = computed(() => products.filter((p) => p.status === 'draft').length)

// Only what is actually waiting: a block that lists a zero is a block that
// teaches you to stop reading it.
const attention = computed(() =>
  [
    {
      icon: 'lucide-package-open',
      title: `${unfulfilled.value} orders to fulfil`,
      note: 'Oldest has been waiting 3 days',
      action: 'Fulfil orders',
      to: '/orders',
    },
    {
      icon: 'lucide-hourglass',
      title: `${unpaid.value} ${unpaid.value === 1 ? 'payment' : 'payments'} pending`,
      note: 'Bank transfer not yet reconciled',
      action: 'Review',
      to: '/orders',
    },
    {
      icon: 'lucide-triangle-alert',
      title: `${lowStock.value} ${lowStock.value === 1 ? 'variant' : 'variants'} low on stock`,
      note: 'At or below four units in a location',
      action: 'Restock',
      to: '/inventory',
    },
    {
      icon: 'lucide-file-pen-line',
      title: `${draftCount.value} ${draftCount.value === 1 ? 'product' : 'products'} in draft`,
      note: 'Not visible on the storefront yet',
      action: 'Open catalogue',
      to: '/products',
    },
  ].filter((row) => !row.title.startsWith('0 ')),
)

const recent = computed(() => orders.slice(0, 5))

const soldBySku = orders
  .flatMap((o) => o.items)
  .reduce((acc, item) => acc.set(item.sku, (acc.get(item.sku) ?? 0) + item.qty), new Map())

const topProducts = computed(() =>
  products
    .filter((p) => p.status === 'active')
    .map((p) => {
      const units = p.hasVariants ? p.variants : [p]
      const sold = units.reduce((sum, u) => sum + (soldBySku.get(u.sku) ?? 0), 0)
      return {
        ...p,
        sold,
        revenue: units.reduce((sum, u) => sum + (soldBySku.get(u.sku) ?? 0) * u.price, 0),
        onHand: units.reduce((sum, u) => sum + (u.stock ?? 0), 0),
      }
    })
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 4),
)
</script>

<template>
  <AppPageHeader title="Overview">
    <template #actions>
      <Button label="Add product" icon-left="lucide-plus" variant="solid" theme="gray" route="/products" />
    </template>
  </AppPageHeader>

  <PageBody width="narrow">
    <div class="grid grid-cols-2 rounded-5 border border-outline-gray-1 sm:grid-cols-4 sm:divide-x sm:divide-outline-gray-2">
      <div v-for="kpi in kpis" :key="kpi.key" class="px-4 py-3.5">
        <p class="text-sm text-ink-gray-5">{{ kpi.label }}</p>
        <p class="mt-1 text-2xl text-ink-gray-9 tabular-nums">{{ kpi.value }}</p>
        <p class="mt-1 text-sm" :class="kpi.trend === 'up' ? 'text-ink-green-6' : 'text-ink-red-6'">
          {{ kpi.delta }} vs. last period
        </p>
      </div>
    </div>

    <section v-if="attention.length" class="mt-6">
      <h2 class="text-lg-semibold text-ink-gray-8">Needs attention</h2>
      <div class="mt-2 divide-y divide-outline-gray-1 rounded-5 border border-outline-gray-1">
        <div v-for="row in attention" :key="row.title" class="flex items-center gap-3 px-4 py-3">
          <span class="grid size-8 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-ink-gray-6">
            <span :class="[row.icon, 'size-4']" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-base text-ink-gray-8">{{ row.title }}</p>
            <p class="mt-1 truncate text-sm text-ink-gray-5">{{ row.note }}</p>
          </div>
          <Button :label="row.action" :route="row.to" />
        </div>
      </div>
    </section>

    <section class="mt-6 rounded-5 border border-outline-gray-1 p-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg-semibold text-ink-gray-8">Revenue</h2>
        <div class="flex items-center gap-2">
          <span class="text-sm text-ink-gray-5">Last 12 months</span>
          <Button
            variant="ghost"
            label="Revenue report"
            icon-right="lucide-arrow-right"
            route="/analytics/revenue"
          />
        </div>
      </div>
      <div class="h-72">
        <LineChart :data="revenueByMonth" x="month" :y="['revenue']" />
      </div>
    </section>

    <section class="mt-6 rounded-5 border border-outline-gray-1">
      <div class="flex items-center justify-between px-4 py-3">
        <h2 class="text-lg-semibold text-ink-gray-8">Recent orders</h2>
        <Button variant="ghost" label="View all" icon-right="lucide-arrow-right" route="/orders" />
      </div>
      <div class="overflow-x-auto px-2 pb-2">
        <List
          class="min-w-[34rem]"
          :columns="['6rem', 'minmax(0,1fr)', '9rem', '7rem', '6rem']"
          :row-height="Math.max(ia.density, 48)"
        >
          <ListHeader>
            <ListHeaderCell>Order</ListHeaderCell>
            <ListHeaderCell>Customer</ListHeaderCell>
            <ListHeaderCell>Status</ListHeaderCell>
            <ListHeaderCell>Total</ListHeaderCell>
            <ListHeaderCell>Placed</ListHeaderCell>
          </ListHeader>
          <ListRows :items="recent" row-key="id" v-slot="{ item }">
            <ListRow :to="`/orders/${item.slug}`" :value="item.id">
              <ListCell>
                <span class="text-base text-ink-gray-5 tabular-nums">{{ item.id }}</span>
              </ListCell>
              <ListCell>
                <div class="flex min-w-0 items-center gap-2">
                  <Avatar :label="item.customer" size="sm" />
                  <span class="truncate text-base text-ink-gray-8">{{ item.customer }}</span>
                </div>
              </ListCell>
              <ListCell>
                <div class="flex items-center gap-1.5">
                  <StatusBadge :status="item.payment" />
                  <StatusBadge :status="item.fulfillment" />
                </div>
              </ListCell>
              <ListCell>
                <span class="text-base text-ink-gray-7 tabular-nums">{{ money(item.total) }}</span>
              </ListCell>
              <ListCell>
                <span class="text-base text-ink-gray-5">{{ shortDate(item.date) }}</span>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </section>

    <section class="mt-6 rounded-5 border border-outline-gray-1">
      <div class="flex items-center justify-between px-4 py-3">
        <h2 class="text-lg-semibold text-ink-gray-8">Top products</h2>
        <Button variant="ghost" label="All products" icon-right="lucide-arrow-right" route="/products" />
      </div>
      <div class="divide-y divide-outline-gray-1 border-t border-outline-gray-1">
        <RouterLink
          v-for="product in topProducts"
          :key="product.id"
          :to="`/products/${product.id}`"
          class="flex items-center gap-3 px-4 py-3 hover:bg-surface-gray-1"
        >
          <Thumb :emoji="product.thumb" size="size-8" />
          <div class="min-w-0 flex-1">
            <p class="truncate text-base text-ink-gray-8">{{ product.title }}</p>
            <p class="mt-1 text-sm text-ink-gray-5">{{ product.onHand }} in stock</p>
          </div>
          <span class="w-20 text-right text-sm text-ink-gray-5 tabular-nums">{{ product.sold }} sold</span>
          <span class="w-24 text-right text-base text-ink-gray-7 tabular-nums">
            {{ compactMoney(product.revenue) }}
          </span>
        </RouterLink>
      </div>
    </section>
  </PageBody>
</template>
