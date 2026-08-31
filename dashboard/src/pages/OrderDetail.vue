<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar, Badge, Button, Dropdown, ScrollArea, dialog, toast } from 'frappe-ui'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import StatusBadge from '../components/StatusBadge.vue'
import OrderProgress from '../components/OrderProgress.vue'
import Thumb from '../components/Thumb.vue'
import { customers, orders } from '../data/mock'
import { erpnextLink } from '../data/erpnext'
import { longDate, money } from '../data/format'

const route = useRoute()

const EXCEPTIONS = ['pending', 'refunded', 'partially_refunded']

const order = computed(() => orders.find((o) => o.slug === route.params.id) ?? orders[0])
const customer = computed(() => customers.find((c) => c.id === order.value.customerId))
const erpLink = computed(() => erpnextLink('Sales Order', order.value.id.replace('#', 'SO-')))

const moreActions = [
  { label: 'Duplicate', icon: 'lucide-copy', onClick: () => toast.info('Duplicated') },
  { label: 'Print invoice', icon: 'lucide-printer', onClick: () => toast.info('Sent to printer') },
  { label: 'Refund', icon: 'lucide-rotate-ccw', onClick: () => refund() },
  {
    label: 'Cancel order',
    icon: 'lucide-x-circle',
    onClick: () =>
      dialog.confirm({
        title: 'Cancel this order?',
        message: 'The customer is refunded and stock is restocked. This cannot be undone.',
        theme: 'red',
        confirmLabel: 'Cancel order',
        onConfirm: () => toast.success('Order cancelled'),
      }),
  },
]

function refund() {
  dialog.confirm({
    title: 'Refund this order?',
    message: 'The full amount goes back to the original payment method.',
    onConfirm: () => {
      order.value.payment = 'refunded'
      toast.success('Refund issued')
    },
  })
}

function fulfil() {
  order.value.fulfillment = 'fulfilled'
  toast.success('Fulfilment created')
}
</script>

