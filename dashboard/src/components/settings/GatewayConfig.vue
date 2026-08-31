<script setup>
/**
 * Configuring one gateway takes over the panel, so the keys of seven providers
 * never share a scroll. Nothing here is exclusive — several gateways run side
 * by side; only the checkout default is one of a kind.
 */
import {
  Button,
  SettingsBody,
  SettingsHeader,
  SettingsRow,
  Switch,
  TabButtons,
  TextInput,
  toast,
} from 'frappe-ui'

const props = defineProps({
  gateway: { type: Object, required: true },
  config: { type: Object, required: true },
  isDefault: { type: Boolean, default: false },
})

const emit = defineEmits(['back', 'make-default'])

function save() {
  props.config.configured = true
  emit('back')
  toast.success(`${props.gateway.name} saved`)
}
</script>

<template>
  <SettingsHeader :title="gateway.name" description="Keys and environment for this provider.">
    <template #actions>
      <Button label="Back" icon-left="lucide-arrow-left" @click="emit('back')" />
      <Button label="Save keys" variant="solid" theme="gray" @click="save" />
    </template>
  </SettingsHeader>

  <SettingsBody>
    <div class="divide-y divide-outline-gray-1">
      <SettingsRow title="Enabled" description="Offered to shoppers at checkout.">
        <Switch v-model="config.enabled" size="sm" />
      </SettingsRow>
      <SettingsRow title="Environment" description="Test keys never move real money.">
        <TabButtons
          v-model="config.mode"
          :options="[
            { label: 'Test', value: 'test' },
            { label: 'Live', value: 'live' },
          ]"
        />
      </SettingsRow>
      <SettingsRow
        v-for="field in gateway.fields"
        :key="field.key"
        :title="field.label"
        :description="field.secret ? 'Stored encrypted, never shown again.' : undefined"
      >
        <TextInput
          v-model="config.values[field.key]"
          class="w-72"
          :type="field.secret ? 'password' : 'text'"
          :placeholder="field.placeholder"
        />
      </SettingsRow>
      <SettingsRow
        title="Capture manually"
        description="Authorise at checkout, take the money when you fulfil."
      >
        <Switch v-model="config.captureManually" size="sm" />
      </SettingsRow>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-2">
      <Button
        label="Send a test payment"
        icon-left="lucide-beaker"
        @click="toast.info('Test charge of ₹1 queued')"
      />
      <Button
        v-if="config.enabled && !isDefault"
        label="Make default at checkout"
        variant="ghost"
        @click="emit('make-default', gateway.id)"
      />
    </div>
  </SettingsBody>
</template>
