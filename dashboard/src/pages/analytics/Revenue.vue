<script setup>
import { computed, ref } from 'vue'
import { AreaChart, BarChart } from 'frappe-ui/charts'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import ReportHeader from '../../components/ReportHeader.vue'
import ReportStats from '../../components/ReportStats.vue'
import PageBody from '../../components/PageBody.vue'
import { revenueByMonth } from '../../data/analytics'
import { compactMoney, money } from '../../data/format'
import { ia } from '../../ia/store'

const range = ref('Last 12 months')
const compare = ref(true)

const total = computed(() => revenueByMonth.reduce((sum, m) => sum + m.revenue, 0))
const orderCount = computed(() => revenueByMonth.reduce((sum, m) => sum + m.orders, 0))
const refunds = computed(() => revenueByMonth.reduce((sum, m) => sum + m.refunds, 0))

const stats = computed(() => [
  { label: 'Gross revenue', value: compactMoney(total.value), delta: '+18.2%', up: true },
  { label: 'Orders', value: orderCount.value.toLocaleString('en-IN'), delta: '+11.4%', up: true },
  { label: 'Avg. order value', value: money(total.value / orderCount.value), delta: '-1.8%', up: false },
  { label: 'Refunded', value: compactMoney(refunds.value), delta: '+6.1%', up: false },
])

const rows = computed(() =>
  [...revenueByMonth].reverse().map((m) => ({ ...m, net: m.revenue - m.refunds - m.discounts })),
)
</script>

<template>
  <ReportHeader title="Revenue" v-model:range="range" v-model:compare="compare" />

  <PageBody width="narrow">
    <div>
      <h1 class="text-2xl text-ink-gray-9">Revenue</h1>
      <p class="mt-1 text-p-base text-ink-gray-6">
        What the store earned, and what came back off the top. {{ range }}.
      </p>
    </div>

    <ReportStats class="mt-5" :stats="stats" :compare="compare" />

    <section class="mt-6 rounded-5 border border-outline-gray-1 p-4">
      <h2 class="text-lg-semibold text-ink-gray-8">Revenue over time</h2>
      <div class="h-72">
        <AreaChart :data="revenueByMonth" x="month" :y="['revenue']" />
      </div>
    </section>

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <section class="rounded-5 border border-outline-gray-1 p-4">
        <h2 class="text-lg-semibold text-ink-gray-8">Discounts given</h2>
        <div class="h-56">
          <BarChart :data="revenueByMonth" x="month" :y="['discounts']" />
        </div>
      </section>
      <section class="rounded-5 border border-outline-gray-1 p-4">
        <h2 class="text-lg-semibold text-ink-gray-8">Average order value</h2>
        <div class="h-56">
          <BarChart :data="revenueByMonth" x="month" :y="['aov']" />
        </div>
      </section>
    </div>

    <section class="mt-6 rounded-5 border border-outline-gray-1">
      <h2 class="px-4 py-3 text-lg-semibold text-ink-gray-8">By month</h2>
      <div class="overflow-x-auto px-2 pb-2">
        <List
          class="min-w-[46rem]"
          :columns="['6rem', '8rem', '6rem', '7rem', '7rem', '8rem']"
          :row-height="Math.max(ia.density, 44)"
        >
          <ListHeader>
            <ListHeaderCell>Month</ListHeaderCell>
            <ListHeaderCell>Revenue</ListHeaderCell>
            <ListHeaderCell>Orders</ListHeaderCell>
            <ListHeaderCell>Discounts</ListHeaderCell>
            <ListHeaderCell>Refunds</ListHeaderCell>
            <ListHeaderCell>Net</ListHeaderCell>
          </ListHeader>
          <ListRows :items="rows" row-key="month" v-slot="{ item }">
            <ListRow :value="item.month">
              <ListCell><span class="text-base text-ink-gray-8">{{ item.month }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-7 tabular-nums">{{ money(item.revenue) }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-6 tabular-nums">{{ item.orders }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-6 tabular-nums">{{ money(item.discounts) }}</span></ListCell>
              <ListCell><span class="text-base text-ink-red-6 tabular-nums">{{ money(item.refunds) }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-8 tabular-nums">{{ money(item.net) }}</span></ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </section>
  </PageBody>
</template>
