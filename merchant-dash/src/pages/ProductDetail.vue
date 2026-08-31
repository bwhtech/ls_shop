<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dropdown, ScrollArea, toast } from 'frappe-ui'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import StatusBadge from '../components/StatusBadge.vue'
import VariantEditor from '../components/VariantEditor.vue'
import ProductBasics from '../components/product/ProductBasics.vue'
import ProductTypeFields from '../components/product/ProductTypeFields.vue'
import ProductPricing from '../components/product/ProductPricing.vue'
import ProductStock from '../components/product/ProductStock.vue'
import ProductOrganization from '../components/product/ProductOrganization.vue'
import ProductStorefront from '../components/product/ProductStorefront.vue'
import ProductSummaryPanel from '../components/product/ProductSummaryPanel.vue'
import { products } from '../data/mock'
import { longDate } from '../data/format'
import { useProductStats } from '../data/product'
import { asDropdownOptions, buildProductActions } from '../ia/productActions'

const route = useRoute()
const router = useRouter()

const product = computed(() => products.find((p) => p.id === route.params.id) ?? products[0])
const stats = useProductStats(product)
const actions = computed(() => buildProductActions(product.value, router))

// Stand-in for form state: any edit in the prototype arms the save affordances.
const dirty = ref(false)
watch(() => route.params.id, () => (dirty.value = false))

function save() {
  dirty.value = false
  toast.success('Saved')
}
</script>

<template>
  <AppPageHeader
    :title="product.title"
    back-to="/products"
    :breadcrumbs="[{ label: 'Products', route: '/products' }, { label: product.title }]"
  >
    <template #actions>
      <Dropdown :options="asDropdownOptions(actions.groups)">
        <Button icon="lucide-ellipsis" label="More actions" />
      </Dropdown>
      <Button label="Save" variant="solid" theme="gray" @click="save" />
    </template>
  </AppPageHeader>

  <!-- Two panes, each with its own scroll: the form is long and the summary
       beside it should stay put while you work down the form. -->
  <div class="flex min-h-0 flex-1 overflow-hidden">
    <ScrollArea class="min-w-0 flex-1">
      <PageBody width="narrow">
        <div class="flex flex-wrap items-center gap-2">
          <StatusBadge :status="product.status" />
          <span class="text-sm text-ink-gray-5">
            {{ product.sku }} · updated {{ longDate(product.updated) }}
          </span>
        </div>

        <div class="mt-6 space-y-11">
          <ProductBasics :product="product" />
          <ProductTypeFields :product="product" />
          <ProductPricing :product="product" />
          <VariantEditor :product="product" />
          <ProductStock :product="product" />
          <ProductStorefront :product="product" />
          <ProductOrganization :product="product" />
        </div>
      </PageBody>
    </ScrollArea>

    <aside class="hidden w-[19rem] shrink-0 flex-col border-l border-outline-gray-1 lg:flex">
      <ScrollArea class="min-h-0 flex-1">
        <ProductSummaryPanel :product="product" :stats="stats" />
      </ScrollArea>
    </aside>
  </div>
</template>
