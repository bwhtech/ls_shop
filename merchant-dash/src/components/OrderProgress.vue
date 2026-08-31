<script setup>
import { computed } from 'vue'
import { longDate } from '../data/format'

const props = defineProps({ order: { type: Object, required: true } })

const PAID = ['paid', 'refunded', 'partially_refunded']
const FULFILLED = ['fulfilled', 'delivered']

// One reading of where the order has got to, derived from the payment and
// fulfilment states rather than kept as a separate field.
const steps = computed(() => {
  const { payment, fulfillment } = props.order
  const cancelled = fulfillment === 'cancelled'
  const when = `${longDate(props.order.date)}, ${props.order.time}`

  const state = (done, current) => (cancelled && !done ? 'halted' : done ? 'done' : current ? 'current' : 'todo')

  // Each step depends on the one before it, so the line can only ever fill
  // left to right however the underlying states are combined.
  const paid = PAID.includes(payment)
  const fulfilled = paid && FULFILLED.includes(fulfillment)
  const delivered = fulfilled && fulfillment === 'delivered'

  return [
    {
      key: 'placed',
      label: 'Placed',
      icon: 'lucide-shopping-bag',
      caption: when,
      state: 'done',
    },
    {
      key: 'paid',
      label: 'Paid',
      icon: 'lucide-credit-card',
      caption: paid
        ? payment === 'paid'
          ? when
          : payment === 'refunded'
            ? 'Refunded'
            : 'Partly refunded'
        : 'Awaiting payment',
      state: state(paid, !paid),
    },
    {
      key: 'fulfilled',
      label: 'Fulfilled',
      icon: 'lucide-package-check',
      caption: fulfilled
        ? 'Packed and handed over'
        : fulfillment === 'partial'
          ? 'Part of the order shipped'
          : 'Nothing shipped yet',
      state: state(fulfilled, paid && !fulfilled),
    },
    {
      key: 'delivered',
      label: cancelled ? 'Cancelled' : 'Delivered',
      icon: cancelled ? 'lucide-circle-x' : 'lucide-house',
      caption: cancelled ? 'Refunded and restocked' : delivered ? 'Received by the customer' : 'In transit',
      state: cancelled ? 'cancelled' : state(delivered, fulfilled && !delivered),
    },
  ]
})

// The same surface/ink pairings Avatar uses for a letter with no image: a tint
// behind, the matching ink on top, so a step reads as a state and not as a
// button.
const DOT = {
  done: 'bg-surface-green-2 text-ink-green-7',
  current: 'bg-surface-blue-2 text-ink-blue-7',
  todo: 'bg-surface-gray-2 text-ink-gray-5',
  halted: 'bg-surface-gray-2 text-ink-gray-5',
  cancelled: 'bg-surface-red-2 text-ink-red-7',
}

const LABEL = {
  done: 'text-ink-gray-8',
  current: 'text-ink-gray-9',
  todo: 'text-ink-gray-5',
  halted: 'text-ink-gray-4',
  cancelled: 'text-ink-red-6',
}

// A connector is filled up to the last step the order actually reached.
const REACHED = ['done', 'current', 'cancelled']
const reached = (step) => Boolean(step) && REACHED.includes(step.state)
</script>

<template>
  <div class="rounded-5 border border-outline-gray-1 px-5 py-4">
    <ol class="mx-auto flex max-w-2xl items-start">
      <li
        v-for="(step, index) in steps"
        :key="step.key"
        class="flex min-w-0 flex-1 flex-col items-center text-center"
      >
        <!-- The connectors carry the reading: filled up to where the order got. -->
        <div class="flex w-full items-center">
          <span
            class="h-px flex-1"
            :class="index === 0 ? 'bg-transparent' : reached(step) ? 'bg-surface-gray-5' : 'bg-surface-gray-3'"
            aria-hidden="true"
          />
          <span class="mx-2 grid size-8 shrink-0 place-content-center rounded-full" :class="DOT[step.state]">
            <span :class="[step.state === 'done' ? 'lucide-check' : step.icon, 'size-4']" aria-hidden="true" />
          </span>
          <span
            class="h-px flex-1"
            :class="
              index === steps.length - 1
                ? 'bg-transparent'
                : reached(steps[index + 1])
                  ? 'bg-surface-gray-5'
                  : 'bg-surface-gray-3'
            "
            aria-hidden="true"
          />
        </div>

        <p class="mt-2 max-w-full truncate text-base" :class="LABEL[step.state]">{{ step.label }}</p>
        <p class="mt-0.5 max-w-full truncate text-sm text-ink-gray-5">{{ step.caption }}</p>
      </li>
    </ol>
  </div>
</template>
