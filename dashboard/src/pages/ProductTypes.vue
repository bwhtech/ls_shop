<script setup>
import { Button, dialog, toast } from 'frappe-ui'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import { productTypes, products } from '../data/mock'

const countFor = (id) => products.filter((p) => p.type === id).length

function addType() {
  dialog.prompt({
    title: 'New product type',
    message: 'A type is a field schema. Products of this type get these extra fields on their form.',
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'fields', label: 'Fields', description: 'Comma separated, e.g. Author, ISBN, Pages' },
    ],
    onConfirm: ({ values }) => toast.success(`"${values.name}" created`),
  })
}
</script>

<template>
  <AppPageHeader title="Product types">
    <template #actions>
      <Button label="New type" icon-left="lucide-plus" variant="solid" theme="gray" @click="addType" />
    </template>
  </AppPageHeader>

  <PageBody width="narrow">
    <p class="text-p-base text-ink-gray-7">
      A type decides what a product <em>is</em>. The core fields — title, media, price, options —
      never change; the type only adds its own. This is what keeps the catalogue from being
      hard-wired to one kind of product.
    </p>

    <div class="mt-6 divide-y divide-outline-gray-1 border-y border-outline-gray-1">
      <div v-for="type in productTypes" :key="type.id" class="flex items-start gap-4 py-4">
        <div class="grid size-9 shrink-0 place-content-center rounded-4 bg-surface-gray-2 text-ink-gray-7">
          <span :class="[type.icon, 'size-4']" aria-hidden="true" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-base text-ink-gray-8">{{ type.name }}</p>
          <p class="mt-1 text-sm text-ink-gray-5">
            {{ countFor(type.id) }} products · {{ type.fields.length }} extra fields
          </p>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="field in type.fields"
              :key="field.key"
              class="rounded-1 bg-surface-gray-2 px-1.5 py-0.5 text-sm text-ink-gray-7"
            >
              {{ field.label }}
              <span class="text-ink-gray-4">{{ field.type }}</span>
            </span>
          </div>
        </div>
        <Button label="Edit" variant="ghost" />
      </div>
    </div>
  </PageBody>
</template>
