<script setup>
import { Badge } from 'frappe-ui'
import { label, statusTheme } from '../data/format'

defineProps({ status: { type: String, required: true } })
</script>

<template>
  <Badge :label="label(status)" :theme="statusTheme(status)" variant="subtle" />
</template>
