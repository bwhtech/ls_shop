<script setup lang="ts">
import { FrappeUIProvider } from "frappe-ui"
import AppShell from "./layouts/AppShell.vue"
</script>

<template>
	<FrappeUIProvider>
		<AppShell>
			<router-view />
		</AppShell>
	</FrappeUIProvider>
</template>
