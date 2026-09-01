<script setup>
/**
 * Create a sellable product in one screen: catalog.create_product does the rest
 * (Item template + variants, Style Attribute Configurator, generate_variants, prices).
 * Company, warehouse, price list, UOM and naming series are resolved server-side —
 * this dialog never shows an ERPNext concept the owner did not ask for.
 */
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Button, Dialog, ErrorMessage, FormControl, Select, dialog, toast } from 'frappe-ui'
import { useAdminAction, useAdminRead } from '../data/api'
import { addProduct, closeAddProduct } from '../data/addProduct'
import { buildOptionSizes } from '../data/optionSizes'
import AttributeMultiSelect from './AttributeMultiSelect.vue'
import OptionSizeGrid from './OptionSizeGrid.vue'

const router = useRouter()

const title = ref('')
const collection = ref('')
const optionAttribute = ref('Color')
const colors = ref([])
const sizes = ref([])
const excludedPairs = ref([])
const compareAt = ref(null)
const price = ref(null)
const colorsOpen = ref(false)
const sizesOpen = ref(false)

// reka guards only Escape by topmost layer, so one outside click dismisses the
// popover and the dialog both; the dialog yields while a picker owns that click.
const pickerOpen = computed(() => colorsOpen.value || sizesOpen.value)

function resetForm() {
  title.value = ''
  collection.value = ''
  optionAttribute.value = 'Color'
  colors.value = []
  sizes.value = []
  excludedPairs.value = []
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

// Values picked off one attribute mean nothing on another, and neither do the pairs they were unticked in.
watch(optionAttribute, () => {
  colors.value = []
  excludedPairs.value = []
})

const optionSizes = computed(() => buildOptionSizes(colors.value, sizes.value, excludedPairs.value))
const variantCount = computed(() => optionSizes.value.reduce((total, row) => total + row.sizes.length, 0))
const emptyOption = computed(() => optionSizes.value.find((row) => !row.sizes.length)?.option)
const gridError = computed(() => (emptyOption.value ? `Pick at least one size for ${emptyOption.value}` : ''))

const canSubmit = computed(
  () =>
    Boolean(title.value.trim()) &&
    Boolean(collection.value) &&
    Boolean(optionAttribute.value) &&
    sizeAttributeExists.value &&
    variantCount.value > 0 &&
    !emptyOption.value,
)

const createAction = useAdminAction('catalog.create_product')

// A disabled button with no reason reads as a broken screen, so the first thing still missing is named.
const submitHint = computed(() => {
  if (canSubmit.value || createAction.loading) return ''
  if (!title.value.trim()) return 'Add a title to continue.'
  if (!collection.value) return 'Pick a collection to continue.'
  if (!sizeAttributeExists.value) return 'This store needs a "Size" attribute first.'
  if (!colors.value.length) return `Pick at least one ${(optionAttribute.value || 'option').toLowerCase()}.`
  if (!sizes.value.length) return 'Pick at least one size.'
  return ''
})

async function submit() {
  if (!canSubmit.value) return

  await createAction.submit({
    title: title.value.trim(),
    collection: collection.value,
    option_attribute: optionAttribute.value,
    size_attribute: 'Size',
    option_sizes: optionSizes.value,
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
  <Dialog
    v-model:open="addProduct.open"
    size="xl"
    title="Add product"
    :dismissible="!pickerOpen"
    @update:open="(v) => (v ? null : closeAddProduct())"
  >
    <template #default>
      <div class="space-y-5">
        <FormControl v-model="title" label="Title" placeholder="Cotton oversized tee" required />

        <div>
          <span class="mb-1.5 block text-base text-ink-gray-6">
            Collection
            <span class="text-ink-red-5 select-none" aria-hidden="true">*</span>
            <span class="sr-only">(required)</span>
          </span>
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

        <AttributeMultiSelect
          v-model="colors"
          v-model:open="colorsOpen"
          :attribute="optionAttribute"
          :label="optionAttribute || 'Options'"
          :placeholder="`Pick or type a ${(optionAttribute || 'option').toLowerCase()}`"
          :description="`Type a new ${(optionAttribute || 'option').toLowerCase()} to add it`"
          required
        />

        <div>
          <AttributeMultiSelect
            v-model="sizes"
            v-model:open="sizesOpen"
            attribute="Size"
            label="Sizes"
            placeholder="Pick or type a size"
            description="Type a new size to add it"
            required
          />
          <Alert
            v-if="!sizeAttributeExists"
            class="mt-2"
            theme="red"
            title='This store has no "Size" attribute yet'
            description="Create it from the Attributes screen first, then come back to add products."
          />
        </div>

        <OptionSizeGrid
          v-if="colors.length && sizes.length"
          v-model="excludedPairs"
          :options="colors"
          :sizes="sizes"
          :option-label="optionAttribute || 'Option'"
        />

        <p v-if="variantCount" class="text-sm text-ink-gray-5">
          {{ colors.length }} {{ colors.length === 1 ? 'option' : 'options' }} ·
          {{ variantCount }} {{ variantCount === 1 ? 'variant' : 'variants' }} will be created
        </p>
        <ErrorMessage :message="gridError" />

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
      <div class="w-full">
        <Button
          class="w-full"
          variant="solid"
          theme="gray"
          label="Add product"
          :disabled="!canSubmit"
          :loading="createAction.loading"
          @click="submit"
        />
        <p v-if="submitHint" class="mt-2 text-center text-sm text-ink-gray-5">{{ submitHint }}</p>
      </div>
    </template>
  </Dialog>
</template>
