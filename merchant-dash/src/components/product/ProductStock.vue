<script setup>
import { computed } from 'vue'
import { Button, TextInput } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { inventory } from '../../data/mock'
import { stockTone } from '../../data/format'
import { ia } from '../../ia/store'

const props = defineProps({ product: { type: Object, required: true } })

const rows = computed(() => inventory.filter((row) => row.productId === props.product.id))
</script>

<template>
  <section>
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-8">Stock</h2>
        <p class="mt-1 text-p-sm text-ink-gray-5">On hand per variant.</p>
      </div>
      <Button label="Open in Inventory" variant="ghost" route="/inventory" />
    </div>

    <div class="mt-3 overflow-x-auto">
    <List
      class="min-w-[28rem]"
      :row-height="Math.max(ia.density, 44)"
      :columns="['minmax(7rem,1fr)', 'minmax(8rem,1fr)', '6rem', '6rem']"
    >
      <ListHeader>
        <ListHeaderCell>Variant</ListHeaderCell>
        <ListHeaderCell>SKU</ListHeaderCell>
        <ListHeaderCell>Committed</ListHeaderCell>
        <ListHeaderCell>On hand</ListHeaderCell>
      </ListHeader>
      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :value="item.id">
          <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.variantTitle }}</span></ListCell>
          <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.sku }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-5 tabular-nums">{{ item.committed }}</span></ListCell>
          <ListCell>
            <TextInput :model-value="String(item.onHand)" size="sm" class="w-16" />
          </ListCell>
        </ListRow>
      </ListRows>
    </List>
    </div>
  </section>
</template>
