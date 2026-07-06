class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0]?.[0]
    if (!input || input.length === 0) {
      return true
    }

    const pcm = new Int16Array(input.length)
    let sumSquares = 0

    for (let index = 0; index < input.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, input[index]))
      sumSquares += sample * sample
      pcm[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
    }

    const level = Math.sqrt(sumSquares / Math.max(input.length, 1))
    this.port.postMessage({ pcm: pcm.buffer, level }, [pcm.buffer])
    return true
  }
}

registerProcessor('pcm-capture-processor', PcmCaptureProcessor)
