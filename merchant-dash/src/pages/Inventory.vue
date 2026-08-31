<script setup>
import { computed, ref } from 'vue'
import { Button, Switch, TextInput, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import Thumb from '../components/Thumb.vue'
import EmptyState from '../components/EmptyState.vue'
import BulkBar from '../components/BulkBar.vue'
import { inventory } from '../data/mock'
import { stockTone } from '../data/format'
import { ia } from '../ia/store'

const lowOnly = ref(false)
const query = ref('')
const selecting = ref(false)
const selection = ref([])

function endSelecting() {
  selecting.value = false
  selection.value = []
}

const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  return inventory.filter(
    (row) =>
      (!lowOnly.value || row.onHand <= 5) &&
      (!q || row.productTitle.toLowerCase().includes(q) || row.sku.toLowerCase().includes(q)),
  )
})

function adjust() {
  toast.success(`Adjustment recorded for ${selection.value.length} lines`)
  endSelecting()
}
</script>

<template>
  <AppPageHeader title="Stock">
    <template #actions>
      <Button label="Adjustments" icon-left="lucide-history" route="/inventory/adjustments" />
      <Button label="Receive stock" icon-left="lucide-plus" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody>
    <div class="flex flex-wrap items-center gap-3">
      <Switch v-model="lowOnly" label="Low stock only" size="sm" />
      <TextInput v-model="query" class="ml-auto w-56" placeholder="Search SKU or product" icon-left="lucide-search" />
      <Button
        :label="selecting ? 'Cancel selection' : 'Select'"
        icon-left="lucide-list-checks"
        :variant="selecting ? 'solid' : 'subtle'"
        theme="gray"
        @click="selecting ? endSelecting() : (selecting = true)"
      />
    </div>

    <BulkBar v-if="selecting" :count="selection.length" noun="line" @done="endSelecting">
      <Button label="Adjust quantity" @click="adjust" />
      <Button label="Transfer" />
    </BulkBar>

    <div class="mt-3 overflow-x-auto">
      <List
      v-model:selection="selection"
      class="min-w-[56rem]"
      :selectable="selecting"
      :row-height="Math.max(ia.density, 44)"
      :columns="['1fr', '11rem', '6rem', '6rem', '7rem']"
    >
      <ListHeader>
        <ListHeaderCell>Product</ListHeaderCell>
        <ListHeaderCell>SKU</ListHeaderCell>
        <ListHeaderCell>Committed</ListHeaderCell>
        <ListHeaderCell>Available</ListHeaderCell>
        <ListHeaderCell>On hand</ListHeaderCell>
      </ListHeader>
      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :value="item.id">
          <ListCell>
            <div class="flex min-w-0 items-center gap-2.5">
              <Thumb :emoji="item.thumb" size="size-7" />
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">{{ item.productTitle }}</p>
                <p class="truncate text-sm text-ink-gray-5">{{ item.variantTitle }}</p>
              </div>
            </div>
          </ListCell>
          <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.sku }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-5 tabular-nums">{{ item.committed }}</span></ListCell>
          <ListCell>
            <span class="text-base tabular-nums" :class="stockTone(item.onHand - item.committed)">
              {{ item.onHand - item.committed }}
            </span>
          </ListCell>
          <ListCell><TextInput :model-value="String(item.onHand)" size="sm" class="w-16" /></ListCell>
        </ListRow>
      </ListRows>
    </List>
    </div>

    <EmptyState v-if="!rows.length" icon="lucide-boxes" title="Nothing matches" description="Clear the filters to see all stock." />
  </PageBody>
</template>
