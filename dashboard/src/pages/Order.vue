<script setup lang="ts">
import ErrorState from "@/components/ErrorState.vue"
import OrderStateBadge from "@/components/OrderStateBadge.vue"
import AnalyticsPanel from "@/components/analytics/AnalyticsPanel.vue"
import OrderProgress from "@/components/orders/OrderProgress.vue"
import type { OrderProgressStep } from "@/components/orders/types"
import type { OrderDetail } from "@/types"
import { errorMessage } from "@/utils/errors"
import { formatDate, formatMoney } from "@/utils/format"
import {
	Breadcrumbs,
	Button,
	LoadingText,
	dialog,
	toast,
	useCall,
} from "frappe-ui"
import {
	List,
	ListCell,
	ListHeader,
	ListHeaderCell,
	ListRow,
	ListRows,
} from "frappe-ui/list"
import { computed } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()
const orderName = computed(() => String(route.params.name))

const order = useCall<
	OrderDetail & { progress: OrderProgressStep[] },
	{ sales_order: string }
>({
	url: "/api/v2/method/ls_shop.api.admin.orders.get_order",
	params: () => ({ sales_order: orderName.value }),
	refetch: true,
})

const fulfil = useCall<{ delivery_note: string }, { sales_order: string }>({
	url: "/api/v2/method/ls_shop.api.admin.orders.fulfil_order",
	method: "POST",
	immediate: false,
	onSuccess: (result) => {
		toast.success(`Fulfilled — delivery note ${result.delivery_note}`)
		order.reload()
	},
	onError: (error: Error) => toast.error(errorMessage(error)),
})

const totalsBreakdown = computed(() => {
	const data = order.data
	if (!data) return []
	const charges = [
		{ label: "Shipping", amount: data.shipping },
		{ label: "Cash on delivery", amount: data.cod_charge },
		{ label: "Tax", amount: data.tax },
	]
	return [
		{ label: "Subtotal", amount: data.net_total },
		...charges.filter((charge) => charge.amount),
	]
})

