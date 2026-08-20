<script setup lang="ts">
import {
	type ColorScheme,
	Select,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	useColorScheme,
} from "frappe-ui"
import { computed } from "vue"

const { colorScheme, setColorScheme } = useColorScheme()

const themeOptions = [
	{ label: "Light", value: "light" },
	{ label: "Dark", value: "dark" },
	{ label: "System Default", value: "system" },
]

const selectedTheme = computed({
	get: () => colorScheme.value,
	set: (theme: ColorScheme) => setColorScheme(theme),
})
</script>

<template>
	<SettingsHeader>
		<h2 class="text-md font-semibold text-ink-gray-8">Appearance</h2>
	</SettingsHeader>

	<SettingsBody>
		<div class="pt-6">
			<div class="divide-y divide-outline-gray-1">
				<SettingsRow
					title="Theme"
					description="Choose a light, dark, or system-matched interface"
				>
					<Select v-model="selectedTheme" :options="themeOptions">
						<template #item-prefix="{ item }">
							<div
								v-if="item.value === 'system'"
								class="flex size-3 overflow-hidden rounded-full border border-outline-gray-2"
							>
								<div class="w-1/2 bg-white" />
								<div class="w-1/2 bg-gray-950" />
							</div>
							<div
								v-else
								class="size-3 rounded-full border"
								:class="
									item.value === 'light' ? 'border-outline-gray-2 bg-white' : 'bg-gray-950'
								"
							/>
						</template>
					</Select>
				</SettingsRow>
			</div>
		</div>
	</SettingsBody>
</template>
