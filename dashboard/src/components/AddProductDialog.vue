<script setup>
/**
 * Create a sellable product in one screen: catalog.create_product does the rest
 * (Item template + variants, Style Attribute Configurator, generate_variants, prices).
 * Company, warehouse, price list, UOM and naming series are resolved server-side —
 * this dialog never shows an ERPNext concept the owner did not ask for.
 */
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Button, Dialog, FormControl, Select, dialog, toast } from 'frappe-ui'
import { useAdminAction, useAdminRead } from '../data/api'
import { addProduct, closeAddProduct } from '../data/addProduct'

const router = useRouter()

const title = ref('')
const collection = ref('')
const optionAttribute = ref('Color')
const colors = ref([])
const newColor = ref('')
const sizes = ref([])
const newSize = ref('')
const compareAt = ref(null)
const price = ref(null)

function resetForm() {
  title.value = ''
  collection.value = ''
  optionAttribute.value = 'Color'
  colors.value = []
  newColor.value = ''
  sizes.value = []
  newSize.value = ''
  compareAt.value = null
  price.value = null
}

watch(
  () => addProduct.open,
  (open) => {
    if (open) resetForm()
  },
)

const collectionsRequest = useAdminRead('catalog.get_collections')
const collectionOptions = computed(() => [
  { label: 'Select a collection', value: '' },
  ...(collectionsRequest.data ?? []).map((name) => ({ label: name, value: name })),
])

const createCollectionAction = useAdminAction('catalog.create_collection')
function addCollection() {
  dialog.prompt({
    title: 'New collection',
    fields: [{ name: 'title', label: 'Name', required: true }],
    onConfirm: async ({ values }) => {
      await createCollectionAction.submit({ title: values.title })
      if (createCollectionAction.error) return
      await collectionsRequest.reload()
      collection.value = values.title
      toast.success(`"${values.title}" created`)
    },
  })
}

// Every product this store sells is built on its own Color/Size pair — Size has to keep that
// exact spelling (generate_variants() depends on it; see catalog.create_product's Trap 2 guard),
// so the option axis is any OTHER attribute and Size is fixed, not picked.
const attributesRequest = useAdminRead('catalog.get_attributes')
const attributes = computed(() => attributesRequest.data ?? [])
const sizeAttributeExists = computed(() => attributes.value.some((a) => a.name === 'Size'))
const optionAttributeOptions = computed(() =>
  attributes.value.filter((a) => a.name !== 'Size').map((a) => ({ label: a.name, value: a.name })),
)
watch(attributes, (list) => {
  if (!list.some((a) => a.name === optionAttribute.value)) {
    optionAttribute.value = list.find((a) => a.name === 'Color')?.name ?? list.find((a) => a.name !== 'Size')?.name ?? ''
  }
})

const colorSuggestionsRequest = useAdminRead('catalog.get_attribute_values', {
  params: () => ({ attribute: optionAttribute.value }),
  refetch: true,
})
const colorSuggestions = computed(() => (colorSuggestionsRequest.data ?? []).filter((v) => !colors.value.includes(v)))

const sizeSuggestionsRequest = useAdminRead('catalog.get_attribute_values', {
  params: () => ({ attribute: 'Size' }),
})
const sizeSuggestions = computed(() => (sizeSuggestionsRequest.data ?? []).filter((v) => !sizes.value.includes(v)))

function addColor(value) {
  const trimmed = (value ?? newColor.value).trim()
  if (trimmed && !colors.value.some((c) => c.toLowerCase() === trimmed.toLowerCase())) colors.value.push(trimmed)
  newColor.value = ''
}
function removeColor(value) {
  colors.value = colors.value.filter((c) => c !== value)
}

function addSize(value) {
  const trimmed = (value ?? newSize.value).trim()
  if (trimmed && !sizes.value.some((s) => s.toLowerCase() === trimmed.toLowerCase())) sizes.value.push(trimmed)
  newSize.value = ''
}
function removeSize(value) {
  sizes.value = sizes.value.filter((s) => s !== value)
}

const canSubmit = computed(
  () =>
    title.value.trim() &&
    collection.value &&
    optionAttribute.value &&
    sizeAttributeExists.value &&
    colors.value.length &&
    sizes.value.length,
)

const createAction = useAdminAction('catalog.create_product')

