<script setup>
import { ref } from 'vue'
import { Badge } from 'frappe-ui'
import { AreaChart, DonutChart, FunnelChart } from 'frappe-ui/charts'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import ReportHeader from '../../components/ReportHeader.vue'
import ReportStats from '../../components/ReportStats.vue'
import PageBody from '../../components/PageBody.vue'
import { channels, funnel, searchTerms, sessionsByMonth, topPages } from '../../data/analytics'
import { ia } from '../../ia/store'

const range = ref('Last 12 months')
const compare = ref(true)

const stats = [
  { label: 'Sessions', value: '4,44,600', delta: '+13.2%', up: true },
  { label: 'Conversion', value: '2.9%', delta: '+0.3pt', up: true },
  { label: 'Add to cart', value: '14.3%', delta: '-0.6pt', up: false },
  { label: 'Checkout completion', value: '44.3%', delta: '+2.1pt', up: true },
]
</script>

<template>
  <ReportHeader title="Storefront" v-model:range="range" v-model:compare="compare" />

  <PageBody width="narrow">
    <div>
      <h1 class="text-2xl text-ink-gray-9">Storefront</h1>
      <p class="mt-1 text-p-base text-ink-gray-6">
        Who reaches the store, what they look at, where they drop out. {{ range }}.
      </p>
    </div>

    <ReportStats class="mt-5" :stats="stats" :compare="compare" />

    <section class="mt-6 rounded-5 border border-outline-gray-1 p-4">
      <h2 class="text-lg-semibold text-ink-gray-8">Sessions over time</h2>
      <div class="h-72">
        <AreaChart :data="sessionsByMonth" x="month" :y="['sessions']" />
      </div>
    </section>

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <section class="rounded-5 border border-outline-gray-1 p-4">
        <h2 class="text-lg-semibold text-ink-gray-8">Where they come from</h2>
        <div class="h-64">
          <DonutChart :data="channels" category="channel" value="sessions" />
        </div>
      </section>
      <section class="rounded-5 border border-outline-gray-1 p-4">
        <h2 class="text-lg-semibold text-ink-gray-8">Checkout funnel</h2>
        <div class="h-64">
          <FunnelChart :data="funnel" category="stage" value="count" />
        </div>
      </section>
    </div>

    <section class="mt-6 rounded-5 border border-outline-gray-1">
      <h2 class="px-4 py-3 text-lg-semibold text-ink-gray-8">Top pages</h2>
      <div class="px-2 pb-2">
        <List :columns="['minmax(0,1fr)', '8rem', '8rem']" :row-height="Math.max(ia.density, 44)">
          <ListHeader>
            <ListHeaderCell>Page</ListHeaderCell>
            <ListHeaderCell>Views</ListHeaderCell>
            <ListHeaderCell>Conversion</ListHeaderCell>
          </ListHeader>
          <ListRows :items="topPages" row-key="page" v-slot="{ item }">
            <ListRow :value="item.page">
              <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.page }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-6 tabular-nums">{{ item.views.toLocaleString('en-IN') }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-6 tabular-nums">{{ item.conversion }}%</span></ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </section>

    <section class="mt-6 rounded-5 border border-outline-gray-1">
      <div class="px-4 py-3">
        <h2 class="text-lg-semibold text-ink-gray-8">Search terms</h2>
        <p class="mt-1 text-sm text-ink-gray-5">
          Terms with no results are demand you are not stocking.
        </p>
      </div>
      <div class="px-2 pb-2">
        <List :columns="['minmax(0,1fr)', '8rem', '8rem']" :row-height="Math.max(ia.density, 44)">
          <ListHeader>
            <ListHeaderCell>Term</ListHeaderCell>
            <ListHeaderCell>Searches</ListHeaderCell>
            <ListHeaderCell>Results</ListHeaderCell>
          </ListHeader>
          <ListRows :items="searchTerms" row-key="term" v-slot="{ item }">
            <ListRow :value="item.term">
              <ListCell><span class="truncate text-base text-ink-gray-8">{{ item.term }}</span></ListCell>
              <ListCell><span class="text-base text-ink-gray-6 tabular-nums">{{ item.searches }}</span></ListCell>
              <ListCell>
                <Badge v-if="!item.results" label="No results" theme="red" variant="subtle" />
                <span v-else class="text-base text-ink-gray-6 tabular-nums">{{ item.results }}</span>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </section>
  </PageBody>
</template>
