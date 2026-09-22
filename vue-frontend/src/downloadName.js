export function validDownloadBasename(value) {
  const name = String(value ?? "").trim()
  return name !== "" && name !== "." && name !== ".."
    && !/[<>:"/\\|?*\x00-\x1f]/.test(name)
}

export function downloadFilename(basename, extension) {
  const name = basename.trim()
  const suffix = `.${extension}`
  return name.toLowerCase().endsWith(suffix.toLowerCase())
    ? name : name + suffix
}

export function downloadBasename(filename, extension) {
  const name = String(filename ?? "").trim()
  const suffix = `.${extension}`
  return name.toLowerCase().endsWith(suffix.toLowerCase())
    ? name.slice(0, -suffix.length) : name
}

export function canChooseSaveLocation() {
  return typeof window !== "undefined"
    && typeof window.showSaveFilePicker === "function"
}

export function chooseSaveLocation(basename, extension) {
  return window.showSaveFilePicker({
    suggestedName: downloadFilename(basename, extension),
  })
}

export async function writeDownload(fileHandle, blob) {
  const writable = await fileHandle.createWritable()
  await writable.write(blob)
  await writable.close()
}

export function timestampedDownloadBasename(prefix, date = new Date()) {
  const pad = value => String(value).padStart(2, "0")
  return `${prefix}-${date.getFullYear()}.${pad(date.getMonth() + 1)}.`
    + `${pad(date.getDate())}T${pad(date.getHours())}.`
    + `${pad(date.getMinutes())}.${pad(date.getSeconds())}`
}