<template>
  <AppPageHeader
    :title="order.id"
    back-to="/orders"
    :breadcrumbs="[{ label: 'Orders', route: '/orders' }, { label: order.id }]"
  >
    <template #actions>
      <Button label="View in ERP" icon-right="lucide-external-link" :link="erpLink" />
      <Dropdown :options="moreActions">
        <Button icon="lucide-ellipsis" label="More actions" />
      </Dropdown>
      <Button
        label="Fulfil items"
        icon-left="lucide-truck"
        variant="solid"
        theme="gray"
        :disabled="order.fulfillment === 'fulfilled' || order.fulfillment === 'cancelled'"
        @click="fulfil"
      />
    </template>
  </AppPageHeader>

  <!-- Two panes, each with its own scroll: the order is worked down the left,
       and who it is for stays put on the right. -->
  <div class="flex min-h-0 flex-1 overflow-hidden">
    <ScrollArea class="min-w-0 flex-1">
      <PageBody width="narrow">
    <div class="flex flex-wrap items-center gap-2">
      <StatusBadge v-if="EXCEPTIONS.includes(order.payment)" :status="order.payment" />
      <StatusBadge v-if="order.fulfillment === 'cancelled'" :status="order.fulfillment" />
      <span class="text-sm text-ink-gray-5">
        {{ longDate(order.date) }} at {{ order.time }} · {{ order.channel }} · {{ order.location }}
      </span>
    </div>

    <!-- Where the order has reached, read left to right. -->
    <OrderProgress class="mt-6" :order="order" />

    <!-- The lines and what they add up to are one thing, so they are one
         card: the total is the last row of the same table. -->
    <div class="mt-5 space-y-6">
      <section class="rounded-5 border border-outline-gray-1">
          <div class="flex items-center justify-between px-4 py-3">
            <h2 class="text-lg-semibold text-ink-gray-8">Items</h2>
            <div class="flex items-center gap-2">
              <span class="text-sm text-ink-gray-5">
                {{ order.items.length }} {{ order.items.length === 1 ? 'line' : 'lines' }}
              </span>
              <StatusBadge :status="order.fulfillment" />
            </div>
          </div>

          <div class="divide-y divide-outline-gray-1 border-t border-outline-gray-1">
            <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3 px-4 py-3">
              <Thumb :emoji="item.thumb" size="size-10" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-base text-ink-gray-8">{{ item.title }}</p>
                <p class="mt-1 truncate text-sm text-ink-gray-5">
                  <span v-if="item.variantTitle">{{ item.variantTitle }} · </span>{{ item.sku }}
                </p>
              </div>
              <span class="w-28 text-right text-base text-ink-gray-5 tabular-nums">
                {{ money(item.price) }} × {{ item.qty }}
              </span>
              <span class="w-24 text-right text-base text-ink-gray-8 tabular-nums">
                {{ money(item.price * item.qty) }}
              </span>
            </div>
          </div>

          <div class="space-y-1.5 border-t border-outline-gray-1 px-4 py-3">
            <div class="flex justify-between text-base text-ink-gray-6">
              <span>Subtotal</span><span class="tabular-nums">{{ money(order.subtotal) }}</span>
            </div>
            <div class="flex justify-between text-base text-ink-gray-6">
              <span>Shipping</span>
              <span class="tabular-nums">{{ order.shipping ? money(order.shipping) : 'Free' }}</span>
            </div>
            <div class="flex justify-between text-base text-ink-gray-6">
              <span>Tax (5%)</span><span class="tabular-nums">{{ money(order.tax) }}</span>
            </div>
            <div class="flex justify-between pt-1 text-base-semibold text-ink-gray-9">
              <span>Total</span><span class="tabular-nums">{{ money(order.total) }}</span>
            </div>
          </div>
      </section>
    </div>
      </PageBody>
    </ScrollArea>

    <aside class="hidden w-[19rem] shrink-0 flex-col border-l border-outline-gray-1 lg:flex">
      <ScrollArea class="min-h-0 flex-1">
        <div class="divide-y divide-outline-gray-1">
        <section class="px-4 py-4">
          <p class="text-sm text-ink-gray-5">Customer</p>
          <router-link :to="`/customers/${customer.id}`" class="mt-2 flex items-center gap-2.5">
            <Avatar :label="customer.name" size="md" />
            <div class="min-w-0">
              <p class="truncate text-base text-ink-gray-8">{{ customer.name }}</p>
              <p class="truncate text-sm text-ink-gray-5">
                {{ customer.orders }} orders · {{ money(customer.spend) }} lifetime
              </p>
            </div>
          </router-link>
          <p class="mt-3 truncate text-sm text-ink-blue-link">{{ order.email }}</p>
        </section>

        <section class="px-4 py-4">
          <p class="text-sm text-ink-gray-5">Shipping address</p>
          <p class="mt-1.5 text-p-base text-ink-gray-7">
            <span class="block">{{ order.address.line1 }}</span>
            <span class="block">{{ order.address.city }} {{ order.address.pin }}</span>
            <span class="block">{{ order.address.country }}</span>
          </p>
        </section>

        <section class="px-4 py-4">
          <p class="text-sm text-ink-gray-5">Tags</p>
          <div class="mt-1.5 flex flex-wrap gap-1.5">
            <Badge v-for="tag in order.tags" :key="tag" :label="tag" variant="subtle" />
            <span v-if="!order.tags.length" class="text-sm text-ink-gray-5">None</span>
          </div>
        </section>

        <section class="px-4 py-4">
          <p class="text-sm text-ink-gray-5">Note</p>
          <p class="mt-1.5 text-p-base" :class="order.note ? 'text-ink-gray-7' : 'text-ink-gray-4'">
            {{ order.note || 'No note from the customer.' }}
          </p>
        </section>
        </div>
      </ScrollArea>
    </aside>
  </div>
</template>
