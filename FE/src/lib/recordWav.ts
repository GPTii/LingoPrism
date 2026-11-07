/**
 * Record the microphone and hand back a 16 kHz mono 16-bit WAV (what the pronunciation scorer reads).
 * MediaRecorder records in the browser's own format (webm / mp4); the browser decodes it again and an
 * OfflineAudioContext resamples it, so no codec is needed on the server.
 */
export const canRecord = () =>
  typeof window !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined'

export interface Recording {
  stop: () => Promise<Blob>
  cancel: () => void
}

export async function startRecording(): Promise<Recording> {
  let stream: MediaStream
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
  } catch {
    throw new Error('Hãy cho phép trình duyệt dùng micro để luyện nói.')
  }
  const recorder = new MediaRecorder(stream)
  const chunks: Blob[] = []
  recorder.ondataavailable = (e) => {
    if (e.data.size) chunks.push(e.data)
  }
  recorder.start()
  const release = () => stream.getTracks().forEach((t) => t.stop())
  return {
    cancel: () => {
      if (recorder.state !== 'inactive') recorder.stop()
      release()
    },
    stop: () =>
      new Promise<Blob>((resolve, reject) => {
        recorder.onstop = async () => {
          release()
          try {
            resolve(await toWav16k(new Blob(chunks, { type: recorder.mimeType })))
          } catch {
            reject(new Error('Không xử lý được bản ghi âm, thử lại nhé.'))
          }
        }
        recorder.stop()
      }),
  }
}

async function toWav16k(blob: Blob): Promise<Blob> {
  const ctx = new AudioContext()
  const decoded = await ctx.decodeAudioData(await blob.arrayBuffer())
  void ctx.close()
  const rate = 16000
  const offline = new OfflineAudioContext(1, Math.max(1, Math.ceil(decoded.duration * rate)), rate)
  const src = offline.createBufferSource()
  src.buffer = decoded
  src.connect(offline.destination)
  src.start()
  const pcm = (await offline.startRendering()).getChannelData(0)
  const buf = new ArrayBuffer(44 + pcm.length * 2)
  const v = new DataView(buf)
  const str = (o: number, s: string) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)))
  str(0, 'RIFF')
  v.setUint32(4, 36 + pcm.length * 2, true)
  str(8, 'WAVE')
  str(12, 'fmt ')
  v.setUint32(16, 16, true)
  v.setUint16(20, 1, true)
  v.setUint16(22, 1, true)
  v.setUint32(24, rate, true)
  v.setUint32(28, rate * 2, true)
  v.setUint16(32, 2, true)
  v.setUint16(34, 16, true)
  str(36, 'data')
  v.setUint32(40, pcm.length * 2, true)
  for (let i = 0; i < pcm.length; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, pcm[i])) * 0x7fff, true)
  return new Blob([buf], { type: 'audio/wav' })
}
