<script setup>
import { FormControl } from 'frappe-ui'

defineProps({ product: { type: Object, required: true } })
</script>

<template>
  <section>
    <h2 class="text-lg-semibold text-ink-gray-8">Pricing</h2>
    <p v-if="product.hasVariants" class="mt-1 text-p-sm text-ink-gray-5">
      This product has variants — price is set per variant below.
    </p>
    <div v-else class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <FormControl :model-value="String(product.price)" type="number" label="Price" />
      <FormControl :model-value="product.compareAt ? String(product.compareAt) : ''" type="number" label="Compare at" />
      <FormControl
        :model-value="String(Math.round(product.price * 0.55))"
        type="number"
        label="Cost"
        description="Not shown to customers."
      />
    </div>
  </section>
</template>
