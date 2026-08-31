<script setup>
import { ref } from 'vue'
import { Button, Progress, Spinner, toast } from 'frappe-ui'
import { CSV_COLUMNS, TOTAL_ROWS, delay, imp } from '../../../data/importFlow'
import CoachTip from '../CoachTip.vue'

const dragging = ref(false)
const pct = ref(0)

function pick() {
  imp.parsing = true
  imp.parsed = false
  pct.value = 0
  imp.file = { name: 'kirana-catalogue-aug.csv', size: '312 KB', rows: TOTAL_ROWS }

  const tick = () => {
    pct.value = Math.min(100, pct.value + 20)
    if (pct.value < 100) setTimeout(tick, delay(180))
    else
      setTimeout(() => {
        imp.parsing = false
        imp.parsed = true
        toast.success(`${TOTAL_ROWS} rows read from ${imp.file.name}`)
      }, delay(250))
  }
  setTimeout(tick, delay(180))
}

function clear() {
  imp.file = null
  imp.parsed = false
  pct.value = 0
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl text-ink-gray-9">Upload your product file</h2>
      <p class="mt-1.5 text-p-base text-ink-gray-6">
        CSV or Excel, up to 10 MB. Column names can be anything, we work them out next.
      </p>
    </div>

    <div
      v-if="!imp.file"
      class="flex flex-col items-center justify-center rounded-5 border-2 border-dashed px-6 py-14 text-center transition"
      :class="dragging ? 'border-outline-gray-4 bg-surface-gray-2' : 'border-outline-gray-2 bg-surface-gray-1'"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="((dragging = false), pick())"
    >
      <div class="flex size-11 items-center justify-center rounded-full bg-surface-base text-ink-gray-6 shadow-sm">
        <span class="lucide-upload size-5" aria-hidden="true" />
      </div>
      <p class="mt-3 text-base text-ink-gray-7">Drop your spreadsheet here</p>
      <p class="mt-1 text-sm text-ink-gray-5">or</p>
      <Button class="mt-2" variant="solid" theme="gray" label="Browse files" @click="pick" />
      <div class="mt-5 flex items-center gap-4 text-sm text-ink-gray-5">
        <span>.csv</span>
        <span>.xlsx</span>
        <span>Max 10 MB</span>
      </div>
    </div>

    <div v-else class="rounded-5 border border-outline-gray-1 p-4">
      <div class="flex items-center gap-3">
        <div class="flex size-9 items-center justify-center rounded-4 bg-surface-green-2 text-ink-green-7">
          <span class="lucide-file-spreadsheet size-4" aria-hidden="true" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="truncate text-base-semibold text-ink-gray-8">{{ imp.file.name }}</div>
          <div class="mt-0.5 text-sm text-ink-gray-5">
            {{ imp.file.size }}
            <template v-if="imp.parsed"> · {{ imp.file.rows }} rows · {{ CSV_COLUMNS.length }} columns</template>
          </div>
        </div>
        <Spinner v-if="imp.parsing" class="size-4" />
        <Button v-else variant="ghost" icon="lucide-x" label="Remove file" @click="clear" />
      </div>

      <Progress v-if="imp.parsing" :value="pct" size="sm" class="mt-4" />
      <p v-if="imp.parsing" class="mt-2 text-sm text-ink-gray-5">Reading rows and sniffing column types…</p>

      <div v-if="imp.parsed" class="mt-4 overflow-x-auto rounded-4 border border-outline-gray-1">
        <table class="w-full min-w-[42rem] border-collapse text-left">
          <thead class="bg-surface-gray-1">
            <tr>
              <th
                v-for="c in CSV_COLUMNS.slice(0, 5)"
                :key="c.header"
                class="whitespace-nowrap px-3 py-2 text-sm font-normal text-ink-gray-5"
              >
                {{ c.header }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-gray-1">
            <tr v-for="n in 3" :key="n">
              <td
                v-for="c in CSV_COLUMNS.slice(0, 5)"
                :key="c.header"
                class="truncate px-3 py-2 text-sm text-ink-gray-7"
              >
                {{ c.sample }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="imp.parsed" class="mt-2 text-sm text-ink-gray-5">
        Showing the first 3 of {{ imp.file.rows }} rows.
      </p>
    </div>

    <CoachTip
      v-if="!imp.file"
      icon="lucide-download"
      title="Starting from scratch?"
      text="Download our template spreadsheet, fill it in, and drop it back here."
    />
    <CoachTip
      v-else-if="imp.parsed"
      theme="orange"
      icon="lucide-triangle-alert"
      title="A few rows look odd"
      text="That is fine. We show you exactly which ones before anything is saved."
    />
  </div>
</template>
