<script setup>
/**
 * One variant, everything about it: its own price, stock, identifiers and
 * photos. A variant is a small record, so it opens over the product rather
 * than taking you away from the matrix you were working down.
 */
import { Badge, Button, Dialog, FormControl, toast } from 'frappe-ui'
import VariantMedia from './VariantMedia.vue'

const props = defineProps({
  variant: { type: Object, default: null },
  product: { type: Object, required: true },
})

const open = defineModel('open', { type: Boolean, default: false })

function save() {
  open.value = false
  toast.success(`${props.variant.title} saved`)
}
</script>

<template>
  <Dialog v-model:open="open" size="2xl" :title="variant ? variant.title : 'Variant'">
    <div v-if="variant" class="space-y-6">
      <div class="flex flex-wrap items-center gap-1.5">
        <Badge v-for="part in variant.combo" :key="part.name" :label="`${part.name} · ${part.value}`" variant="subtle" />
        <span class="text-sm text-ink-gray-5">of {{ product.title }}</span>
      </div>

      <section>
        <h3 class="text-base-semibold text-ink-gray-8">Photos</h3>
        <p class="mt-1 text-p-sm text-ink-gray-5">
          Shown when a shopper picks this combination. The first one is the cover.
        </p>
        <VariantMedia class="mt-3" :variant="variant" :thumb="variant.thumb" />
      </section>

      <section>
        <h3 class="text-base-semibold text-ink-gray-8">Pricing and stock</h3>
        <div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl v-model.number="variant.price" type="number" label="Price" />
          <FormControl v-model.number="variant.compareAt" type="number" label="Compare at" />
          <FormControl v-model.number="variant.stock" type="number" label="On hand" />
          <FormControl v-model.number="variant.committed" type="number" label="Committed" />
        </div>
      </section>

      <section>
        <h3 class="text-base-semibold text-ink-gray-8">Identifiers</h3>
        <div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl v-model="variant.sku" label="SKU" />
          <FormControl v-model="variant.barcode" label="Barcode" />
        </div>
      </section>

      <div class="flex items-center gap-2 pt-2">
        <Button
          label="Open full page"
          icon-left="lucide-external-link"
          :route="`/products/${product.id}/variants/${variant.id}`"
        />
        <div class="ml-auto flex gap-2">
          <Button label="Cancel" @click="open = false" />
          <Button label="Save variant" variant="solid" theme="gray" @click="save" />
        </div>
      </div>
    </div>
  </Dialog>
</template>
