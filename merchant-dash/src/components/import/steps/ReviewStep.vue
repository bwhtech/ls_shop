<script setup>
import { computed } from 'vue'
import { Badge, Button, TabButtons, Tooltip } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { IMPORT_ROWS, TOTAL_ROWS, counts, imp } from '../../../data/importFlow'
import { money } from '../../../data/format'
import ProductThumb from '../ProductThumb.vue'
import CoachTip from '../CoachTip.vue'

const filtered = computed(() => {
  if (imp.reviewFilter === 'errors') return IMPORT_ROWS.filter((r) => r.issue?.level === 'error')
  if (imp.reviewFilter === 'warnings') return IMPORT_ROWS.filter((r) => r.issue?.level === 'warning')
  if (imp.reviewFilter === 'ready') return IMPORT_ROWS.filter((r) => !r.issue)
  return IMPORT_ROWS
})

const newGroups = ['Footwear', 'Sweatshirts']
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl text-ink-gray-9">Check before it goes live</h2>
      <p class="mt-1.5 text-p-base text-ink-gray-6">
        Nothing has been saved yet. Rows with an error are left out; everything else imports.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-4">
      <div class="rounded-5 border border-outline-gray-1 p-4">
        <div class="text-2xl text-ink-gray-9 tabular-nums">{{ counts.ready }}</div>
        <div class="mt-0.5 text-sm text-ink-gray-5">ready to import</div>
      </div>
      <div class="rounded-5 border border-outline-gray-1 p-4">
        <div class="text-2xl text-ink-amber-7 tabular-nums">{{ counts.warnings }}</div>
        <div class="mt-0.5 text-sm text-ink-gray-5">warnings, still imported</div>
      </div>
      <div class="rounded-5 border border-outline-gray-1 p-4">
        <div class="text-2xl text-ink-red-6 tabular-nums">{{ counts.errors }}</div>
        <div class="mt-0.5 text-sm text-ink-gray-5">errors, skipped</div>
      </div>
      <div class="rounded-5 border border-outline-gray-1 p-4">
        <div class="text-2xl text-ink-gray-9 tabular-nums">{{ newGroups.length }}</div>
        <div class="mt-0.5 text-sm text-ink-gray-5">new categories created</div>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <TabButtons
        v-model="imp.reviewFilter"
        :options="[
          { label: 'All rows', value: 'all' },
          { label: 'Ready', value: 'ready' },
          { label: 'Warnings', value: 'warnings' },
          { label: 'Errors', value: 'errors' },
        ]"
      />
      <Tooltip text="Categories that do not exist yet are created for you">
        <div class="flex items-center gap-1.5">
          <span class="text-sm text-ink-gray-5">New categories:</span>
          <Badge v-for="g in newGroups" :key="g" :label="g" theme="blue" variant="subtle" />
        </div>
      </Tooltip>
      <Button class="ml-auto" variant="subtle" icon-left="lucide-download" label="Download error rows" />
    </div>

    <div class="overflow-hidden rounded-5 border border-outline-gray-1">
      <div class="overflow-x-auto px-2">
        <List
          class="min-w-[44rem]"
          :columns="['minmax(0,1fr)', '9rem', '7rem', '5rem', 'minmax(0,14rem)']"
          :row-height="52"
        >
          <ListHeader>
            <ListHeaderCell>Product</ListHeaderCell>
            <ListHeaderCell>Category</ListHeaderCell>
            <ListHeaderCell>Price</ListHeaderCell>
            <ListHeaderCell>Stock</ListHeaderCell>
            <ListHeaderCell>Status</ListHeaderCell>
          </ListHeader>
          <ListRows :items="filtered" row-key="sku" v-slot="{ item }">
            <ListRow :value="item.sku">
              <ListCell>
                <div class="flex min-w-0 items-center gap-2.5">
                  <ProductThumb
                    :seed="item.sku"
                    :icon="item.icon"
                    size="size-8"
                    icon-size="size-3.5"
                    :empty="item.images === 0"
                  />
                  <div class="min-w-0">
                    <div class="truncate text-base text-ink-gray-8">{{ item.name }}</div>
                    <div class="truncate text-sm text-ink-gray-5">{{ item.variant }} · {{ item.sku }}</div>
                  </div>
                </div>
              </ListCell>
              <ListCell><span class="truncate text-sm text-ink-gray-7">{{ item.group }}</span></ListCell>
              <ListCell><span class="text-sm text-ink-gray-7 tabular-nums">{{ money(item.price) }}</span></ListCell>
              <ListCell>
                <span class="text-sm tabular-nums" :class="item.stock ? 'text-ink-gray-7' : 'text-ink-gray-4'">
                  {{ item.stock }}
                </span>
              </ListCell>
              <ListCell>
                <Badge v-if="!item.issue" label="Ready" theme="green" variant="subtle" />
                <Tooltip v-else :text="item.issue.text">
                  <div class="flex min-w-0 items-center gap-1.5">
                    <Badge
                      :label="item.issue.level === 'error' ? 'Error' : 'Warning'"
                      :theme="item.issue.level === 'error' ? 'red' : 'orange'"
                      variant="subtle"
                    />
                    <span class="truncate text-sm text-ink-gray-5">{{ item.issue.text }}</span>
                  </div>
                </Tooltip>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>

      <div v-if="!filtered.length" class="flex flex-col items-center justify-center gap-2 py-14 text-center">
        <div class="rounded-full bg-surface-green-2 p-3 text-ink-green-7">
          <span class="lucide-check size-6" aria-hidden="true" />
        </div>
        <p class="text-base text-ink-gray-7">Nothing in this bucket</p>
        <p class="text-sm text-ink-gray-5">Your file is clean on this count.</p>
      </div>

      <div v-else class="border-t border-outline-gray-1 bg-surface-gray-1 px-4 py-2.5 text-sm text-ink-gray-5">
        Showing {{ filtered.length }} of {{ TOTAL_ROWS }} rows
      </div>
    </div>

    <CoachTip
      icon="lucide-shield-check"
      title="Errors do not stop the import"
      text="Every other row goes in, and you get a small file of just the failed rows to fix and upload again."
    />
  </div>
</template>
