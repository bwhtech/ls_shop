<script setup>
import { computed } from 'vue'
import { Alert, Badge, Button, Select, Tooltip } from 'frappe-ui'
import { CSV_COLUMNS, TARGET_FIELDS, imp } from '../../../data/importFlow'
import CoachTip from '../CoachTip.vue'

const mapped = computed(() => Object.values(imp.mapping).filter(Boolean).length)
const skipped = computed(() => CSV_COLUMNS.length - mapped.value)

const required = ['item_name', 'item_code', 'price']
const missing = computed(() => required.filter((f) => !Object.values(imp.mapping).includes(f)))

const labelFor = (v) => TARGET_FIELDS.find((f) => f.value === v)?.label ?? ''

const confidenceTheme = { high: 'green', medium: 'orange', low: 'gray', none: 'gray' }
const confidenceLabel = { high: 'Sure', medium: 'Likely', low: 'Guess', none: 'No match' }

function resetToSuggested() {
  for (const c of CSV_COLUMNS) imp.mapping[c.header] = c.target
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-start gap-4">
      <div class="min-w-0 flex-1">
        <h2 class="text-xl text-ink-gray-9">Match your columns</h2>
        <p class="mt-1 text-p-base text-ink-gray-6">
          We matched {{ CSV_COLUMNS.filter((c) => c.target).length }} of {{ CSV_COLUMNS.length }}
          columns for you. Change anything that looks wrong.
        </p>
      </div>
      <Button
        class="shrink-0"
        variant="subtle"
        icon-left="lucide-wand-sparkles"
        label="Use suggestions"
        @click="resetToSuggested"
      />
    </div>

    <Alert v-if="missing.length" theme="red" :title="'Still needed: ' + missing.map(labelFor).join(', ')" />

    <div class="overflow-hidden rounded-5 border border-outline-gray-1">
      <div
        class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_6rem] gap-4 border-b border-outline-gray-1 bg-surface-gray-1 px-5 py-3"
      >
        <span class="text-sm text-ink-gray-5">Column in your file</span>
        <span class="text-sm text-ink-gray-5">Goes into</span>
        <span class="text-right text-sm text-ink-gray-5">Match</span>
      </div>

      <div class="divide-y divide-outline-gray-1">
        <div
          v-for="c in CSV_COLUMNS"
          :key="c.header"
          class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_6rem] items-center gap-4 px-5 py-3.5"
        >
          <div class="min-w-0">
            <div class="truncate text-base text-ink-gray-8">{{ c.header }}</div>
            <Tooltip :text="'First value: ' + c.sample">
              <div class="mt-0.5 truncate text-sm text-ink-gray-5">{{ c.sample }}</div>
            </Tooltip>
          </div>

          <div class="flex items-center gap-2">
            <span class="lucide-arrow-right size-3.5 shrink-0 text-ink-gray-4" aria-hidden="true" />
            <Select v-model="imp.mapping[c.header]" :options="TARGET_FIELDS" class="min-w-0 flex-1" />
          </div>

          <div class="flex justify-end">
            <Badge
              :label="imp.mapping[c.header] ? confidenceLabel[c.confidence] : 'Skipped'"
              :theme="imp.mapping[c.header] ? confidenceTheme[c.confidence] : 'gray'"
              variant="subtle"
            />
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4 border-t border-outline-gray-1 bg-surface-gray-1 px-4 py-2.5">
        <span class="text-sm text-ink-gray-6">{{ mapped }} columns mapped</span>
        <span class="text-sm text-ink-gray-5">{{ skipped }} skipped</span>
      </div>
    </div>

    <CoachTip
      title="Skipping a column is safe"
      text="Anything you leave out never reaches your catalogue, and your own file stays untouched."
    />
  </div>
</template>
