<script setup>
import { computed } from 'vue'
import { MultiSelect, Select, TextInput } from 'frappe-ui'
import { collections, productTypes } from '../../data/mock'

const props = defineProps({
  product: { type: Object, required: true },
  layout: { type: String, default: 'stacked' },
})

const typeOptions = productTypes.map((t) => ({ label: t.name, value: t.id }))
const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Draft', value: 'draft' },
  { label: 'Archived', value: 'archived' },
]
const collectionOptions = collections.map((c) => ({ label: c.title, value: c.id }))

const productCollections = computed(() => props.product.collections ?? [])
</script>

<template>
  <section :class="layout === 'stacked' ? '' : 'space-y-4'">
    <h2 v-if="layout === 'stacked'" class="text-lg-semibold text-ink-gray-8">Organisation</h2>
    <h3 v-else class="text-sm text-ink-gray-5">Organisation</h3>

    <div :class="layout === 'stacked' ? 'mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2' : 'mt-4 space-y-4'">
      <Select :model-value="product.status" class="w-full" label="Status" :options="statusOptions" />
      <Select :model-value="product.type" class="w-full" label="Product type" :options="typeOptions" />
      <TextInput :model-value="product.vendor" class="w-full" label="Vendor" />
      <MultiSelect
        :model-value="productCollections"
        class="w-full"
        label="Collections"
        :options="collectionOptions"
      />
      <TextInput
        :model-value="product.tags.join(', ')"
        class="w-full"
        label="Tags"
        :class="layout === 'stacked' ? 'sm:col-span-2' : ''"
      />
    </div>
  </section>
</template>
