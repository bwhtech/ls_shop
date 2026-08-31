<script setup>
import { computed, ref } from 'vue'
import { Avatar, Button, TextInput } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import { customers } from '../data/mock'
import { longDate, money } from '../data/format'
import { ia } from '../ia/store'

const query = ref('')

const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  return customers.filter((c) => !q || c.name.toLowerCase().includes(q) || c.email.includes(q))
})
</script>

<template>
  <AppPageHeader title="Customers">
    <template #actions>
      <Button label="Export" icon-left="lucide-download" />
      <Button label="Add customer" icon-left="lucide-plus" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody>
    <TextInput v-model="query" class="w-56" placeholder="Search customers" icon-left="lucide-search" />
    <List class="mt-3 -mx-3 list-row-px-3" :row-height="Math.max(ia.density, 44)" :columns="['1fr', '9rem', '6rem', '8rem', '9rem']">
      <ListHeader>
        <ListHeaderCell>Customer</ListHeaderCell>
        <ListHeaderCell>City</ListHeaderCell>
        <ListHeaderCell>Orders</ListHeaderCell>
        <ListHeaderCell>Spend</ListHeaderCell>
        <ListHeaderCell>Customer since</ListHeaderCell>
      </ListHeader>
      <ListRows :items="rows" row-key="id" v-slot="{ item }">
        <ListRow :to="`/customers/${item.id}`" :value="item.id">
          <ListCell>
            <div class="flex min-w-0 items-center gap-2.5">
              <Avatar :label="item.name" size="sm" />
              <div class="min-w-0">
                <p class="truncate text-base text-ink-gray-8">{{ item.name }}</p>
                <p class="truncate text-sm text-ink-gray-5">{{ item.email }}</p>
              </div>
            </div>
          </ListCell>
          <ListCell><span class="text-base text-ink-gray-7">{{ item.city }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-7 tabular-nums">{{ item.orders }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-8 tabular-nums">{{ money(item.spend) }}</span></ListCell>
          <ListCell><span class="text-base text-ink-gray-5">{{ longDate(item.since) }}</span></ListCell>
        </ListRow>
      </ListRows>
    </List>
  </PageBody>
</template>
