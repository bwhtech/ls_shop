import { ref } from "vue"

/** Global handles for the command centre, so the shell can offer it without prop-drilling. */
export const showPalette = ref(false)
export const showShortcuts = ref(false)
