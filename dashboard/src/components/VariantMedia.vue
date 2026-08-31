<script setup>
/**
 * Photos for one variant. The first one is the cover — it is what the
 * storefront swaps to when a shopper picks this colour or size.
 */
import { Badge, Button, toast } from 'frappe-ui'

const props = defineProps({
  variant: { type: Object, required: true },
  thumb: { type: String, default: '🖼️' },
})

function add() {
  props.variant.images += 1
  toast.success(`Photo added to ${props.variant.title}`)
}

function remove() {
  if (props.variant.images > 0) props.variant.images -= 1
}
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-2">
      <div
        v-for="n in variant.images"
        :key="n"
        class="group relative grid size-20 place-content-center rounded-4 border border-outline-gray-1 bg-surface-gray-2 text-2xl"
      >
        <span aria-hidden="true">{{ thumb }}</span>
        <Badge v-if="n === 1" class="absolute inset-x-1 bottom-1" label="Cover" variant="subtle" />
        <Button
          class="absolute right-1 top-1 opacity-0 transition-opacity group-hover:opacity-100"
          icon="lucide-x"
          label="Remove photo"
          @click="remove"
        />
      </div>

      <button
        class="grid size-20 place-content-center rounded-4 border border-dashed border-outline-gray-2 text-ink-gray-5 hover:bg-surface-gray-1"
        aria-label="Add photo"
        @click="add"
      >
        <span class="flex flex-col items-center gap-1">
          <span class="lucide-plus size-5" aria-hidden="true" />
          <span class="text-sm">Add</span>
        </span>
      </button>
    </div>

    <p v-if="!variant.images" class="mt-2 text-p-sm text-ink-gray-5">
      No photo yet — this variant falls back to the product's own images on the storefront.
    </p>
  </div>
</template>
