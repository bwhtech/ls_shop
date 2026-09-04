<script setup>
import { computed } from 'vue'
import { FormControl, TextInput } from 'frappe-ui'

const props = defineProps({ product: { type: Object, required: true } })

const handle = computed(() => props.product.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''))

// Display-only, unchanged from the prototype: the real SEO fields (route,
// meta_title, meta_description) live per option on Style Attribute Variant —
// each published colour/size gets its own storefront URL — not on the
// product template shown here, and no admin endpoint reads or writes them
// yet. The handle above is computed client-side, same as before.
</script>

<template>
  <section>
    <h2 class="text-lg-semibold text-ink-gray-8">Storefront listing</h2>
    <p class="mt-1 text-p-sm text-ink-gray-5">
      How this product appears on the store and in search results.
    </p>
    <div class="mt-4 space-y-4">
      <TextInput :model-value="`/products/${handle}`" class="w-full" label="URL handle" />
      <TextInput :model-value="product.title" class="w-full" label="Page title" />
      <FormControl
        :model-value="product.description"
        type="textarea"
        label="Meta description"
        :rows="3"
        description="Roughly 160 characters shows in search results."
      />
    </div>
  </section>
</template>
