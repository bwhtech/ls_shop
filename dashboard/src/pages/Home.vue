<script setup lang="ts">
import OrderStateBadge from "@/components/OrderStateBadge.vue"
import type { Overview } from "@/types"
import { formatMoney, formatShortDate } from "@/utils/format"
import {
	Button,
	PageHeader,
	PageHeaderTitle,
	ScrollArea,
	TabButtons,
	useCall,
} from "frappe-ui"
import { List, ListCell, ListRow, ListRows } from "frappe-ui/list"
import { computed, ref } from "vue"

const orderStatus = ref("")

const orderTabs = [
	{ label: "Recent", value: "" },
	{ label: "To fulfil", value: "open" },
]

const overview = useCall<Overview, { order_status: string }>({
	url: "/api/v2/method/ls_shop.api.admin.orders.get_overview",
	params: () => ({ order_status: orderStatus.value }),
	refetch: true,
})

const currency = computed(() => overview.data?.currency ?? "")
const stats = computed(() => overview.data?.stats ?? [])
const recentOrders = computed(() => overview.data?.recent_orders ?? [])
const runningLow = computed(() => overview.data?.running_low ?? [])
const needsAttention = computed(() => overview.data?.needs_attention ?? [])

function formatStat(stat: Overview["stats"][number]) {
	return stat.format === "currency"
		? formatMoney(stat.value, currency.value)
		: String(stat.value)
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<PageHeader>
			<PageHeaderTitle>Home</PageHeaderTitle>
			<div class="flex items-center gap-2">
				<TabButtons v-model="orderStatus" :options="orderTabs" />
				<Button
					variant="ghost"
					icon-left="lucide-refresh-cw"
					label="Refresh"
					:loading="overview.loading"
					@click="overview.reload()"
				/>
			</div>
		</PageHeader>

		<ScrollArea class="min-h-0 flex-1" viewport-class="pb-40">
			<div class="mx-auto max-w-4xl space-y-6 px-3 pt-5 sm:px-5">
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<div
						v-for="stat in stats"
						:key="stat.key"
						class="rounded-6 border border-outline-gray-1 bg-surface-base p-4"
					>
						<div class="text-xs text-ink-gray-5">{{ stat.label }}</div>
						<div
							class="mt-1 truncate text-3xl font-semibold"
							:class="stat.value < 0 ? 'text-ink-red-5' : 'text-ink-gray-9'"
						>
							{{ formatStat(stat) }}
						</div>
						<div
							v-if="stat.delta !== null"
							class="mt-1 flex items-center gap-1 text-xs"
							:class="stat.delta < 0 ? 'text-ink-red-5' : 'text-ink-gray-5'"
						>
							<span
								:class="stat.delta >= 0 ? 'lucide-arrow-up' : 'lucide-arrow-down'"
								class="size-3 shrink-0"
								aria-hidden="true"
							/>
							<span class="truncate">
								{{ Math.abs(stat.delta) }}% vs last month
							</span>
						</div>
						<div v-else class="mt-1 truncate text-xs text-ink-gray-5">
							{{ stat.note ?? "No data for last month" }}
						</div>
					</div>
				</div>

				<section class="space-y-2">
					<div class="flex h-7 items-center justify-between">
						<h3 class="text-sm font-semibold text-ink-gray-8">Recent orders</h3>
						<Button
							variant="ghost"
							label="View all"
							@click="$router.push({ name: 'Orders' })"
						/>
					</div>
					<List
						v-if="recentOrders.length"
						class="list-row-px-0"
						:columns="['6.5rem', 'minmax(0,1fr)', '10.5rem', '7rem']"
						:row-height="44"
					>
						<ListRows :items="recentOrders" v-slot="{ item }">
							<ListRow :to="{ name: 'Order', params: { name: item.name } }">
								<ListCell>
									<span class="text-sm text-ink-gray-6">
										{{ formatShortDate(item.placed_on) }}
									</span>
								</ListCell>
								<ListCell>
									<span class="truncate text-sm text-ink-gray-8">
										{{ item.customer }}
									</span>
								</ListCell>
								<ListCell>
									<OrderStateBadge :state="item.state" />
								</ListCell>
								<ListCell class="justify-end">
									<span class="text-sm text-ink-gray-8">
										{{ formatMoney(item.total, item.currency) }}
									</span>
								</ListCell>
							</ListRow>
						</ListRows>
					</List>
					<p v-else class="py-6 text-sm text-ink-gray-5">
						No orders yet. Orders placed in your store will show up here.
					</p>
				</section>

				<div class="grid gap-3 sm:grid-cols-2">
					<section
						class="space-y-2 rounded-6 border border-outline-gray-1 bg-surface-base p-4"
					>
						<div class="flex h-7 items-center justify-between">
							<h3 class="text-sm font-semibold text-ink-gray-8">Running low</h3>
							<Button
								variant="ghost"
								label="View all"
								@click="$router.push({ name: 'Inventory' })"
							/>
						</div>
						<div v-if="runningLow.length" class="divide-y divide-outline-gray-1">
							<div
								v-for="row in runningLow"
								:key="row.item_code"
								class="flex items-center justify-between gap-3 py-2"
							>
								<div class="min-w-0">
									<div class="truncate text-sm text-ink-gray-8">
										{{ row.product }}
									</div>
									<div class="text-p-xs text-ink-gray-5">
										{{ row.option }} · {{ row.size }}
									</div>
								</div>
								<span
									class="shrink-0 text-sm"
									:class="row.stock <= 0 ? 'text-ink-red-5' : 'text-ink-gray-8'"
								>
									{{ row.stock }}
								</span>
							</div>
						</div>
						<p v-else class="py-6 text-sm text-ink-gray-5">
							Every size has healthy stock.
						</p>
					</section>

					<section
						class="space-y-2 rounded-6 border border-outline-gray-1 bg-surface-base p-4"
					>
						<div class="flex h-7 items-center justify-between">
							<h3 class="text-sm font-semibold text-ink-gray-8">
								Needs attention
							</h3>
							<Button
								variant="ghost"
								label="View all"
								@click="$router.push({ name: 'Products' })"
							/>
						</div>
						<div
							v-if="needsAttention.length"
							class="divide-y divide-outline-gray-1"
						>
							<router-link
								v-for="row in needsAttention"
								:key="row.variant"
								:to="{ name: 'Product', params: { name: row.product } }"
								class="flex items-center justify-between gap-3 py-2"
							>
								<div class="min-w-0">
									<div class="truncate text-sm text-ink-gray-8">
										{{ row.title }}
									</div>
									<div class="truncate text-p-xs text-ink-gray-5">
										{{ row.option }} · {{ row.blockers.join(", ") }}
									</div>
								</div>
								<span
									class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5"
									aria-hidden="true"
								/>
							</router-link>
						</div>
						<p v-else class="py-6 text-sm text-ink-gray-5">
							Every option is ready to go live.
						</p>
					</section>
				</div>
			</div>
		</ScrollArea>
	</div>
</template>
