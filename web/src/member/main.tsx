import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import MemberPortal from './MemberPortal'

createRoot(document.getElementById('member-root')!).render(
  <StrictMode>
    <MemberPortal />
  </StrictMode>,
)
