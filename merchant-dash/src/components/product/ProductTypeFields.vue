<script setup>
import { computed } from 'vue'
import { Button, FormControl, Select } from 'frappe-ui'
import RichTextField from '../RichTextField.vue'
import { productTypes } from '../../data/mock'

const props = defineProps({ product: { type: Object, required: true } })

// The schema — not the product — decides which fields render here. Swap the
// type and a book's ISBN gives way to an apparel product's fabric and fit.
const type = computed(() => productTypes.find((t) => t.id === props.product.type))
</script>

<template>
  <section>
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-8">{{ type.name }} details</h2>
        <p class="mt-1 text-p-sm text-ink-gray-5">
          Fields defined by the {{ type.name }} product type.
        </p>
      </div>
      <Button label="Edit type" variant="ghost" route="/product-types" />
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <template v-for="field in type.fields" :key="field.key">
        <Select
          v-if="field.type === 'select'"
          :model-value="product.typeFields[field.key]"
          class="w-full"
          :label="field.label"
          :options="field.options.map((o) => ({ label: o, value: o }))"
        />
        <!-- A schema field that wants paragraphs gets the editor; the rest are
             one-line values. -->
        <RichTextField
          v-else-if="field.type === 'textarea'"
          v-model="product.typeFields[field.key]"
          class="sm:col-span-2"
          :label="field.label"
        />
        <FormControl
          v-else
          :model-value="String(product.typeFields[field.key] ?? '')"
          :type="field.type === 'number' ? 'number' : 'text'"
          :label="field.label"
        />
      </template>
    </div>
  </section>
</template>
