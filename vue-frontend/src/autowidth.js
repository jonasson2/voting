let measurementContext
const pending = new Map()
let scheduled = false

function getMeasurementContext() {
  if (!measurementContext) {
    measurementContext = document.createElement("canvas").getContext("2d")
  }
  return measurementContext
}

function measuredText(el, value, cache) {
  const styles = window.getComputedStyle(el)
  const context = getMeasurementContext()
  context.font = styles.font

  let text = value
  if (styles.textTransform === "uppercase") text = text.toUpperCase()
  else if (styles.textTransform === "lowercase") text = text.toLowerCase()

  const spacing = Number.parseFloat(styles.letterSpacing) || 0
  const key = [styles.font, spacing, text].join("\0")
  if (!cache.has(key)) {
    cache.set(key,
      context.measureText(text).width + spacing * Math.max(text.length - 1, 0))
  }
  return cache.get(key)
}

function optionsFor(binding) {
  return {
    maxWidth: "none",
    minWidth: "none",
    comfortZone: 0,
    ...binding.value,
  }
}

function update(el, binding) {
  const options = optionsFor(binding)
  const value = el.value || el.placeholder || ""
  const cacheKey = [value, options.maxWidth, options.minWidth,
    options.comfortZone].join("\0")
  if (el.autowidthCacheKey === cacheKey) {
    pending.delete(el)
    return
  }
  pending.set(el, {el, options, value, cacheKey})
  if (!scheduled) {
    scheduled = true
    queueMicrotask(flush)
  }
}

function flush() {
  scheduled = false
  const entries = [...pending.values()]
  pending.clear()
  const cache = new Map()
  // Read all styles before changing widths: each input belongs to a large table.
  for (const entry of entries) {
    entry.width = measuredText(entry.el, entry.value, cache)
      + entry.options.comfortZone + 2
  }
  for (const {el, options, width} of entries) {
    el.style.boxSizing = "content-box"
    el.style.maxWidth = options.maxWidth
    el.style.minWidth = options.minWidth
    el.style.width = `${width}px`
  }
  // Keep the native-input overflow correction, with one layout read phase.
  for (const entry of entries) {
    entry.overflow = entry.el.scrollWidth - entry.el.clientWidth
  }
  for (const {el, width, overflow, cacheKey} of entries) {
    if (overflow > 0) el.style.width = `${width + overflow}px`
    el.autowidthCacheKey = cacheKey
  }
}

export default {
  mounted(el, binding) {
    update(el, binding)
  },
  updated(el, binding) {
    update(el, binding)
  },
  unmounted(el) {
    pending.delete(el)
  },
}
