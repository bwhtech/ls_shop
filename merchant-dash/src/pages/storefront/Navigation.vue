<script setup>
import { ref } from 'vue'
import { Button, TabButtons, toast } from 'frappe-ui'
import AppPageHeader from '../../components/AppPageHeader.vue'
import PageBody from '../../components/PageBody.vue'
import { storefrontMenus } from '../../data/mock'

const menuId = ref('main')
const menu = () => storefrontMenus.find((m) => m.id === menuId.value)
</script>

<template>
  <AppPageHeader title="Navigation">
    <template #actions>
      <Button label="Add item" icon-left="lucide-plus" />
      <Button label="Save menu" variant="solid" theme="gray" @click="toast.success('Menu saved')" />
    </template>
  </AppPageHeader>

  <PageBody>
    <TabButtons
      v-model="menuId"
      size="sm"
      :options="storefrontMenus.map((m) => ({ label: m.name, value: m.id }))"
    />

    <div class="mt-4 gap-6 lg:flex">
      <div class="min-w-0 flex-1">
        <div class="divide-y divide-outline-gray-1 border-y border-outline-gray-1">
          <div v-for="item in menu().items" :key="item.id">
            <div class="flex items-center gap-2 py-2.5">
              <span class="lucide-grip-vertical size-4 cursor-grab text-ink-gray-4" aria-hidden="true" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-base text-ink-gray-8">{{ item.label }}</p>
                <p class="truncate text-sm text-ink-gray-5">{{ item.target }}</p>
              </div>
              <Button icon="lucide-pencil" variant="ghost" label="Edit item" />
              <Button icon="lucide-trash-2" variant="ghost" theme="red" label="Remove item" />
            </div>
            <div v-for="child in item.children" :key="child.id" class="flex items-center gap-2 py-2.5 pl-8">
              <span class="lucide-corner-down-right size-4 text-ink-gray-4" aria-hidden="true" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-base text-ink-gray-7">{{ child.label }}</p>
                <p class="truncate text-sm text-ink-gray-5">{{ child.target }}</p>
              </div>
              <Button icon="lucide-pencil" variant="ghost" label="Edit item" />
            </div>
          </div>
        </div>
      </div>

      <aside class="mt-8 w-full shrink-0 lg:mt-0 lg:w-[22rem]">
        <p class="text-sm text-ink-gray-5">Preview</p>
        <div class="mt-2 rounded-6 border border-outline-gray-2 bg-surface-base p-4">
          <div class="flex flex-wrap items-center gap-4 border-b border-outline-gray-1 pb-3">
            <span class="text-base-semibold text-ink-gray-9">Kirana & Co</span>
            <span v-for="item in menu().items" :key="item.id" class="text-sm text-ink-gray-6">
              {{ item.label }}
            </span>
          </div>
          <p class="mt-3 text-p-sm text-ink-gray-5">
            Nested items appear as a dropdown under their parent.
          </p>
        </div>
      </aside>
    </div>
  </PageBody>
</template>
