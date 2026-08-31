<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dropdown, Select, TabButtons, TextInput, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListHeaderCellSort, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import ListPagination from '../components/ListPagination.vue'
import StatusBadge from '../components/StatusBadge.vue'
import Thumb from '../components/Thumb.vue'
import EmptyState from '../components/EmptyState.vue'
import BulkBar from '../components/BulkBar.vue'
import { productTypes, products } from '../data/mock'
import { money, shortDate, stockTone } from '../data/format'
import { ia } from '../ia/store'
import { openImport } from '../data/importFlow'

const STATUS_TABS = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Draft', value: 'draft' },
  { label: 'Archived', value: 'archived' },
]

const typeOptions = [
  { label: 'All types', value: 'all' },
  ...productTypes.map((t) => ({ label: t.name, value: t.id })),
]

const status = ref('all')
const type = ref('all')
const query = ref('')
const selecting = ref(false)
const selection = ref([])

function endSelecting() {
  selecting.value = false
  selection.value = []
}

const sort = ref({ key: 'updated', direction: 'desc' })

const page = ref(1)
const pageSize = ref(20)

const matches = computed(() => {
  const q = query.value.trim().toLowerCase()
  const filtered = products.filter(
    (p) =>
      (status.value === 'all' || p.status === status.value) &&
      (type.value === 'all' || p.type === type.value) &&
      (!q || p.title.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)),
  )
  const { key, direction } = sort.value
  const dir = direction === 'asc' ? 1 : -1
  return [...filtered].sort((a, b) => (a[key] > b[key] ? dir : a[key] < b[key] ? -dir : 0))
})

// A filter or a sort changes what page one is, so it sends you back to it.
watch([query, status, type, sort], () => (page.value = 1))

const rows = computed(() =>
  matches.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value),
)

const typeName = (id) => productTypes.find((t) => t.id === id)?.name ?? id

function toggleSort(key) {
  sort.value =
    sort.value.key === key
      ? { key, direction: sort.value.direction === 'asc' ? 'desc' : 'asc' }
      : { key, direction: 'asc' }
}

const directionFor = (key) => (sort.value.key === key ? sort.value.direction : null)

const addOptions = [
  { label: 'Add product', icon: 'lucide-plus', onClick: () => toast.info('Product form — pick a type first') },
  { label: 'Import from CSV', icon: 'lucide-upload', onClick: openImport },
  { label: 'Add product type', icon: 'lucide-shapes', route: '/product-types' },
]
</script>

<template>
  <AppPageHeader title="Products">
    <template #actions>
      <Button label="Import" icon-left="lucide-upload" @click="openImport" />
      <Dropdown :options="addOptions">
        <Button label="Add product" icon-right="lucide-chevron-down" variant="solid" theme="gray" />
      </Dropdown>
    </template>
  </AppPageHeader>

  <PageBody>
    <div class="flex flex-wrap items-center gap-2">
      <TabButtons v-model="status" size="sm" :options="STATUS_TABS" />
      <Select v-model="type" :options="typeOptions" />
      <TextInput
        v-model="query"
        class="ml-auto w-56"
        placeholder="Search products"
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

    <BulkBar v-if="selecting" :count="selection.length" noun="product" @done="endSelecting">
      <Button label="Edit prices" route="/pricing" />
      <Button label="Add to collection" />
      <Button label="Archive" theme="red" variant="subtle" />
    </BulkBar>

    <div class="mt-3 overflow-x-auto">
      <List
      v-model:selection="selection"
      class="min-w-[54rem]"
      :selectable="selecting"
      :row-height="ia.density"
      :columns="['1fr', '7rem', '8rem', '8rem', '7rem', '6rem']"
    >
      <ListHeader>
        <ListHeaderCellSort :direction="directionFor('title')" @click="toggleSort('title')">
          Product
        </ListHeaderCellSort>
        <ListHeaderCell>Status</ListHeaderCell>
        <ListHeaderCell>Type</ListHeaderCell>
        <ListHeaderCellSort align="end" :direction="directionFor('stock')" @click="toggleSort('stock')">
          Inventory
        </ListHeaderCellSort>
        <ListHeaderCellSort align="end" :direction="directionFor('price')" @click="toggleSort('price')">
          Price
        </ListHeaderCellSort>
        <ListHeaderCellSort align="end" :direction="directionFor('updated')" @click="toggleSort('updated')">
          Updated
        </ListHeaderCellSort>
      </ListHeader>

      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :to="`/products/${item.id}`" :value="item.id">
          <ListCell>
            <div class="flex min-w-0 items-center gap-2.5">
              <Thumb :emoji="item.thumb" />
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">{{ item.title }}</p>
                <p class="truncate text-sm text-ink-gray-5">
                  {{ item.sku }}<span v-if="item.hasVariants"> · {{ item.variants.length }} variants</span>
                </p>
              </div>
            </div>
          </ListCell>
          <ListCell><StatusBadge :status="item.status" /></ListCell>
          <ListCell><span class="text-base text-ink-gray-7">{{ typeName(item.type) }}</span></ListCell>
          <ListCell>
            <span class="w-full text-right text-base tabular-nums" :class="stockTone(item.stock)">
              {{ item.stock }} in stock
            </span>
          </ListCell>
          <ListCell>
            <span class="w-full text-right text-base text-ink-gray-8 tabular-nums">{{ money(item.price) }}</span>
          </ListCell>
          <ListCell>
            <span class="w-full text-right text-base text-ink-gray-5">{{ shortDate(item.updated) }}</span>
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
      icon="lucide-package"
      title="No products match"
      description="Change the filters, or import a catalogue to get started."
    >
      <Button label="Import CSV" icon-left="lucide-upload" variant="solid" theme="gray" class="mt-2" @click="openImport" />
    </EmptyState>
  </PageBody>
</template>
