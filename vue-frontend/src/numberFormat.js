export const NUMBER_SEPARATOR_OPTIONS = [
  {value: "comma-dot", text: "1,234.567", thousands: ",", decimal: "."},
  {value: "dot-comma", text: "1.234,567", thousands: ".", decimal: ","},
  {value: "space-comma", text: "1\u202f234,567", thousands: " ", decimal: ","},
]

const DEFAULT_FRACTIONAL_DIGITS = 2
const DEFAULT_PERCENTAGE_DIGITS = 1

export function defaultDisplaySettings() {
  return {
    thousands_separator: ",",
    decimal_separator: ".",
    fractional_digits: DEFAULT_FRACTIONAL_DIGITS,
    percentage_digits: DEFAULT_PERCENTAGE_DIGITS,
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
    : DEFAULT_FRACTIONAL_DIGITS
  const requestedPercentageDigits = Number(settings.percentage_digits)
  const percentageDigits = Number.isInteger(requestedPercentageDigits)
    ? Math.min(10, Math.max(0, requestedPercentageDigits))
    : DEFAULT_PERCENTAGE_DIGITS
  return {
    thousands_separator: separators.thousands,
    decimal_separator: separators.decimal,
    fractional_digits: fractionalDigits,
    percentage_digits: percentageDigits,
  }
}

export function formatNumber(value, digits, settings) {
  const number = Number(value)
  if (!Number.isFinite(number)) return "–"
  const normalized = normalizeDisplaySettings(settings)
  const precision = Math.min(10, Math.max(0, Number(digits)))
  const fixed = (Object.is(number, -0) ? 0 : number).toFixed(precision)
  const [integer, fraction] = fixed.split(".")
  const displaySeparator = normalized.thousands_separator === " "
    ? "\u202f"
    : normalized.thousands_separator
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, displaySeparator)
  return fraction === undefined
    ? grouped
    : grouped + normalized.decimal_separator + fraction
}

function groupedIntegerDigits(text, settings) {
  const separator = normalizeDisplaySettings(settings).thousands_separator
  const separatorPattern = separator === " "
    ? "[ \\u00a0\\u202f]"
    : separator.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  const groupedPattern = new RegExp(`^\\d{1,3}(?:${separatorPattern}\\d{3})+$`)
  return groupedPattern.test(text)
    ? text.replace(new RegExp(separatorPattern, "g"), "")
    : null
}

export function parseInteger(value, settings = {}, allowUnlimited = false) {
  if (Number.isInteger(value)) return value
  const text = String(value ?? "").trim()
  if (allowUnlimited && text === "-") return text
  if (/^\d+$/.test(text)) return Number(text)
  const digits = groupedIntegerDigits(text, settings)
  return digits === null ? text : Number(digits)
}

export function validIntegerEntry(value, settings = {}, allowUnlimited = false) {
  const text = String(value ?? "").trim()
  return text === "" || Number.isInteger(parseInteger(text, settings, allowUnlimited))
    || (allowUnlimited && text === "-")
}
