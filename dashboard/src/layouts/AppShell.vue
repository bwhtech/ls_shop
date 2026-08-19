<script setup lang="ts">
import { DesktopShell, Sidebar, SidebarItem, SidebarLabel } from "frappe-ui"
</script>

<template>
	<DesktopShell :scroll="false">
		<template #sidebar>
			<Sidebar>
				<SidebarLabel>Store</SidebarLabel>
				<SidebarItem :to="{ name: 'Products' }" label="Products">Products</SidebarItem>
			</Sidebar>
		</template>
		<slot />
	</DesktopShell>
</template>
