<script setup>
import { Button, ScrollArea, dialog, toast } from 'frappe-ui'
import AppPageHeader from '../components/AppPageHeader.vue'
import PageBody from '../components/PageBody.vue'
import { attributes } from '../data/mock'

function addAttribute() {
  dialog.prompt({
    title: 'New attribute',
    message: 'Attributes are shared across products. Any product can turn one into a variant option.',
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'values', label: 'Values', description: 'Comma separated' },
    ],
    onConfirm: ({ values }) => toast.success(`"${values.name}" created`),
  })
}
</script>

<template>
  <AppPageHeader title="Attributes">
    <template #actions>
      <Button label="New attribute" icon-left="lucide-plus" variant="solid" theme="gray" @click="addAttribute" />
    </template>
  </AppPageHeader>

  <PageBody width="narrow">
    <p class="text-p-base text-ink-gray-7">
      Size and Color ship out of the box, but they are ordinary records — a bookshop can delete
      them and add Format and Binding instead.
    </p>

    <!-- The list scrolls on its own, so the page header and the intent above
         stay put while you work down a long set of attributes. -->
    <ScrollArea class="mt-6 max-h-[calc(100vh-15rem)] border-y border-outline-gray-1">
      <div class="divide-y divide-outline-gray-1">
        <div v-for="attribute in attributes" :key="attribute.id" class="flex items-start gap-4 py-4">
          <div class="min-w-0 flex-1">
            <p class="text-base text-ink-gray-8">{{ attribute.name }}</p>
            <p class="mt-1 text-sm text-ink-gray-5">Used by {{ attribute.usedBy }} products</p>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="value in attribute.values"
                :key="value"
                class="rounded-1 bg-surface-gray-2 px-1.5 py-0.5 text-sm text-ink-gray-7"
              >
                {{ value }}
              </span>
            </div>
          </div>
          <Button label="Edit" variant="ghost" />
        </div>
      </div>
    </ScrollArea>
  </PageBody>
</template>
