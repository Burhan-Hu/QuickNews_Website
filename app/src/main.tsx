import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// @ts-expect-error JSX module
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
