<script setup>
import { Badge, Button, Switch } from 'frappe-ui'
import BrandMark from './BrandMark.vue'

defineProps({
  gateway: { type: Object, required: true },
  config: { type: Object, required: true },
  isDefault: { type: Boolean, default: false },
  needsKeys: { type: Boolean, default: false },
})

defineEmits(['configure'])
</script>

<!-- One provider, one row: the mark, what state it is in, and the two things
     you came to do — turn it on, or give it keys. -->
<template>
  <div class="flex items-center gap-3 py-3">
    <BrandMark :mark="gateway.mark" :brand="gateway.brand" size="size-8" />

    <p class="min-w-0 shrink truncate text-base text-ink-gray-8">{{ gateway.name }}</p>

    <Badge
      v-if="config.enabled"
      :label="config.mode === 'live' ? 'Live' : 'Test mode'"
      :theme="config.mode === 'live' ? 'green' : 'orange'"
      variant="subtle"
    />
    <Badge v-if="isDefault && config.enabled" label="Default" theme="blue" variant="subtle" />
    <span v-if="needsKeys" class="shrink-0 text-sm text-ink-amber-7">Keys missing</span>

    <div class="ml-auto flex shrink-0 items-center gap-3">
      <Button
        :label="config.configured ? 'Configure' : 'Add keys'"
        :disabled="!config.enabled"
        @click="$emit('configure', gateway.id)"
      />
      <Switch v-model="config.enabled" size="sm" />
    </div>
  </div>
</template>
