<script setup>
/**
 * Photos for a whole matrix in one go. The zip carries one folder per variant,
 * named after its SKU, and every image inside that folder lands on that
 * variant — which is the only way this is bearable at 12 variants a product.
 */
import { computed, ref } from 'vue'
import { Badge, Button, Dialog, Progress, toast } from 'frappe-ui'

const props = defineProps({ product: { type: Object, required: true } })
const open = defineModel('open', { type: Boolean, default: false })

const state = ref('idle') // idle | uploading | done
const pct = ref(0)
const result = ref({ matched: 0, images: 0, unmatched: [] })

const skus = computed(() => props.product.variants.map((v) => v.sku))

function upload() {
  state.value = 'uploading'
  pct.value = 0

  const tick = () => {
    pct.value = Math.min(100, pct.value + 14)
    if (pct.value < 100) return setTimeout(tick, 140)

    // Every folder but the last two matches a SKU; the rest are reported back
    // rather than silently dropped.
    let images = 0
    props.product.variants.forEach((variant, i) => {
      if (i >= props.product.variants.length - 1) return
      const added = 2 + (i % 2)
      variant.images += added
      images += added
    })

    result.value = {
      matched: Math.max(0, props.product.variants.length - 1),
      images,
      unmatched: ['shoot-final/', 'IMG_4471/'],
    }
    state.value = 'done'
    toast.success(`${images} photos attached to ${result.value.matched} variants`)
  }
  setTimeout(tick, 140)
}

function reset() {
  state.value = 'idle'
  pct.value = 0
}

function close() {
  open.value = false
  setTimeout(reset, 200)
}
</script>

<template>
  <Dialog v-model:open="open" size="2xl" title="Import variant photos">
    <div class="space-y-5">
      <template v-if="state === 'idle'">
        <div
          class="flex flex-col items-center justify-center rounded-5 border-2 border-dashed border-outline-gray-2 bg-surface-gray-1 px-6 py-10 text-center"
          @dragover.prevent
          @drop.prevent="upload"
        >
          <div class="flex size-11 items-center justify-center rounded-full bg-surface-base text-ink-gray-6 shadow-sm">
            <span class="lucide-folder-archive size-5" aria-hidden="true" />
          </div>
          <p class="mt-3 text-base text-ink-gray-7">Drop a .zip of folders</p>
          <p class="mt-1 max-w-[420px] text-p-sm text-ink-gray-5">
            One folder per variant, named after its SKU. Everything inside that folder is attached
            to that variant, in file order.
          </p>
          <Button class="mt-3" variant="solid" theme="gray" label="Choose a zip file" @click="upload" />
        </div>

        <div class="rounded-5 border border-outline-gray-1 p-4">
          <p class="text-base-semibold text-ink-gray-8">What the zip should look like</p>
          <ul class="mt-2 space-y-1 font-mono text-sm text-ink-gray-6">
            <li v-for="sku in skus.slice(0, 3)" :key="sku">
              {{ sku }}/ <span class="text-ink-gray-4">1.jpg, 2.jpg …</span>
            </li>
            <li class="text-ink-gray-4">…</li>
          </ul>
        </div>
      </template>

      <template v-else-if="state === 'uploading'">
        <div class="rounded-5 border border-outline-gray-1 p-4">
          <div class="flex items-center gap-3">
            <span class="lucide-folder-archive size-4 text-ink-gray-6" aria-hidden="true" />
            <span class="text-base text-ink-gray-8">Reading folders and matching SKUs…</span>
            <span class="ml-auto text-sm text-ink-gray-5 tabular-nums">{{ pct }}%</span>
          </div>
          <Progress :value="pct" size="sm" class="mt-3" />
        </div>
      </template>

      <template v-else>
        <div class="grid gap-4 sm:grid-cols-3">
          <div class="rounded-5 border border-outline-gray-1 p-4">
            <div class="text-2xl text-ink-gray-9 tabular-nums">{{ result.images }}</div>
            <div class="mt-0.5 text-sm text-ink-gray-5">photos attached</div>
          </div>
          <div class="rounded-5 border border-outline-gray-1 p-4">
            <div class="text-2xl text-ink-gray-9 tabular-nums">{{ result.matched }}</div>
            <div class="mt-0.5 text-sm text-ink-gray-5">variants matched</div>
          </div>
          <div class="rounded-5 border border-outline-gray-1 p-4">
            <div class="text-2xl text-ink-amber-7 tabular-nums">{{ result.unmatched.length }}</div>
            <div class="mt-0.5 text-sm text-ink-gray-5">folders unmatched</div>
          </div>
        </div>

        <div v-if="result.unmatched.length" class="rounded-5 border border-outline-gray-1">
          <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-3">
            <span class="text-base-semibold text-ink-gray-8">Folders with no matching SKU</span>
            <Badge :label="String(result.unmatched.length)" theme="orange" variant="subtle" />
          </div>
          <div class="divide-y divide-outline-gray-1">
            <div v-for="folder in result.unmatched" :key="folder" class="flex items-center gap-3 px-4 py-3">
              <span class="lucide-folder size-4 text-ink-gray-5" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate font-mono text-sm text-ink-gray-7">{{ folder }}</span>
              <span class="text-sm text-ink-gray-5">Left out</span>
            </div>
          </div>
        </div>
      </template>

      <div class="flex justify-end gap-2 pt-1">
        <Button v-if="state === 'done'" label="Import another zip" @click="reset" />
        <Button
          :label="state === 'done' ? 'Done' : 'Cancel'"
          :variant="state === 'done' ? 'solid' : 'subtle'"
          theme="gray"
          @click="close"
        />
      </div>
    </div>
  </Dialog>
</template>
