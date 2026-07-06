export class PcmStreamPlayer {
  private audioContext: AudioContext | null = null
  private nextStartTime = 0
  private sampleRate: number

  constructor(sampleRate = 16_000) {
    this.sampleRate = sampleRate
  }

  private ensureContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new AudioContext({ sampleRate: this.sampleRate })
      this.nextStartTime = this.audioContext.currentTime
    }
    return this.audioContext
  }

  enqueue(chunk: ArrayBuffer): void {
    const context = this.ensureContext()
    const pcm = new Int16Array(chunk)
    const floats = new Float32Array(pcm.length)
    for (let index = 0; index < pcm.length; index += 1) {
      floats[index] = pcm[index] / (pcm[index] < 0 ? 0x8000 : 0x7fff)
    }
    const buffer = context.createBuffer(1, floats.length, this.sampleRate)
    buffer.copyToChannel(floats, 0)
    const source = context.createBufferSource()
    source.buffer = buffer
    source.connect(context.destination)
    const startAt = Math.max(context.currentTime, this.nextStartTime)
    source.start(startAt)
    this.nextStartTime = startAt + buffer.duration
  }

  stop(): void {
    if (!this.audioContext) {
      return
    }
    void this.audioContext.close()
    this.audioContext = null
    this.nextStartTime = 0
  }
}
