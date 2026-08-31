<script setup>
import { computed, ref } from 'vue'
import { Button, Select, TextInput, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import Thumb from '../components/Thumb.vue'
import BulkBar from '../components/BulkBar.vue'
import { productTypes, products } from '../data/mock'
import { money } from '../data/format'
import { ia } from '../ia/store'

const type = ref('all')
const selecting = ref(false)
const selection = ref([])

function endSelecting() {
  selecting.value = false
  selection.value = []
}

const typeOptions = [
  { label: 'All types', value: 'all' },
  ...productTypes.map((t) => ({ label: t.name, value: t.id })),
]

// One row per sellable unit — a plain product, or each of its variants.
const rows = computed(() =>
  products
    .filter((p) => type.value === 'all' || p.type === type.value)
    .flatMap((p) =>
      p.hasVariants
        ? p.variants.map((v) => ({
            id: v.id, title: p.title, subtitle: v.title, sku: v.sku,
            thumb: p.thumb, price: v.price, compareAt: v.compareAt,
          }))
        : [{ id: p.id, title: p.title, subtitle: '—', sku: p.sku, thumb: p.thumb, price: p.price, compareAt: p.compareAt }],
    ),
)

const margin = (price) => Math.round(((price - price * 0.55) / price) * 100)

function bulkPrice() {
  toast.success(`Price rule queued for ${selection.value.length} items`)
  endSelecting()
}
</script>

<template>
  <AppPageHeader
    title="Edit prices"
    back-to="/products"
    :breadcrumbs="[{ label: 'Products', route: '/products' }, { label: 'Edit prices' }]"
  >
    <template #actions>
      <Button label="Price rules" icon-left="lucide-percent" />
      <Button label="Export prices" icon-left="lucide-download" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody>
    <div class="flex flex-wrap items-center gap-3">
      <Select v-model="type" :options="typeOptions" />
      <p class="text-sm text-ink-gray-5">
        {{ rows.length }} sellable units · one row per variant, priced individually on its product
      </p>
      <Button
        class="ml-auto"
        :label="selecting ? 'Cancel selection' : 'Select'"
        icon-left="lucide-list-checks"
        :variant="selecting ? 'solid' : 'subtle'"
        theme="gray"
        @click="selecting ? endSelecting() : (selecting = true)"
      />
    </div>

    <BulkBar v-if="selecting" :count="selection.length" noun="item" @done="endSelecting">
      <Button label="Raise by %" @click="bulkPrice" />
      <Button label="Set compare-at" @click="bulkPrice" />
    </BulkBar>

    <div class="mt-3 overflow-x-auto">
      <List
      v-model:selection="selection"
      class="min-w-[50rem]"
      :selectable="selecting"
      :row-height="Math.max(ia.density, 44)"
      :columns="['1fr', '11rem', '7rem', '8rem', '6rem']"
    >
      <ListHeader>
        <ListHeaderCell>Item</ListHeaderCell>
        <ListHeaderCell>SKU</ListHeaderCell>
        <ListHeaderCell>Price</ListHeaderCell>
        <ListHeaderCell>Compare at</ListHeaderCell>
        <ListHeaderCell>Margin</ListHeaderCell>
      </ListHeader>
      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :value="item.id">
          <ListCell>
            <div class="flex min-w-0 items-center gap-2.5">
              <Thumb :emoji="item.thumb" size="size-7" />
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">{{ item.title }}</p>
                <p class="truncate text-sm text-ink-gray-5">{{ item.subtitle }}</p>
              </div>
            </div>
          </ListCell>
          <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.sku }}</span></ListCell>
          <ListCell><TextInput :model-value="String(item.price)" size="sm" class="w-20" /></ListCell>
          <ListCell>
            <span class="text-base tabular-nums" :class="item.compareAt ? 'text-ink-gray-7' : 'text-ink-gray-4'">
              {{ item.compareAt ? money(item.compareAt) : '—' }}
            </span>
          </ListCell>
          <ListCell><span class="text-base text-ink-gray-7 tabular-nums">{{ margin(item.price) }}%</span></ListCell>
        </ListRow>
      </ListRows>
    </List>
    </div>
  </PageBody>
</template>
