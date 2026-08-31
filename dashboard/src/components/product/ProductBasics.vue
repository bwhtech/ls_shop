<script setup>
import { FormControl } from 'frappe-ui'
import RichTextField from '../RichTextField.vue'
import Thumb from '../Thumb.vue'

defineProps({ product: { type: Object, required: true } })
</script>

<template>
  <section class="space-y-4">
    <FormControl :model-value="product.title" label="Title" />
    <RichTextField
      v-model="product.description"
      label="Description"
      description="Shown on the product page."
      min-height="min-h-32"
    />
    <div>
      <p class="mb-1.5 text-base text-ink-gray-6">Media</p>
      <div class="flex flex-wrap gap-2">
        <Thumb :emoji="product.thumb" size="size-20" />
        <Thumb emoji="🖼️" size="size-20" />
        <button
          class="grid size-20 place-content-center rounded-4 border border-dashed border-outline-gray-2 text-ink-gray-5 hover:bg-surface-gray-1"
          aria-label="Add media"
        >
          <span class="lucide-plus size-5" aria-hidden="true" />
        </button>
      </div>
    </div>
  </section>
</template>
