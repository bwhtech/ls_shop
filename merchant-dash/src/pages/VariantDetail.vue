<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Button, FormControl, TextInput, toast } from 'frappe-ui'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import Thumb from '../components/Thumb.vue'
import VariantMedia from '../components/VariantMedia.vue'
import { inventory, products } from '../data/mock'

const route = useRoute()
const product = computed(() => products.find((p) => p.id === route.params.id) ?? products[0])
const variant = computed(
  () => product.value.variants.find((v) => v.id === route.params.variantId) ?? product.value.variants[0],
)
const stockRows = computed(() => inventory.filter((row) => row.variantId === variant.value?.id))
</script>

<template>
  <AppPageHeader
    :title="variant?.title ?? product.title"
    :back-to="`/products/${product.id}`"
    :breadcrumbs="[
      { label: 'Products', route: '/products' },
      { label: product.title, route: `/products/${product.id}` },
      { label: variant?.title ?? '—' },
    ]"
  >
    <template #actions>
      <Button label="Save" variant="solid" theme="gray" @click="toast.success('Variant saved')" />
    </template>
  </AppPageHeader>

  <PageBody width="narrow">
    <div class="flex items-center gap-3">
      <Thumb :emoji="variant.thumb" size="size-16" />
      <div>
        <p class="text-base text-ink-gray-8">{{ product.title }}</p>
        <p class="mt-1 text-sm text-ink-gray-5">{{ variant.title }}</p>
      </div>
    </div>

    <div class="mt-8 space-y-11">
      <section>
        <h2 class="text-lg-semibold text-ink-gray-8">Photos</h2>
        <p class="mt-1 text-p-sm text-ink-gray-5">
          Shown when a shopper picks this combination. The first one is the cover.
        </p>
        <VariantMedia class="mt-4" :variant="variant" :thumb="variant.thumb" />
      </section>

      <section>
        <h2 class="text-lg-semibold text-ink-gray-8">Options</h2>
        <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextInput
            v-for="part in variant.combo"
            :key="part.name"
            :model-value="part.value"
            class="w-full"
            :label="part.name"
          />
        </div>
      </section>

      <section>
        <h2 class="text-lg-semibold text-ink-gray-8">Pricing and identifiers</h2>
        <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl :model-value="String(variant.price)" type="number" label="Price" />
          <FormControl :model-value="variant.compareAt ? String(variant.compareAt) : ''" type="number" label="Compare at" />
          <FormControl :model-value="variant.sku" label="SKU" />
          <FormControl :model-value="variant.barcode" label="Barcode" />
        </div>
      </section>

      <section>
        <h2 class="text-lg-semibold text-ink-gray-8">Stock</h2>
        <div class="mt-4 divide-y divide-outline-gray-1 border-y border-outline-gray-1">
          <div v-for="row in stockRows" :key="row.id" class="flex items-center justify-between py-3">
            <span class="text-base text-ink-gray-7">{{ row.location }}</span>
            <TextInput :model-value="String(row.onHand)" size="sm" class="w-20" />
          </div>
        </div>
      </section>
    </div>
  </PageBody>
</template>
