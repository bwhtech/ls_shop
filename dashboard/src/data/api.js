// The shared entry point for every screen that reads or writes the real
// ls_shop backend, instead of each screen wiring its own useCall + toast.
// Task-shaped endpoints live under `ls_shop.api.admin.*` (see docs/comera-wiring-map.md),
// so callers pass the path below that prefix, e.g. useAdminRead('catalog.get_products').
import { toast, useCall } from 'frappe-ui'
import { errorMessage } from './errors'

// useCall fetches `baseUrl + url` verbatim — it does NOT prepend /api/method/. Without the
// absolute prefix the browser resolves the dotted path against the current page, the SPA
// catch-all route serves the shell back, and every screen dies on `Unexpected token '<'`.
const ADMIN_MODULE_PREFIX = '/api/method/ls_shop.api.admin.'

// A GET read. Every list/detail screen fetches the same way, and a failure
// surfaces the same way — as a toast, not a silently empty screen.
export function useAdminRead(path, options = {}) {
  const { onError, ...rest } = options
  return useCall({
    url: ADMIN_MODULE_PREFIX + path,
    method: 'GET',
    onError: (error) => {
      toast.error(errorMessage(error))
      onError?.(error)
    },
    ...rest,
  })
}

// A POST write. `immediate` defaults to false — a write fires on `.submit()`,
// never on mount — and a failure toasts here so no screen has to remember to.
export function useAdminAction(path, options = {}) {
  const { onError, ...rest } = options
  return useCall({
    url: ADMIN_MODULE_PREFIX + path,
    method: 'POST',
    immediate: false,
    onError: (error) => {
      toast.error(errorMessage(error))
      onError?.(error)
    },
    ...rest,
  })
}
