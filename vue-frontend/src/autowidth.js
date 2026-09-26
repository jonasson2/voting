let measurementContext

function getMeasurementContext() {
  if (!measurementContext) {
    measurementContext = document.createElement("canvas").getContext("2d")
  }
  return measurementContext
}

function measuredText(el, value) {
  const styles = window.getComputedStyle(el)
  const context = getMeasurementContext()
  context.font = styles.font

  let text = value
  if (styles.textTransform === "uppercase") text = text.toUpperCase()
  else if (styles.textTransform === "lowercase") text = text.toLowerCase()

  const spacing = Number.parseFloat(styles.letterSpacing) || 0
  return context.measureText(text).width + spacing * Math.max(text.length - 1, 0)
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
  if (el.autowidthCacheKey === cacheKey) return

  el.style.boxSizing = "content-box"
  el.style.maxWidth = options.maxWidth
  el.style.minWidth = options.minWidth
  let width = measuredText(el, value) + options.comfortZone + 2
  el.style.width = `${width}px`
  // Native inputs can need a pixel more than canvas reports, especially after
  // an edited integer gains its thousands separator again on blur.
  const overflow = el.scrollWidth - el.clientWidth
  if (overflow > 0) {
    width += overflow
    el.style.width = `${width}px`
  }
  el.autowidthCacheKey = cacheKey
}

export default {
  mounted(el, binding) {
    update(el, binding)
  },
  updated(el, binding) {
    update(el, binding)
  },
}
