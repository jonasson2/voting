import catalog from './terminology.json'

export const TERMINOLOGY_STORAGE_KEY = 'voting.terminology'

export function normalizeTerminology(preferences = {}) {
  return Object.fromEntries(Object.entries(catalog).map(([concept, definition]) => [
    concept, Object.hasOwn(definition.choices, preferences?.[concept])
      ? preferences[concept] : definition.default,
  ]))
}

export function term(concept, preferences = {}, {plural = false, capitalized = false} = {}) {
  const definition = catalog[concept]
  const choice = definition.choices[normalizeTerminology(preferences)[concept]]
  const text = choice[plural ? 'plural' : 'singular']
  return capitalized ? text[0].toUpperCase() + text.slice(1) : text
}

// Call only for application-owned labels and prose, never for names or input data.
export function formatTerminology(text, preferences = {}) {
  if (typeof text !== 'string') return text
  for (const [concept, definition] of Object.entries(catalog)) {
    const original = definition.choices[definition.default]
    const forms = Object.entries(original).sort((a, b) => b[1].length - a[1].length)
    const escaped = forms.map(([, value]) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replaceAll(' ', '[\\s-]+'))
    const pattern = new RegExp(`\\b(?:(a|an)(\\s+))?(${escaped.join('|')})(?!\\w)`, 'gi')
    text = text.replace(pattern, (whole, article, space, match) => {
      const form = forms.find(([, value]) => value === match.toLowerCase().replace(/[\s-]+/g, ' '))[0]
      const choice = definition.choices[normalizeTerminology(preferences)[concept]]
      let replacement = choice[form]
      if (original[form].includes(' ') && match.includes('-')) replacement = replacement.replaceAll(' ', '-')
      if (match[0] === match[0].toUpperCase()) replacement = replacement[0].toUpperCase() + replacement.slice(1)
      const noun = match === match.toUpperCase() ? replacement.toUpperCase() : replacement
      if (!article) return noun
      let nextArticle = /^[aeiou]/i.test(noun) ? 'an' : 'a'
      if (article === article.toUpperCase() && match === match.toUpperCase()) nextArticle = nextArticle.toUpperCase()
      else if (article[0] === article[0].toUpperCase()) {
        nextArticle = nextArticle[0].toUpperCase() + nextArticle.slice(1)
      }
      return nextArticle + space + noun
    })
  }
  return text
}

export function terminologyOptions(concept) {
  return Object.entries(catalog[concept].choices).map(([value, choice]) => ({
    value, text: choice.singular[0].toUpperCase() + choice.singular.slice(1),
  }))
}

export function installTerminology(app, store, storage) {
  try {
    storage ??= window.localStorage
    store.commit('updateTerminology', normalizeTerminology(
      JSON.parse(storage.getItem(TERMINOLOGY_STORAGE_KEY)) || {}))
  } catch (_) { /* A disabled or unavailable browser store must not prevent startup. */ }
  store.subscribe((mutation, state) => {
    if (mutation.type !== 'updateTerminology') return
    try {
      storage.setItem(TERMINOLOGY_STORAGE_KEY, JSON.stringify(normalizeTerminology(state.terminology)))
    } catch (_) { /* The preference still works for the current session. */ }
  })
  app.config.globalProperties.$terms = text => formatTerminology(text, store.state.terminology)
  app.config.globalProperties.$termOptions = options => options?.map(option =>
    typeof option === 'string' ? formatTerminology(option, store.state.terminology)
      : {...option, text: formatTerminology(option.text, store.state.terminology)})
}
