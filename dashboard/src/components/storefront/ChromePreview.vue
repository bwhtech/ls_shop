<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Button, TabButtons } from 'frappe-ui'

const props = defineProps({
  // Bumped by every mutation; it is what makes the iframe refetch the rendered chrome.
  token: { type: Number, required: true },
  path: { type: String, required: true },
  title: { type: String, required: true },
  selector: { type: String, required: true },
})

const collapsed = defineModel('collapsed', { type: Boolean, required: true })

const FRAME_WIDTH = 1440
const FALLBACK_FRAME_HEIGHT = 560
const MAX_STAGE_HEIGHT = 420
// A hovered mega-menu opens under the navbar, so a frame ending at the chrome bottom
// clips it out of existence.
const DROPDOWN_HEADROOM = 460

const LANGUAGES = [
  { label: 'English', value: 'en' },
  { label: 'العربية', value: 'ar' },
]

const language = ref('en')
const reloadToken = ref(0)
const contentHeight = ref(0)

const stage = ref(null)
const stageWidth = ref(0)
let stageObserver = null

onMounted(() => {
  stageObserver = new ResizeObserver(([entry]) => {
    stageWidth.value = entry.contentRect.width
  })
  if (stage.value) stageObserver.observe(stage.value)
})

onBeforeUnmount(() => stageObserver?.disconnect())

const scale = computed(() => (stageWidth.value ? Math.min(1, stageWidth.value / FRAME_WIDTH) : 1))

const headroom = computed(() => (props.selector === 'header' ? DROPDOWN_HEADROOM : 0))

// Sizing the frame to the pane crops the footer-bottom strip, so it is driven by the
// rendered chrome instead.
const frameHeight = computed(() => (contentHeight.value || FALLBACK_FRAME_HEIGHT) + headroom.value)

const stageHeight = computed(() => Math.min(frameHeight.value * scale.value, MAX_STAGE_HEIGHT))

function measureFrame(event) {
  const previewDocument = event.target.contentDocument
  // Measured off the chrome itself: a full-height themed page's scrollHeight would hang
  // an empty storefront under the navbar.
  const chrome = previewDocument?.querySelector(props.selector)
  contentHeight.value = chrome
    ? Math.ceil(chrome.getBoundingClientRect().bottom)
    : (previewDocument?.documentElement?.scrollHeight ?? 0)
}

const source = computed(() => `${props.path}?lang=${language.value}&t=${props.token}-${reloadToken.value}`)
</script>

<template>
  <div class="mt-4 rounded-6 border border-outline-gray-1 bg-surface-gray-1">
    <div class="flex min-h-11 items-center justify-between gap-2 px-3">
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          :icon-left="collapsed ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          :label="collapsed ? `Show ${title.toLowerCase()}` : title"
          @click="collapsed = !collapsed"
        />
        <TabButtons v-if="!collapsed" v-model="language" size="sm" :options="LANGUAGES" />
      </div>

      <Button v-if="!collapsed" icon-left="lucide-rotate-cw" label="Refresh" @click="reloadToken += 1" />
    </div>

    <div v-if="!collapsed" class="px-3 pb-3">
      <div
        ref="stage"
        class="overflow-y-auto rounded-4 border border-outline-gray-2 bg-surface-base"
        :style="{ height: `${stageHeight}px` }"
      >
        <iframe
          :key="language"
          :src="source"
          :title="title"
          class="origin-top-left border-0"
          :style="{
            width: `${FRAME_WIDTH}px`,
            height: `${frameHeight}px`,
            transform: `scale(${scale})`,
          }"
          @load="measureFrame"
        />
      </div>
    </div>
  </div>
</template>