function confirmFulfil() {
	dialog.confirm({
		title: "Fulfil this order?",
		message:
			"This ships everything outstanding and takes the stock out of your warehouse.",
		confirmLabel: "Fulfil",
		onConfirm: async () => {
			await fulfil.submit({ sales_order: orderName.value })
		},
	})
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 shrink-0 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs
				:items="[
					{ label: 'Orders', route: { name: 'Orders' } },
					{ label: order.data?.name ?? 'Loading', route: '' },
				]"
			/>
			<div class="flex items-center gap-3">
				<a
					v-if="order.data"
					class="text-p-sm text-ink-blue-link hover:underline"
					:href="`/app/sales-order/${order.data.name}`"
					target="_blank"
					rel="noopener"
				>
					View in Desk
				</a>
				<Button
					v-if="order.data?.can_fulfil"
					variant="solid"
					theme="gray"
					icon-left="lucide-truck"
					:loading="fulfil.loading"
					label="Fulfil order"
					@click="confirmFulfil"
				/>
			</div>
		</header>

		<LoadingText v-if="order.loading && !order.data" class="p-5" :lines="4" />

		<ErrorState
			v-else-if="order.error"
			title="Could not load this order"
			:message="errorMessage(order.error)"
			@retry="order.reload()"
		/>

		<div v-else-if="order.data" class="min-h-0 flex-1 overflow-y-auto">
			<div class="body-container pb-40 pt-5">
				<div class="flex items-center gap-3">
					<h1 class="text-2xl font-semibold text-ink-gray-9">{{ order.data.name }}</h1>
					<OrderStateBadge :state="order.data.state" />
				</div>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					Placed {{ formatDate(order.data.placed_on) }} · {{ order.data.payment_mode ?? "No payment mode" }}
				</p>

				<OrderProgress
					:steps="order.data.progress"
					class="mt-5 rounded-6 border border-outline-gray-1 px-4 py-3.5"
				/>

				<section class="mt-6">
					<h2 class="text-md text-ink-gray-9">Items</h2>
					<List
						class="mt-2 border-b border-outline-gray-1"
						:columns="['minmax(0,1fr)', '4rem', '5rem', '6rem', '6rem']"
					>
						<ListHeader>
							<ListHeaderCell>Product</ListHeaderCell>
							<ListHeaderCell class="justify-end">Qty</ListHeaderCell>
							<ListHeaderCell class="justify-end">Shipped</ListHeaderCell>
							<ListHeaderCell class="justify-end">Rate</ListHeaderCell>
							<ListHeaderCell class="justify-end">Amount</ListHeaderCell>
						</ListHeader>
						<ListRows
							:items="order.data.items"
							row-key="item_code"
							v-slot="{ item }"
						>
							<ListRow class="py-2.5">
								<ListCell>
									<div class="flex min-w-0 items-center gap-2.5">
										<img
											v-if="item.image"
											:src="item.image"
											alt=""
											class="size-8 shrink-0 rounded-4 object-cover"
										/>
										<div
											v-else
											class="grid size-8 shrink-0 place-items-center rounded-4 bg-surface-gray-2 text-xs text-ink-gray-4"
										>
											{{ item.title.slice(0, 1) }}
										</div>
										<div class="min-w-0">
											<div class="truncate text-base text-ink-gray-9">
												{{ item.title }}
											</div>
											<div v-if="item.size" class="text-xs text-ink-gray-5">
												Size {{ item.size }}
											</div>
										</div>
									</div>
								</ListCell>
								<ListCell class="justify-end">
									<span class="text-base text-ink-gray-7">{{ item.qty }}</span>
								</ListCell>
								<ListCell class="justify-end">
									<span
										class="text-base"
										:class="item.delivered_qty >= item.qty ? 'text-ink-green-6' : 'text-ink-gray-5'"
									>
										{{ item.delivered_qty }}
									</span>
								</ListCell>
								<ListCell class="justify-end">
									<span class="text-base text-ink-gray-7">
										{{ formatMoney(item.rate, order.data.currency) }}
									</span>
								</ListCell>
								<ListCell class="justify-end">
									<span class="text-base text-ink-gray-9">
										{{ formatMoney(item.amount, order.data.currency) }}
									</span>
								</ListCell>
							</ListRow>
						</ListRows>
					</List>

					<div class="mt-3 flex justify-end">
						<dl class="w-64 space-y-1.5 text-base">
							<div
								v-for="row in totalsBreakdown"
								:key="row.label"
								class="flex justify-between gap-8"
							>
								<dt class="text-ink-gray-5">{{ row.label }}</dt>
								<dd class="text-ink-gray-7">
									{{ formatMoney(row.amount, order.data.currency) }}
								</dd>
							</div>
							<div
								class="flex justify-between gap-8 border-t border-outline-gray-1 pt-1.5"
							>
								<dt class="text-ink-gray-5">Total</dt>
								<dd class="text-ink-gray-9">
									{{ formatMoney(order.data.grand_total, order.data.currency) }}
								</dd>
							</div>
						</dl>
					</div>
				</section>

				<section class="mt-6 grid items-start gap-4 sm:grid-cols-2">
					<AnalyticsPanel title="Customer">
						<template #actions>
							<a
								class="text-p-sm text-ink-blue-link hover:underline"
								:href="`/app/customer/${order.data.customer}`"
								target="_blank"
								rel="noopener"
							>
								View in Desk
							</a>
						</template>
						<dl class="space-y-1.5 text-base">
							<dd class="text-ink-gray-9">{{ order.data.customer }}</dd>
							<dd v-if="order.data.email" class="text-ink-gray-7">{{ order.data.email }}</dd>
							<dd v-if="order.data.phone" class="text-ink-gray-7">{{ order.data.phone }}</dd>
						</dl>
					</AnalyticsPanel>
					<!-- The address arrives already rendered to lines, so there is no Address docname to link. -->
					<AnalyticsPanel title="Shipping to">
						<p class="whitespace-pre-line text-p-base text-ink-gray-7">
							{{ order.data.shipping_address ?? "No address on this order" }}
						</p>
					</AnalyticsPanel>
				</section>

				<section v-if="order.data.deliveries.length" class="mt-6">
					<h2 class="text-md text-ink-gray-9">Deliveries</h2>
					<ul class="mt-2 space-y-1 text-base text-ink-gray-7">
						<li v-for="delivery in order.data.deliveries" :key="delivery">{{ delivery }}</li>
					</ul>
				</section>
			</div>
		</div>
	</div>
</template>
