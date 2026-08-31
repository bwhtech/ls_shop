<script setup>
import { computed, ref, watch } from 'vue'
import { Button, TabButtons, TextInput, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListHeaderCellSort, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import ListPagination from '../components/ListPagination.vue'
import StatusBadge from '../components/StatusBadge.vue'
import Thumb from '../components/Thumb.vue'
import EmptyState from '../components/EmptyState.vue'
import BulkBar from '../components/BulkBar.vue'
import { orders } from '../data/mock'
import { money, shortDate } from '../data/format'
import { ia } from '../ia/store'

const TABS = [
  { label: 'All', value: 'all' },
  { label: 'Unfulfilled', value: 'unfulfilled' },
  { label: 'Unpaid', value: 'unpaid' },
  { label: 'Open', value: 'open' },
  { label: 'Closed', value: 'closed' },
]

const tab = ref('all')
const query = ref('')
const selecting = ref(false)
const selection = ref([])

function endSelecting() {
  selecting.value = false
  selection.value = []
}

const sort = ref({ key: 'date', direction: 'desc' })

const MATCHERS = {
  all: () => true,
  unfulfilled: (o) => o.fulfillment === 'unfulfilled',
  unpaid: (o) => o.payment === 'pending',
  open: (o) => !['delivered', 'cancelled'].includes(o.fulfillment),
  closed: (o) => ['delivered', 'cancelled'].includes(o.fulfillment),
}

const page = ref(1)
const pageSize = ref(20)

const matches = computed(() => {
  const q = query.value.trim().toLowerCase()
  const filtered = orders.filter(
    (o) =>
      MATCHERS[tab.value](o) &&
      (!q || o.id.toLowerCase().includes(q) || o.customer.toLowerCase().includes(q)),
  )
  const { key, direction } = sort.value
  const dir = direction === 'asc' ? 1 : -1
  return [...filtered].sort((a, b) => (a[key] > b[key] ? dir : a[key] < b[key] ? -dir : 0))
})

// A filter or a sort changes what page one is, so it sends you back to it.
watch([query, tab, sort], () => (page.value = 1))

const rows = computed(() =>
  matches.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value),
)

function toggleSort(key) {
  sort.value =
    sort.value.key === key
      ? { key, direction: sort.value.direction === 'asc' ? 'desc' : 'asc' }
      : { key, direction: 'asc' }
}

const directionFor = (key) => (sort.value.key === key ? sort.value.direction : null)

function markFulfilled() {
  toast.success(`${selection.value.length} order(s) marked fulfilled`)
  endSelecting()
}
</script>

<template>
  <AppPageHeader title="Orders">
    <template #actions>
      <Button label="Export" icon-left="lucide-download" />
      <Button label="Create order" icon-left="lucide-plus" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody>
    <div class="flex flex-wrap items-center gap-2">
      <TabButtons v-model="tab" size="sm" :options="TABS" />
      <TextInput
        v-model="query"
        class="ml-auto w-56"
        placeholder="Search orders"
        icon-left="lucide-search"
      />
      <Button
        :label="selecting ? 'Cancel selection' : 'Select'"
        icon-left="lucide-list-checks"
        :variant="selecting ? 'solid' : 'subtle'"
        theme="gray"
        @click="selecting ? endSelecting() : (selecting = true)"
      />
    </div>

    <BulkBar v-if="selecting" :count="selection.length" noun="order" @done="endSelecting">
      <Button label="Mark fulfilled" @click="markFulfilled" />
      <Button label="Print packing slips" />
    </BulkBar>

    <div class="mt-3 overflow-x-auto">
      <List
      v-model:selection="selection"
      class="min-w-[54rem]"
      :selectable="selecting"
      :row-height="ia.density"
      :columns="['1fr', '7rem', '9rem', '9rem', '6rem', '7rem']"
    >
      <ListHeader>
        <ListHeaderCellSort :direction="directionFor('customer')" @click="toggleSort('customer')">
          Order
        </ListHeaderCellSort>
        <ListHeaderCellSort :direction="directionFor('date')" @click="toggleSort('date')">
          Date
        </ListHeaderCellSort>
        <ListHeaderCell>Payment</ListHeaderCell>
        <ListHeaderCell>Fulfilment</ListHeaderCell>
        <ListHeaderCell>Items</ListHeaderCell>
        <ListHeaderCellSort align="end" :direction="directionFor('total')" @click="toggleSort('total')">
          Total
        </ListHeaderCellSort>
      </ListHeader>

      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :to="`/orders/${item.slug}`" :value="item.id">
          <ListCell>
            <div class="flex min-w-0 items-center gap-2.5">
              <Thumb :emoji="item.items[0].thumb" />
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">{{ item.customer }}</p>
                <p class="truncate text-sm text-ink-gray-4 tabular-nums">{{ item.id }}</p>
              </div>
            </div>
          </ListCell>
          <ListCell>
            <span class="text-base text-ink-gray-5">{{ shortDate(item.date) }}</span>
          </ListCell>
          <ListCell><StatusBadge :status="item.payment" /></ListCell>
          <ListCell><StatusBadge :status="item.fulfillment" /></ListCell>
          <ListCell>
            <span class="text-base text-ink-gray-7 tabular-nums">{{ item.items.length }}</span>
          </ListCell>
          <ListCell>
            <span class="w-full text-right text-base text-ink-gray-8 tabular-nums">
              {{ money(item.total) }}
            </span>
          </ListCell>
        </ListRow>
      </ListRows>
    </List>
    </div>

    <ListPagination
      v-if="matches.length"
      v-model:page="page"
      v-model:page-size="pageSize"
      :total="matches.length"
    />

    <EmptyState
      v-if="!rows.length"
      icon="lucide-shopping-bag"
      title="No orders here"
      description="Try a different filter or search term."
    />
  </PageBody>
</template>
