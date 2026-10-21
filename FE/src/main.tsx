import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App as AntApp } from 'antd'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App'
import ThemeRoot from './theme/ThemeRoot'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeRoot>
        {/* no wrapper element: antd's `.ant-app a { color }` would repaint every NavLink violet */}
        <AntApp component={false}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AntApp>
      </ThemeRoot>
    </QueryClientProvider>
  </StrictMode>,
)
