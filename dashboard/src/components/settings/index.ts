import { ref } from "vue"

/** Global handle for the settings dialog, so any screen can open it without prop-drilling. */
export const showSettings = ref(false)
export const activeSettingsTab = ref("appearance")

export function openSettings(tab = "appearance") {
	activeSettingsTab.value = tab
	showSettings.value = true
}
