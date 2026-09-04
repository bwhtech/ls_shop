<script setup>
import { FormControl } from 'frappe-ui'
import RichTextField from '../RichTextField.vue'
import Thumb from '../Thumb.vue'

defineProps({ product: { type: Object, required: true } })
</script>

<template>
  <section class="space-y-4">
    <FormControl v-model="product.title" label="Title" />
    <RichTextField
      v-model="product.description"
      label="Description"
      description="Shown on the product page."
      min-height="min-h-32"
    />
    <div>
      <p class="mb-1.5 text-base text-ink-gray-6">Media</p>
      <div class="flex flex-wrap gap-2">
        <Thumb :image="product.image" size="size-20" />
        <!-- Item.image is a single field with no admin write path (photos live per
             option, on Style Attribute Variant — see ProductDetail's variant matrix
             and VariantDetail's Photos section), so adding a second template-level
             image here has nothing to call. -->
        <button
          class="grid size-20 place-content-center rounded-4 border border-dashed border-outline-gray-2 text-ink-gray-5 opacity-50"
          aria-label="Add media"
          disabled
        >
          <span class="lucide-plus size-5" aria-hidden="true" />
        </button>
      </div>
    </div>
  </section>
</template>
