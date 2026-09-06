function refreshWidth(el, options) {
  const value = el.value || el.placeholder || ""
  el.mirror.textContent = value
  el.style.width = `${el.mirror.scrollWidth + options.comfortZone + 2}px`
}

function setupMirror(el) {
  const styles = window.getComputedStyle(el)
  const mirror = document.createElement("span")
  Object.assign(mirror.style, {
    position: "absolute",
    top: "0",
    left: "0",
    visibility: "hidden",
    height: "0",
    overflow: "hidden",
    whiteSpace: "pre",
    fontSize: styles.fontSize,
    fontFamily: styles.fontFamily,
    fontWeight: styles.fontWeight,
    fontStyle: styles.fontStyle,
    letterSpacing: styles.letterSpacing,
    textTransform: styles.textTransform,
  })
  document.body.appendChild(mirror)
  return mirror
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
  el.style.boxSizing = "content-box"
  el.style.maxWidth = options.maxWidth
  el.style.minWidth = options.minWidth
  refreshWidth(el, options)
}

export default {
  mounted(el, binding) {
    el.mirror = setupMirror(el)
    update(el, binding)
    requestAnimationFrame(() => {
      if (el.isConnected) update(el, binding)
    })
  },
  updated(el, binding) {
    update(el, binding)
  },
  beforeUnmount(el) {
    el.mirror.remove()
  },
}
