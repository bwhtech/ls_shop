<script setup>
import { computed, ref } from 'vue'
import { Button } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import AppPageHeader from '../../components/AppPageHeader.vue'
import PageBody from '../../components/PageBody.vue'
import ListPagination from '../../components/ListPagination.vue'
import StatusBadge from '../../components/StatusBadge.vue'
import { storefrontPages } from '../../data/mock'
import { shortDate } from '../../data/format'
import { ia } from '../../ia/store'

const page = ref(1)
const pageSize = ref(10)

const rows = computed(() =>
  storefrontPages.slice((page.value - 1) * pageSize.value, page.value * pageSize.value),
)
</script>

<template>
  <AppPageHeader title="Pages">
    <template #actions>
      <Button label="Add page" icon-left="lucide-plus" variant="solid" theme="gray" />
    </template>
  </AppPageHeader>

  <PageBody width="wide">
    <p class="text-p-sm text-ink-gray-5">
      Home is a page like any other — it just happens to sit at the root and carry section blocks.
    </p>

    <div class="mt-3 overflow-x-auto">
      <List
        class="min-w-[38rem]"
        :row-height="Math.max(ia.density, 44)"
        :columns="['minmax(9rem,1fr)', '11rem', '7rem', 'minmax(9rem,1fr)', '6rem']"
      >
        <ListHeader>
          <ListHeaderCell>Page</ListHeaderCell>
          <ListHeaderCell>Path</ListHeaderCell>
          <ListHeaderCell>Status</ListHeaderCell>
          <ListHeaderCell>Sections</ListHeaderCell>
          <ListHeaderCell>Updated</ListHeaderCell>
        </ListHeader>
        <ListRows :items="rows" row-key="id" v-slot="{ item }">
          <ListRow :value="item.id">
            <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.title }}</span></ListCell>
            <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.slug }}</span></ListCell>
            <ListCell><StatusBadge :status="item.status" /></ListCell>
            <ListCell><span class="truncate text-base text-ink-gray-7">{{ item.sections.join(' · ') }}</span></ListCell>
            <ListCell><span class="text-base text-ink-gray-5">{{ shortDate(item.updated) }}</span></ListCell>
          </ListRow>
        </ListRows>
      </List>
    </div>

    <ListPagination
      v-model:page="page"
      v-model:page-size="pageSize"
      :total="storefrontPages.length"
    />
  </PageBody>
</template>
