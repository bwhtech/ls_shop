<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Badge, Button, Progress, Spinner } from 'frappe-ui'
import { IMPORT_ROWS, closeImport, counts, delay, imp } from '../../../data/importFlow'
import { openSettings } from '../../../ia/settings'
import ProductThumb from '../ProductThumb.vue'

const LOG = [
  'Creating 2 new categories',
  'Importing products 1 to 50',
  'Importing products 51 to 100',
  'Importing products 101 to 119',
  'Attaching 356 photos',
  'Rebuilding search index',
  'Publishing to your storefront',
]

function run() {
  if (imp.running || imp.finished) return
  imp.running = true
  imp.progress = 0
  imp.log = []
  let i = 0
  const tick = () => {
    imp.log = [...imp.log, LOG[i]]
    imp.progress = Math.round(((i + 1) / LOG.length) * 100)
    i += 1
    if (i < LOG.length) setTimeout(tick, delay(500))
    else
      setTimeout(() => {
        imp.running = false
        imp.finished = true
      }, delay(500))
  }
  setTimeout(tick, delay(400))
}

onMounted(run)

const router = useRouter()

function finish(path) {
  closeImport()
  router.push(path)
}

const NEXT = [
  { icon: 'lucide-credit-card', title: 'Turn on payments', body: 'Accept cards and UPI at checkout.', run: () => (closeImport(), openSettings('payments')) },
  { icon: 'lucide-truck', title: 'Set shipping rates', body: 'Flat rate, or by weight and pin code.', run: () => (closeImport(), openSettings('shipping')) },
  { icon: 'lucide-globe', title: 'Set up the storefront', body: 'Theme, navigation and pages.', run: () => finish('/storefront/theme') },
]

const withPhotos = computed(() => IMPORT_ROWS.filter((r) => r.images > 0).slice(0, 8))
</script>

<template>
  <div class="space-y-6">
    <!-- Running -->
    <template v-if="!imp.finished">
      <div>
        <h2 class="text-xl text-ink-gray-9">Importing your catalogue</h2>
        <p class="mt-1 text-p-base text-ink-gray-6">
          This keeps running if you close the tab. We will email you when it is done.
        </p>
      </div>

      <div class="rounded-5 border border-outline-gray-1 p-5">
        <div class="flex items-center gap-3">
          <Spinner class="size-4" />
          <span class="text-base text-ink-gray-8">{{ imp.log[imp.log.length - 1] ?? 'Getting ready' }}</span>
          <span class="ml-auto text-sm text-ink-gray-5 tabular-nums">{{ imp.progress }}%</span>
        </div>
        <Progress :value="imp.progress" size="sm" class="mt-4" />

        <div class="mt-4 space-y-1.5">
          <div v-for="(l, i) in imp.log" :key="l" class="flex items-center gap-2">
            <span v-if="i < imp.log.length - 1" class="lucide-check size-3.5 text-ink-green-6" aria-hidden="true" />
            <Spinner v-else class="size-3.5" />
            <span class="text-sm" :class="i < imp.log.length - 1 ? 'text-ink-gray-5' : 'text-ink-gray-8'">{{ l }}</span>
          </div>
        </div>
      </div>

      <Alert description="Products appear in your catalogue as they land, so you can start editing right away." />
    </template>

    <!-- Done -->
    <template v-else>
      <div class="rounded-6 border border-outline-gray-1 px-6 py-8 text-center">
        <div class="mx-auto flex size-12 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-7">
          <span class="lucide-party-popper size-6" aria-hidden="true" />
        </div>
        <h2 class="mt-4 text-2xl text-ink-gray-9">{{ counts.ready }} products are live</h2>
        <p class="mx-auto mt-1.5 max-w-[460px] text-p-base text-ink-gray-6">
          Your storefront now has a catalogue. Photos are attached and categories are set up.
        </p>

        <div class="mt-5 flex flex-wrap justify-center gap-2">
          <ProductThumb v-for="p in withPhotos" :key="p.sku" :seed="p.sku" :icon="p.icon" size="size-12" />
        </div>

        <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
          <Button variant="solid" theme="gray" label="View my products" @click="finish('/products')" />
          <Button label="Back to overview" @click="finish('/')" />
          <Button variant="ghost" icon-left="lucide-undo-2" label="Undo this import" />
        </div>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-5 border border-outline-gray-1 p-4">
          <div class="text-2xl text-ink-gray-9 tabular-nums">{{ counts.ready }}</div>
          <div class="mt-0.5 text-sm text-ink-gray-5">products created</div>
        </div>
        <div class="rounded-5 border border-outline-gray-1 p-4">
          <div class="text-2xl text-ink-gray-9 tabular-nums">356</div>
          <div class="mt-0.5 text-sm text-ink-gray-5">photos attached</div>
        </div>
        <div class="rounded-5 border border-outline-gray-1 p-4">
          <div class="flex items-baseline gap-2">
            <span class="text-2xl text-ink-red-6 tabular-nums">{{ counts.errors }}</span>
            <Badge label="Fix and re-upload" theme="red" variant="subtle" />
          </div>
          <div class="mt-0.5 text-sm text-ink-gray-5">rows skipped</div>
        </div>
      </div>

      <Alert
        theme="orange"
        title="3 rows need a fix"
        description="We put just those rows in a small file, so you can correct them and upload again."
        :primary-action="{ label: 'Download error rows', iconLeft: 'lucide-download' }"
      />

      <div class="rounded-5 border border-outline-gray-1 p-4">
        <div class="text-base-semibold text-ink-gray-8">What usually comes next</div>
        <div class="mt-3 divide-y divide-outline-gray-1">
          <div v-for="n in NEXT" :key="n.title" class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
            <span :class="[n.icon, 'size-4 text-ink-gray-6']" aria-hidden="true" />
            <div class="min-w-0 flex-1">
              <div class="text-base text-ink-gray-8">{{ n.title }}</div>
              <div class="text-sm text-ink-gray-5">{{ n.body }}</div>
            </div>
            <Button variant="subtle" label="Start" @click="n.run" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
