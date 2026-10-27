import { normalizeDisplaySettings } from './numberFormat.js'

export const DISPLAY_STORAGE_KEY = 'voting.display-settings'

export function installDisplayPreferences(store, storage) {
  try {
    storage ??= window.localStorage
    const saved = JSON.parse(storage.getItem(DISPLAY_STORAGE_KEY))
    if (saved && typeof saved === 'object' && !Array.isArray(saved)) {
      store.commit('updateDisplaySettings', normalizeDisplaySettings(saved))
    }
  } catch (_) { /* Unavailable storage must not prevent startup. */ }
  store.subscribe((mutation, state) => {
    if (mutation.type !== 'updateDisplaySettings') return
    try {
      storage.setItem(DISPLAY_STORAGE_KEY,
        JSON.stringify(normalizeDisplaySettings(state.display_settings)))
    } catch (_) { /* Settings still work for the current session. */ }
  })
}
