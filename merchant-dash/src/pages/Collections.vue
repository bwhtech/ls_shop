<script setup>
import { computed, ref } from 'vue'
import { Badge, Button } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import ListPagination from '../components/ListPagination.vue'
import { collections } from '../data/mock'
import { ia } from '../ia/store'

const page = ref(1)
const pageSize = ref(10)

const rows = computed(() =>
  collections.slice((page.value - 1) * pageSize.value, page.value * pageSize.value),
)
</script>

<template>
  <AppPageHeader title="Collections">
    <template #actions>
      <Button label="Create collection" icon-left="lucide-plus" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody width="wide">
    <p class="text-p-sm text-ink-gray-5">
      Manual collections hold a fixed list. Smart collections re-evaluate their rule on every save.
    </p>

    <div class="mt-3 overflow-x-auto">
      <List
        class="min-w-[34rem]"
        :row-height="ia.density"
        :columns="['minmax(9rem,1fr)', '7rem', 'minmax(9rem,1fr)', '6rem']"
      >
        <ListHeader>
          <ListHeaderCell>Collection</ListHeaderCell>
          <ListHeaderCell>Type</ListHeaderCell>
          <ListHeaderCell>Condition</ListHeaderCell>
          <ListHeaderCell>Products</ListHeaderCell>
        </ListHeader>
        <ListRows :items="rows" row-key="id" v-slot="{ item }">
          <ListRow :value="item.id">
            <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.title }}</span></ListCell>
            <ListCell>
              <Badge :label="item.rule" :theme="item.rule === 'smart' ? 'blue' : 'gray'" variant="subtle" />
            </ListCell>
            <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.condition }}</span></ListCell>
            <ListCell><span class="text-base text-ink-gray-7 tabular-nums">{{ item.count }}</span></ListCell>
          </ListRow>
        </ListRows>
      </List>
    </div>

    <ListPagination v-model:page="page" v-model:page-size="pageSize" :total="collections.length" />
  </PageBody>
</template>
