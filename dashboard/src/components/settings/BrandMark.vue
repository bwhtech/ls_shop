<script setup>
defineProps({
  mark: { type: String, required: true },
  brand: { type: String, required: true },
  size: { type: String, default: 'size-9' },
})
</script>

<template>
  <div
    class="grid shrink-0 place-content-center rounded-4 text-base-semibold text-white"
    :class="size"
    :style="{ backgroundColor: brand }"
    aria-hidden="true"
  >
    {{ mark }}
  </div>
</template>