async function submit() {
  if (!canSubmit.value) return

  await createAction.submit({
    title: title.value.trim(),
    collection: collection.value,
    option_attribute: optionAttribute.value,
    size_attribute: 'Size',
    option_sizes: colors.value.map((option) => ({ option, sizes: sizes.value })),
    price: compareAt.value || undefined,
    sale_price: price.value || undefined,
  })
  // A failure (missing collection, colliding abbreviation, wrong size attribute…) already
  // toasted inside useAdminAction — the form stays open so the owner can fix it and resubmit.
  if (createAction.error) return

  const created = createAction.data
  toast.success(`"${title.value}" created`)
  closeAddProduct()
  router.push(`/products/${created.name}`)
}
</script>

<template>
  <Dialog v-model:open="addProduct.open" size="xl" title="Add product" @update:open="(v) => (v ? null : closeAddProduct())">
    <template #body-content>
      <div class="space-y-5">
        <FormControl v-model="title" label="Title" placeholder="Cotton oversized tee" required />

        <div>
          <span class="mb-1.5 block text-base text-ink-gray-6">Collection</span>
          <div class="flex gap-2">
            <Select v-model="collection" class="min-w-0 flex-1" :options="collectionOptions" />
            <Button label="New" icon-left="lucide-plus" @click="addCollection" />
          </div>
        </div>

        <FormControl
          v-if="optionAttributeOptions.length > 1"
          v-model="optionAttribute"
          type="select"
          label="Option"
          :options="optionAttributeOptions"
          description="Sizes are added below and apply to every option."
        />

        <div>
          <span class="mb-1.5 block text-base text-ink-gray-6">{{ optionAttribute || 'Options' }}</span>
          <div class="flex flex-wrap items-center gap-1.5">
            <span
              v-for="value in colors"
              :key="value"
              class="flex items-center gap-1 rounded-1 bg-surface-gray-2 py-0.5 pl-2 pr-1 text-sm text-ink-gray-7"
            >
              {{ value }}
              <button type="button" class="lucide-x size-3.5 text-ink-gray-5" aria-label="Remove" @click="removeColor(value)" />
            </span>
            <input
              v-model="newColor"
              list="add-product-color-suggestions"
              class="min-w-32 flex-1 border-none bg-transparent text-base text-ink-gray-8 outline-none placeholder:text-ink-gray-4"
              :placeholder="colors.length ? 'Add another' : `e.g. Black, Sand`"
              @keydown.enter.prevent="addColor()"
              @blur="addColor()"
            />
            <datalist id="add-product-color-suggestions">
              <option v-for="value in colorSuggestions" :key="value" :value="value" />
            </datalist>
          </div>
        </div>

        <div>
          <span class="mb-1.5 block text-base text-ink-gray-6">Sizes</span>
          <div class="flex flex-wrap items-center gap-1.5">
            <span
              v-for="value in sizes"
              :key="value"
              class="flex items-center gap-1 rounded-1 bg-surface-gray-2 py-0.5 pl-2 pr-1 text-sm text-ink-gray-7"
            >
              {{ value }}
              <button type="button" class="lucide-x size-3.5 text-ink-gray-5" aria-label="Remove" @click="removeSize(value)" />
            </span>
            <input
              v-model="newSize"
              list="add-product-size-suggestions"
              class="min-w-32 flex-1 border-none bg-transparent text-base text-ink-gray-8 outline-none placeholder:text-ink-gray-4"
              :placeholder="sizes.length ? 'Add another' : `e.g. S, M, L`"
              @keydown.enter.prevent="addSize()"
              @blur="addSize()"
            />
            <datalist id="add-product-size-suggestions">
              <option v-for="value in sizeSuggestions" :key="value" :value="value" />
            </datalist>
          </div>
          <Alert
            v-if="!sizeAttributeExists"
            class="mt-2"
            theme="red"
            title='This store has no "Size" attribute yet'
            description="Create it from the Attributes screen first, then come back to add products."
          />
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl v-model.number="price" type="number" label="Price" placeholder="0" />
          <FormControl v-model.number="compareAt" type="number" label="Compare at" placeholder="0" />
        </div>

        <Alert
          title="Photos come next"
          description="This product is created without a photo, so it stays hidden from shoppers until you add one — from the product page, right after this."
        />
      </div>
    </template>

    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        theme="gray"
        label="Add product"
        :disabled="!canSubmit"
        :loading="createAction.loading"
        @click="submit"
      />
    </template>
  </Dialog>
</template>
