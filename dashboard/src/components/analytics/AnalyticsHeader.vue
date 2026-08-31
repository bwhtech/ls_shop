<script setup lang="ts">
import { PageHeader, PageHeaderTitle, TabButtons } from "frappe-ui"
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { analyticsSections } from "./sections"

const route = useRoute()
const router = useRouter()

const options = analyticsSections.map((section) => ({
	label: section.label,
	value: section.route,
}))

// Driven by the route rather than local state, so a deep link and the back button
// both land on the tab that is actually rendered.
const section = computed({
	get: () =>
		analyticsSections.find((option) => option.route === route.name)?.route ??
		options[0].value,
	set: (name: string) => {
		router.push({ name })
	},
})
</script>

<template>
	<PageHeader>
		<div class="flex min-w-0 items-center gap-3">
			<PageHeaderTitle>Analytics</PageHeaderTitle>
			<TabButtons v-model="section" :options="options" />
		</div>
		<div class="flex items-center gap-2">
			<slot name="actions" />
		</div>
	</PageHeader>
</template>
