<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar, Button } from 'frappe-ui'
import { List, ListCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { customers, orders } from '../data/mock'
import { erpnextLink } from '../data/erpnext'
import { longDate, money, shortDate } from '../data/format'
import { ia } from '../ia/store'

const route = useRoute()
const customer = computed(() => customers.find((c) => c.id === route.params.id) ?? customers[0])
const theirOrders = computed(() => orders.filter((o) => o.customerId === customer.value.id))
</script>

<template>
  <AppPageHeader
    :title="customer.name"
    back-to="/customers"
    :breadcrumbs="[{ label: 'Customers', route: '/customers' }, { label: customer.name }]"
  >
    <template #actions>
      <Button
        label="View in ERP"
        icon-right="lucide-external-link"
        :link="erpnextLink('Customer', customer.name)"
      />
      <Button label="Email customer" icon-left="lucide-mail" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody width="wide">
    <div class="flex items-center gap-3">
      <Avatar :label="customer.name" size="2xl" />
      <div>
        <p class="text-xl text-ink-gray-9">{{ customer.name }}</p>
        <p class="mt-1 text-sm text-ink-gray-5">
          {{ customer.email }} · {{ customer.city }} · since {{ longDate(customer.since) }}
        </p>
        <p class="mt-1 text-sm text-ink-gray-4">
          Contact and billing details are kept on the customer record.
        </p>
      </div>
    </div>

    <section class="mt-6 grid gap-y-4 grid-cols-3 divide-x divide-outline-gray-2">
      <div class="pr-5">
        <p class="text-sm text-ink-gray-5">Orders</p>
        <p class="mt-1 text-2xl text-ink-gray-9 tabular-nums">{{ customer.orders }}</p>
      </div>
      <div class="px-5">
        <p class="text-sm text-ink-gray-5">Lifetime spend</p>
        <p class="mt-1 text-2xl text-ink-gray-9 tabular-nums">{{ money(customer.spend) }}</p>
      </div>
      <div class="px-5">
        <p class="text-sm text-ink-gray-5">Average order</p>
        <p class="mt-1 text-2xl text-ink-gray-9 tabular-nums">
          {{ money(Math.round(customer.spend / customer.orders)) }}
        </p>
      </div>
    </section>

    <section class="mt-8">
      <div class="flex items-baseline justify-between">
        <h2 class="text-lg-semibold text-ink-gray-8">Recent orders</h2>
        <span class="text-sm text-ink-gray-5">{{ customer.orders }} orders all time</span>
      </div>
      <List class="mt-1 -mx-3 list-row-px-3" :row-height="Math.max(ia.density, 48)">
        <ListRows :items="theirOrders" row-key="id" v-slot="{ item }">
          <ListRow :to="`/orders/${item.slug}`" :value="item.id">
            <ListCell>
              <span class="text-base text-ink-gray-4 tabular-nums">{{ item.id }}</span>
            </ListCell>
            <ListCell>
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">
                  {{ item.items.length }} item{{ item.items.length > 1 ? 's' : '' }} ·
                  {{ money(item.total) }}
                </p>
                <p class="mt-1 text-sm text-ink-gray-5">{{ shortDate(item.date) }} · {{ item.channel }}</p>
              </div>
            </ListCell>
            <ListCell>
              <div class="flex items-center gap-3">
                <StatusBadge :status="item.payment" />
                <StatusBadge :status="item.fulfillment" />
                <span class="lucide-chevron-right size-4 text-ink-gray-4" aria-hidden="true" />
              </div>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
    </section>

  </PageBody>
</template>
