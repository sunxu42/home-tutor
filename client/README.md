# Home Tutor Client

React + Vite + shadcn/ui 浏览器客户端。

## 目录结构

```
client/
├── src/
│   ├── components/ui/   # shadcn 组件
│   ├── hooks/           # React hooks
│   ├── lib/             # 工具函数
│   ├── pages/           # 页面（按需添加）
│   └── services/        # 通讯层
│       ├── api.ts       # HTTP
│       ├── websocket.ts # WebSocket
│       └── webrtc.ts    # WebRTC
├── components.json      # shadcn 配置
└── vite.config.ts       # 含 /api、/ws 代理
```

## 开发

```bash
npm install
npm run dev
```

## 添加 shadcn 组件

```bash
npx shadcn@latest add <component>
```
