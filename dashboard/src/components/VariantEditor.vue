<script setup>
import { ref } from 'vue'
import { Badge, Button, Dialog, FormControl, dialog, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import Thumb from './Thumb.vue'
import EditableValue from './EditableValue.vue'
import VariantDialog from './VariantDialog.vue'
import VariantImageImport from './VariantImageImport.vue'
import { attributes, regenerateVariants } from '../data/mock'
import { stockTone } from '../data/format'
import { ia } from '../ia/store'

const props = defineProps({ product: { type: Object, required: true } })

const selection = ref([])

// A row opens the variant rather than navigating: a variant is a small record,
// and you are usually working down the matrix, not away from it.
const editing = ref(null)
const showVariant = ref(false)
const showImageImport = ref(false)

function openVariant(variant) {
  editing.value = variant
  showVariant.value = true
}

// Options are the axes. Variants are every combination of them, rebuilt when
// an axis changes, so a product with no options keeps no matrix at all.
const showOption = ref(false)
const optionDraft = ref({ name: '', values: '' })

function addOption() {
  const values = optionDraft.value.values.split(',').map((v) => v.trim()).filter(Boolean)
  if (!optionDraft.value.name || !values.length) return
  props.product.options.push({ name: optionDraft.value.name, values })
  regenerateVariants(props.product)
  optionDraft.value = { name: '', values: '' }
  showOption.value = false
  toast.success('Option added, variants regenerated')
}

function removeOption(name) {
  dialog.confirm({
    title: `Remove "${name}"`,
    message: 'The variant matrix is rebuilt without this axis.',
    theme: 'red',
    confirmLabel: 'Remove option',
    onConfirm: () => {
      props.product.options = props.product.options.filter((o) => o.name !== name)
      regenerateVariants(props.product)
    },
  })
}

function bulkEdit(field, label) {
  const count = selection.value.length
  dialog.prompt({
    title: `Set ${label.toLowerCase()} on ${count} ${count === 1 ? 'variant' : 'variants'}`,
    fields: [{ name: 'value', label, type: 'number', required: true }],
    onConfirm: ({ values }) => {
      const next = Math.max(0, Number(values.value) || 0)
      props.product.variants
        .filter((v) => selection.value.includes(v.id))
        .forEach((v) => (v[field] = next))
      selection.value = []
      toast.success(`${label} updated on ${count} ${count === 1 ? 'variant' : 'variants'}`)
    },
  })
}

// Five columns, because the matrix sits beside the summary panel: the barcode
// is on the variant's own page, where there is room for it.
const columns = ['minmax(7rem,1.3fr)', 'minmax(5rem,1fr)', '6.5rem', '5rem', '4.5rem']
</script>

<template>
  <section class="space-y-5">
    <!-- The axes, first: the matrix below is nothing but their product. -->
    <div class="rounded-5 border border-outline-gray-1">
      <div class="flex items-center justify-between px-4 py-3">
        <div>
          <h2 class="text-lg-semibold text-ink-gray-8">Options</h2>
          <p class="mt-1 text-p-sm text-ink-gray-5">Each option is an axis of the matrix below.</p>
        </div>
        <Button label="Add option" icon-left="lucide-plus" @click="showOption = true" />
      </div>

      <div v-if="product.options.length" class="divide-y divide-outline-gray-1 border-t border-outline-gray-1">
        <div v-for="option in product.options" :key="option.name" class="flex items-start gap-3 px-4 py-3">
          <span class="w-24 shrink-0 pt-0.5 text-base text-ink-gray-6">{{ option.name }}</span>
          <div class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
            <Badge v-for="value in option.values" :key="value" :label="value" variant="subtle" />
            <span v-if="attributes.some((a) => a.name === option.name)" class="text-sm text-ink-gray-4">
              global attribute
            </span>
          </div>
          <Button icon="lucide-trash-2" label="Remove option" @click="removeOption(option.name)" />
        </div>
      </div>

      <div v-else class="border-t border-outline-gray-1 px-4 py-6 text-center">
        <p class="text-base text-ink-gray-7">This product has no options</p>
        <p class="mt-1 text-p-sm text-ink-gray-5">
          It sells as a single item. Add an option like Size or Colour only if you need one.
        </p>
      </div>
    </div>

    <!-- The matrix: one flat row per permutation, each value set in place. -->
    <div v-if="product.options.length" class="rounded-5 border border-outline-gray-1">
      <div class="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
        <h2 class="text-lg-semibold text-ink-gray-8">Variant matrix</h2>
        <div class="flex items-center gap-2">
          <template v-if="selection.length">
            <span class="text-sm text-ink-gray-5">{{ selection.length }} selected</span>
            <Button label="Set price" @click="bulkEdit('price', 'Price')" />
            <Button label="Set stock" @click="bulkEdit('stock', 'Stock')" />
            <Button label="Clear" variant="ghost" @click="selection = []" />
          </template>
          <Button
            v-if="!selection.length"
            label="Import photos"
            icon-left="lucide-folder-archive"
            @click="showImageImport = true"
          />
        </div>
      </div>

      <div class="overflow-x-auto px-2 pb-2">
        <List
          v-model:selection="selection"
          class="min-w-[30rem]"
          selectable
          :row-height="Math.max(ia.density, 48)"
          :columns="columns"
        >
          <ListHeader>
            <ListHeaderCell>Variant</ListHeaderCell>
            <ListHeaderCell>SKU</ListHeaderCell>
            <ListHeaderCell>Price</ListHeaderCell>
            <ListHeaderCell>Stock</ListHeaderCell>
            <ListHeaderCell>Photos</ListHeaderCell>
          </ListHeader>
          <ListRows :items="product.variants" row-key="id" v-slot="{ item }">
            <ListRow :value="item.id">
              <ListCell>
                <button class="flex min-w-0 items-center gap-2.5" @click.stop="openVariant(item)">
                  <Thumb :emoji="item.thumb" size="size-7" />
                  <span class="truncate text-base text-ink-gray-8">{{ item.title }}</span>
                </button>
              </ListCell>
              <ListCell><span class="truncate text-base text-ink-gray-5">{{ item.sku }}</span></ListCell>
              <ListCell>
                <EditableValue v-model="item.price" label="Price" format="money" />
              </ListCell>
              <ListCell>
                <EditableValue v-model="item.stock" label="On hand" :class="stockTone(item.stock)" />
              </ListCell>
              <ListCell>
                <!-- Photos are per variant, so the count is a way in, not a stat. -->
                <button
                  class="flex items-center gap-1.5 rounded-4 px-1.5 py-0.5 hover:bg-surface-gray-2"
                  @click.stop="openVariant(item)"
                >
                  <span
                    class="size-3.5"
                    :class="item.images ? 'lucide-image text-ink-gray-6' : 'lucide-image-plus text-ink-gray-4'"
                    aria-hidden="true"
                  />
                  <span class="text-base tabular-nums" :class="item.images ? 'text-ink-gray-7' : 'text-ink-gray-4'">
                    {{ item.images || 'Add' }}
                  </span>
                </button>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </div>
  </section>

  <VariantDialog v-model:open="showVariant" :variant="editing" :product="product" />
  <VariantImageImport v-model:open="showImageImport" :product="product" />

  <Dialog v-model:open="showOption" title="Add option">
    <div class="space-y-4">
      <FormControl
        v-model="optionDraft.name"
        label="Option name"
        description="Size, Colour, Format, Material. Reuses a global attribute when the name matches one."
      />
      <FormControl
        v-model="optionDraft.values"
        label="Values"
        description="Comma separated. Every combination becomes a variant."
      />
      <div class="flex justify-end gap-2 pt-2">
        <Button label="Cancel" @click="showOption = false" />
        <Button label="Add option" variant="solid" theme="gray" @click="addOption" />
      </div>
    </div>
  </Dialog>
</template>
