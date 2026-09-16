const gridMoves = {
  ArrowLeft: [0, -1],
  ArrowRight: [0, 1],
  ArrowUp: [-1, 0],
  ArrowDown: [1, 0],
  Enter: [1, 0],
}

export function nextGridPosition(key, row, column) {
  const move = gridMoves[key]
  if (!move) return null
  return {row: row + move[0], column: column + move[1]}
}

function modifiedKey(event) {
  return event.altKey || event.ctrlKey || event.metaKey || event.shiftKey
    || event.isComposing
}

function navigateGrid(event, table, axis) {
  if (modifiedKey(event)) return
  const current = event.target
  if (!current.matches('[data-grid-row][data-grid-column]')) return
  if (axis === 'vertical' && ['ArrowLeft', 'ArrowRight'].includes(event.key)) return
  if (axis === 'horizontal' && !['ArrowLeft', 'ArrowRight'].includes(event.key)) return
  if (current.tagName === 'SELECT'
      && ['ArrowUp', 'ArrowDown', 'Enter'].includes(event.key)) return

  const position = nextGridPosition(
    event.key, Number(current.dataset.gridRow), Number(current.dataset.gridColumn),
  )
  if (!position) return
  event.preventDefault()
  const next = table.querySelector(
    `[data-grid-row="${position.row}"][data-grid-column="${position.column}"]`,
  )
  if (!next) return
  next.focus()
  if (next.matches('input:not([type="checkbox"]):not([type="radio"]), textarea')) {
    next.select()
  }
}

export const gridNavigation = {
  mounted(el, binding) {
    el.gridKeydown = event => navigateGrid(event, el, binding.value)
    el.addEventListener('keydown', el.gridKeydown)
  },
  beforeUnmount(el) {
    el.removeEventListener('keydown', el.gridKeydown)
  },
}
