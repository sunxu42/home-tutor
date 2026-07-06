import { lazy, StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import './index.css'
import App from './App.tsx'

const SessionReviewPage = lazy(() =>
  import('./pages/SessionReviewPage').then((module) => ({
    default: module.SessionReviewPage,
  })),
)

function SessionReviewRouteFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <p className="text-sm text-muted-foreground">正在加载讲解回顾...</p>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route
          path="/sessions/:sessionId/review"
          element={
            <Suspense fallback={<SessionReviewRouteFallback />}>
              <SessionReviewPage />
            </Suspense>
          }
        />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
