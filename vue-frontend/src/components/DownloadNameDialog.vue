<template>
  <b-modal
    :id="id"
    ref="modal"
    title="Download file"
    ok-title="Download"
    :ok-disabled="!validName"
    @shown="focusName"
    @ok="confirm"
  >
    <label :for="`${id}-filename`">File name</label>
    <div class="download-name-entry">
      <input
        :id="`${id}-filename`"
        ref="filenameInput"
        v-model="basename"
        class="form-control"
        type="text"
        spellcheck="false"
      />
      <span>.{{ extension }}</span>
    </div>
    <small class="text-muted">
      <template v-if="isFirefox">
        Firefox: Settings > Downloads > Ask where to save files.
      </template>
      <template v-else-if="isSafari">
        Safari: Settings > General > File download location > Ask for each download.
      </template>
      <template v-else>
        Your browser controls the download folder in its download settings.
      </template>
    </small>
  </b-modal>
</template>

<script>
import { downloadFilename, validDownloadBasename } from "../downloadName.js"

export default {
  props: {
    id: { type: String, required: true },
  },
  data() {
    return { basename: "", extension: "" }
  },
  computed: {
    validName() { return validDownloadBasename(this.basename) },
    isFirefox() { return navigator.userAgent.includes("Firefox/") },
    isSafari() {
      return navigator.userAgent.includes("Safari/")
        && !navigator.userAgent.includes("Chrome/")
    },
  },
  methods: {
    focusName() {
      this.$refs.filenameInput.focus()
      this.$refs.filenameInput.select()
    },
    open(basename, extension) {
      this.basename = basename
      this.extension = extension
      this.$refs.modal.show()
    },
    confirm() {
      if (this.validName) {
        this.$refs.modal.hide()
        this.$emit("confirm", {
          filename: downloadFilename(this.basename, this.extension),
        })
      }
    },
  },
}
</script>

<style scoped>
.download-name-entry {
  align-items: center;
  display: flex;
  gap: 4px;
}

.download-name-entry input {
  flex: 1;
  min-width: 0;
}
</style>
