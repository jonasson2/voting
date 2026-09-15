export const NUMBER_SEPARATOR_OPTIONS = [
  {value: "comma-dot", text: "1,234.567", thousands: ",", decimal: "."},
  {value: "dot-comma", text: "1.234,567", thousands: ".", decimal: ","},
  {value: "space-comma", text: "1 234,567", thousands: " ", decimal: ","},
]

export function defaultDisplaySettings() {
  return {
    thousands_separator: ",",
    decimal_separator: ".",
    fractional_digits: 3,
  }
}

export function normalizeDisplaySettings(settings = {}) {
  const separators = NUMBER_SEPARATOR_OPTIONS.find(option =>
    option.thousands === settings.thousands_separator
      && option.decimal === settings.decimal_separator
  ) || NUMBER_SEPARATOR_OPTIONS[0]
  const requestedDigits = Number(settings.fractional_digits)
  const fractionalDigits = Number.isInteger(requestedDigits)
    ? Math.min(10, Math.max(0, requestedDigits))
    : 3
  return {
    thousands_separator: separators.thousands,
    decimal_separator: separators.decimal,
    fractional_digits: fractionalDigits,
  }
}

export function formatNumber(value, digits, settings) {
  const number = Number(value)
  if (!Number.isFinite(number)) return "–"
  const normalized = normalizeDisplaySettings(settings)
  const precision = Math.min(10, Math.max(0, Number(digits)))
  const fixed = (Object.is(number, -0) ? 0 : number).toFixed(precision)
  const [integer, fraction] = fixed.split(".")
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g,
    normalized.thousands_separator)
  return fraction === undefined
    ? grouped
    : grouped + normalized.decimal_separator + fraction
}

export function parseInteger(value, allowUnlimited = false) {
  if (Number.isInteger(value)) return value
  const text = String(value ?? "").trim()
  if (allowUnlimited && text === "-") return text
  return /^\d+$/.test(text) ? Number(text) : text
}

export function validIntegerEntry(value, allowUnlimited = false) {
  return /^\d*$/.test(value) || (allowUnlimited && value === "-")
}
