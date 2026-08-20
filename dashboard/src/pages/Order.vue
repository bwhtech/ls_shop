<script setup lang="ts">
import type { OrderDetail } from "@/types"
import { orderStateTheme } from "@/utils/format"
import {
	Badge,
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

const order = useCall<OrderDetail>({
	url: "/api/v2/method/ls_shop.api.admin.orders.get_order",
	params: () => ({ sales_order: orderName.value }),
	refetch: true,
})

const fulfil = useCall<{ delivery_note: string }>({
	url: "/api/v2/method/ls_shop.api.admin.orders.fulfil_order",
	method: "POST",
	immediate: false,
	onSuccess: (result) => {
		toast.success(`Fulfilled — delivery note ${result.delivery_note}`)
		order.reload()
	},
	onError: (error: Error) => toast.error(error.message),
})

// Fulfilling submits a stock movement that cannot be undone from here, so it asks first.
function confirmFulfil() {
	dialog.confirm({
		title: "Fulfil this order?",
		message:
			"This ships everything outstanding and takes the stock out of your warehouse.",
		confirmLabel: "Fulfil",
		onConfirm: () => fulfil.submit({ sales_order: orderName.value }),
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
			<Button
				v-if="order.data?.can_fulfil"
				variant="solid"
				theme="gray"
				icon-left="lucide-truck"
				:loading="fulfil.loading"
				label="Fulfil order"
				@click="confirmFulfil"
			/>
		</header>

		<LoadingText v-if="order.loading && !order.data" class="p-5" :lines="4" />

		<div v-else-if="order.data" class="min-h-0 flex-1 overflow-y-auto">
			<div class="body-container pb-40 pt-5">
				<div class="flex items-center gap-3">
					<h1 class="text-md text-ink-gray-9">{{ order.data.name }}</h1>
					<Badge
						variant="subtle"
						:theme="orderStateTheme(order.data.state)"
						:label="order.data.state"
					/>
				</div>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					Placed {{ order.data.placed_on }} · {{ order.data.payment_mode ?? "No payment mode" }}
				</p>

				<section class="mt-6">
					<h2 class="text-md text-ink-gray-9">Items</h2>
					<!-- The trailing rule closes the block: the header draws the one on top,
					     and row dividers only sit between rows. -->
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
									<span class="text-base text-ink-gray-7">{{ item.rate }}</span>
								</ListCell>
								<ListCell class="justify-end">
									<span class="text-base text-ink-gray-9">{{ item.amount }}</span>
								</ListCell>
							</ListRow>
						</ListRows>
					</List>

					<div class="mt-3 flex justify-end gap-8 text-base">
						<span class="text-ink-gray-5">Total</span>
						<span class="text-ink-gray-9">
							{{ order.data.currency }} {{ order.data.grand_total }}
						</span>
					</div>
				</section>

				<section class="mt-6 grid gap-6 sm:grid-cols-2">
					<div>
						<h2 class="text-md text-ink-gray-9">Customer</h2>
						<dl class="mt-2 space-y-1.5 text-base">
							<dd class="text-ink-gray-9">{{ order.data.customer }}</dd>
							<dd v-if="order.data.email" class="text-ink-gray-7">{{ order.data.email }}</dd>
							<dd v-if="order.data.phone" class="text-ink-gray-7">{{ order.data.phone }}</dd>
						</dl>
					</div>
					<div>
						<h2 class="text-md text-ink-gray-9">Shipping to</h2>
						<p class="mt-2 whitespace-pre-line text-p-base text-ink-gray-7">
							{{ order.data.shipping_address ?? "No address on this order" }}
						</p>
					</div>
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
