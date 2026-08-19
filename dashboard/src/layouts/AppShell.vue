<script setup lang="ts">
import { DesktopShell, Sidebar, SidebarItem, SidebarLabel } from "frappe-ui"
</script>

<template>
	<!-- scroll=false: each page owns its own scroll region, so a list can scroll independently
	     of its sticky header instead of the whole shell scrolling. -->
	<DesktopShell :scroll="false">
		<template #sidebar>
			<Sidebar>
				<SidebarLabel>Store</SidebarLabel>
				<SidebarItem :to="{ name: 'Products' }" label="Products" icon="lucide-package" />
			</Sidebar>
		</template>
		<slot />
	</DesktopShell>
</template>
