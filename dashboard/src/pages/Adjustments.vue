<script setup>
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import { adjustments } from '../data/mock'
import { shortDate } from '../data/format'
import { ia } from '../ia/store'
</script>

<template>
  <AppPageHeader title="Adjustments" back-to="/inventory" />

  <PageBody>
    <p class="text-p-sm text-ink-gray-5">Every stock movement, in order. Read-only.</p>
    <div class="mt-3 overflow-x-auto">
      <List class="min-w-[52rem]" :row-height="ia.density" :columns="['7rem', '1fr', '11rem', '6rem', '9rem', '7rem']">
      <ListHeader>
        <ListHeaderCell>Date</ListHeaderCell>
        <ListHeaderCell>Product</ListHeaderCell>
        <ListHeaderCell>SKU</ListHeaderCell>
        <ListHeaderCell>Change</ListHeaderCell>
        <ListHeaderCell>Reason</ListHeaderCell>
        <ListHeaderCell>By</ListHeaderCell>
      </ListHeader>
      <ListRows :items="adjustments" row-key="id" v-slot="{ item }">
        <ListRow :value="item.id">
          <ListCell><span class="text-base text-ink-gray-5">{{ shortDate(item.date) }}</span></ListCell>
          <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.product }}</span></ListCell>
          <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.sku }}</span></ListCell>
          <ListCell>
            <span class="text-base tabular-nums" :class="item.delta > 0 ? 'text-ink-green-6' : 'text-ink-red-6'">
              {{ item.delta > 0 ? '+' : '' }}{{ item.delta }}
            </span>
          </ListCell>
          <ListCell><span class="text-base text-ink-gray-7">{{ item.reason }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-5">{{ item.by }}</span></ListCell>
        </ListRow>
      </ListRows>
    </List>
    </div>
  </PageBody>
</template>
