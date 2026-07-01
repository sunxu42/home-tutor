type MessageHandler = (data: unknown) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Set<MessageHandler> = new Set()

  connect(url = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`) {
    this.ws = new WebSocket(url)

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as unknown
      this.handlers.forEach((handler) => handler(data))
    }

    this.ws.onclose = () => {
      this.ws = null
    }

    return this
  }

  onMessage(handler: MessageHandler) {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  send(payload: unknown) {
    this.ws?.send(JSON.stringify(payload))
  }

  disconnect() {
    this.ws?.close()
    this.ws = null
  }
}

export const wsClient = new WebSocketClient()
