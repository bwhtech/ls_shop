<script setup lang="ts">
import type { OrderProgressStep } from "@/components/orders/types"
import { formatDate, formatDateTime, orderStateBadge } from "@/utils/format"
import { computed } from "vue"

const props = defineProps<{ steps: OrderProgressStep[] }>()

/** Written out in full because Tailwind only keeps class names it can see. */
const stepColours: Record<
	string,
	{ node: string; ring: string; label: string }
> = {
	to_fulfil: {
		node: "bg-surface-amber-2 text-ink-amber-7",
		ring: "ring-outline-amber-3",
		label: "text-ink-amber-7",
	},
	delivery_note_drafted: {
		node: "bg-surface-gray-3 text-ink-gray-7",
		ring: "ring-outline-gray-4",
		label: "text-ink-gray-8",
	},
	packed: {
		node: "bg-surface-violet-2 text-ink-violet-7",
		ring: "ring-outline-violet-3",
		label: "text-ink-violet-7",
	},
	shipped: {
		node: "bg-surface-blue-2 text-ink-blue-7",
		ring: "ring-outline-blue-3",
		label: "text-ink-blue-7",
	},
	delivered: {
		node: "bg-surface-green-2 text-ink-green-7",
		ring: "ring-outline-green-3",
		label: "text-ink-green-7",
	},
	returned: {
		node: "bg-surface-red-2 text-ink-red-7",
		ring: "ring-outline-red-3",
		label: "text-ink-red-7",
	},
	cancelled: {
		node: "bg-surface-red-2 text-ink-red-7",
		ring: "ring-outline-red-3",
		label: "text-ink-red-7",
	},
}

const upcomingNode = "bg-surface-gray-2 text-ink-gray-4"

function stepIcon(step: OrderProgressStep) {
	return orderStateBadge({ key: step.key, label: step.label }).icon
}

function nodeClass(step: OrderProgressStep) {
	const colours = stepColours[step.key]
	if (!colours || step.state === "upcoming") return upcomingNode
	return step.state === "current"
		? `${colours.node} ring-2 ${colours.ring}`
		: colours.node
}

function labelClass(step: OrderProgressStep) {
	if (step.state === "upcoming") return "text-ink-gray-4"
	if (step.state === "done") return "text-ink-gray-7"
	return `font-medium ${stepColours[step.key]?.label ?? "text-ink-gray-8"}`
}

function connectorClass(step: OrderProgressStep) {
	return step.state === "upcoming"
		? "border-outline-gray-1"
		: "border-outline-gray-3"
}

const stateWording: Record<OrderProgressStep["state"], string> = {
	done: "Completed",
	current: "Current step",
	upcoming: "Not reached yet",
}

/** A step stamped with only a date must not grow a misleading 00:00 time of day. */
function formatStepMoment(value: string) {
	const hasTime = value.includes(" ") || value.includes("T")
	return hasTime ? formatDateTime(value) : formatDate(value)
}

const currentStep = computed(() =>
	props.steps.find((step) => step.state === "current"),
)
</script>

<template>
	<nav
		v-if="steps.length"
		class="overflow-x-auto"
		:aria-label="`Fulfilment progress — ${currentStep?.label ?? 'not started'}`"
	>
		<!-- min-w-max keeps the strip scrollable when it overflows, which also makes justify-center a no-op there. -->
		<ol class="flex min-w-max items-start justify-center py-1">
			<!-- `relative` is load-bearing: the sr-only state is position:absolute and without it escapes this strip's clipping. -->
			<li
				v-for="(step, index) in steps"
				:key="step.key"
				class="relative flex items-start"
				:aria-current="step.state === 'current' ? 'step' : undefined"
			>
				<div
					v-if="index"
					class="mt-4 w-8 border-t sm:w-14"
					:class="connectorClass(step)"
					aria-hidden="true"
				/>
				<div class="flex w-24 flex-col items-center px-1 text-center">
					<span
						class="grid size-8 shrink-0 place-items-center rounded-full"
						:class="nodeClass(step)"
					>
						<span :class="stepIcon(step)" class="size-4" aria-hidden="true" />
					</span>
					<span class="mt-1.5 text-xs leading-4" :class="labelClass(step)">
						{{ step.label }}
					</span>
					<span class="sr-only">{{ stateWording[step.state] }}</span>
					<span v-if="step.note" class="text-xs leading-4 text-ink-gray-5">
						{{ step.note }}
					</span>
					<time v-if="step.at" class="text-xs leading-4 text-ink-gray-4" :datetime="step.at">
						{{ formatStepMoment(step.at) }}
					</time>
				</div>
			</li>
		</ol>
	</nav>
</template>
