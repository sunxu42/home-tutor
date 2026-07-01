import { API_BASE } from '@/services/api'

export interface IceServer {
  urls: string[]
  username?: string
  credential?: string
}

export interface WebRTCConfig {
  ice_servers: IceServer[]
}

export class WebRTCClient {
  private pc: RTCPeerConnection | null = null

  async init() {
    const response = await fetch(`${API_BASE}/webrtc/config`)
    const config = (await response.json()) as WebRTCConfig

    this.pc = new RTCPeerConnection({
      iceServers: config.ice_servers.map((server) => ({
        urls: server.urls,
        username: server.username,
        credential: server.credential,
      })),
    })

    return this.pc
  }

  async createOffer() {
    if (!this.pc) await this.init()
    const offer = await this.pc!.createOffer()
    await this.pc!.setLocalDescription(offer)

    await fetch(`${API_BASE}/webrtc/offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
    })

    return offer
  }

  close() {
    this.pc?.close()
    this.pc = null
  }
}

export const webrtcClient = new WebRTCClient()
