// pdf.js 6.x calls Map/WeakMap.prototype.getOrInsert(Computed) (TC39 "upsert"), which older
// Chromium builds lack; without it large PDFs fail to load. The worker uses pdf.js's legacy
// build (core-js polyfilled); this covers the main-thread API.
for (const C of [Map, WeakMap] as unknown as { prototype: Record<string, unknown> }[]) {
  const p = C.prototype as unknown as Map<unknown, unknown> & Record<string, unknown>
  if (!p.getOrInsertComputed) {
    p.getOrInsertComputed = function (this: Map<unknown, unknown>, k: unknown, f: (k: unknown) => unknown) {
      if (!this.has(k)) this.set(k, f(k))
      return this.get(k)
    }
  }
  if (!p.getOrInsert) {
    p.getOrInsert = function (this: Map<unknown, unknown>, k: unknown, v: unknown) {
      if (!this.has(k)) this.set(k, v)
      return this.get(k)
    }
  }
}
