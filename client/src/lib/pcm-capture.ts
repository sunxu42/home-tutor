const DEFAULT_SAMPLE_RATE = 16_000
const WORKLET_MODULE_URL = '/pcm-capture-processor.js'

export interface PcmCaptureHandle {
  stop: () => void
  sampleRate: number
}

export const BARGE_IN_LEVEL = 0.03

async function startWorkletCapture(
  audioContext: AudioContext,
  stream: MediaStream,
  onChunk: (pcm: ArrayBuffer, level: number) => void,
): Promise<PcmCaptureHandle> {
  await audioContext.audioWorklet.addModule(WORKLET_MODULE_URL)
  const source = audioContext.createMediaStreamSource(stream)
  const worklet = new AudioWorkletNode(audioContext, 'pcm-capture-processor')

  worklet.port.onmessage = (event: MessageEvent<{ pcm: ArrayBuffer; level: number }>) => {
    onChunk(event.data.pcm, event.data.level)
  }

  source.connect(worklet)
  worklet.connect(audioContext.destination)

  return {
    sampleRate: audioContext.sampleRate,
    stop: () => {
      worklet.disconnect()
      source.disconnect()
      void audioContext.close()
      for (const track of stream.getTracks()) {
        track.stop()
      }
    },
  }
}

function startScriptProcessorCapture(
  audioContext: AudioContext,
  stream: MediaStream,
  onChunk: (pcm: ArrayBuffer, level: number) => void,
): PcmCaptureHandle {
  const source = audioContext.createMediaStreamSource(stream)
  const processor = audioContext.createScriptProcessor(4096, 1, 1)

  processor.onaudioprocess = (event) => {
    const input = event.inputBuffer.getChannelData(0)
    let sumSquares = 0
    const pcm = new Int16Array(input.length)
    for (let index = 0; index < input.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, input[index]))
      sumSquares += sample * sample
      pcm[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
    }
    const level = Math.sqrt(sumSquares / Math.max(input.length, 1))
    onChunk(pcm.buffer, level)
  }

  source.connect(processor)
  processor.connect(audioContext.destination)

  return {
    sampleRate: audioContext.sampleRate,
    stop: () => {
      processor.disconnect()
      source.disconnect()
      void audioContext.close()
      for (const track of stream.getTracks()) {
        track.stop()
      }
    },
  }
}

export async function startPcmCapture(
  onChunk: (pcm: ArrayBuffer, level: number) => void,
): Promise<PcmCaptureHandle> {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
    },
  })

  const audioContext = new AudioContext({ sampleRate: DEFAULT_SAMPLE_RATE })

  if (typeof audioContext.audioWorklet?.addModule === 'function') {
    try {
      return await startWorkletCapture(audioContext, stream, onChunk)
    } catch {
      // Fall back to deprecated ScriptProcessor when worklet load fails.
    }
  }

  return startScriptProcessorCapture(audioContext, stream, onChunk)
}
