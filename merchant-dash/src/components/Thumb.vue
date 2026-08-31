<script setup>
defineProps({
  emoji: { type: String, default: '📦' },
  size: { type: String, default: 'size-8' },
})
</script>

<template>
  <div
    class="grid shrink-0 place-content-center rounded-4 bg-surface-gray-2 text-ink-gray-7"
    :class="size"
    aria-hidden="true"
  >
    {{ emoji }}
  </div>
</template>
