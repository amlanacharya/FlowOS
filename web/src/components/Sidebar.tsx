import type { ReactNode } from 'react'
import { MANAGER_ROLES, Page, Role, TRAINER_ALLOWED_PAGES, type PageValue } from '../constants'

type Props = {
  currentPage: PageValue
  onNavigate: (page: PageValue) => void
  onLogout: () => void
  userName: string
  userRole: string
  health: 'checking' | 'online' | 'offline'
}

function IconDashboard() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="14" width="7" height="7" rx="2" />
      <rect x="3" y="14" width="7" height="7" rx="2" />
    </svg>
  )
}

function IconLeads() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <line x1="19" y1="8" x2="19" y2="14" />
      <line x1="22" y1="11" x2="16" y2="11" />
    </svg>
  )
}

function IconMembers() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function IconPayments() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="5" width="20" height="14" rx="3" />
      <line x1="2" y1="10" x2="22" y2="10" />
    </svg>
  )
}

function IconAttendance() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 7V3m8 4V3" />
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 11h18" />
      <path d="m8 16 2 2 5-5" />
    </svg>
  )
}

function IconEngagement() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z" />
    </svg>
  )
}

function IconSettings() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}

function IconLogout() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}

const navGroups: { label: string; items: { id: PageValue; label: string; icon: () => ReactNode }[] }[] = [
  {
    label: 'Operations',
    items: [
      { id: Page.Dashboard, label: 'Dashboard', icon: IconDashboard },
      { id: Page.Payments, label: 'Payments', icon: IconPayments },
      { id: Page.Members, label: 'Members', icon: IconMembers },
      { id: Page.Leads, label: 'Leads', icon: IconLeads },
      { id: Page.StaffAttendance, label: 'Staff Attendance', icon: IconAttendance },
      { id: Page.Engagement, label: 'Engagement', icon: IconEngagement },
      { id: Page.Trainer, label: 'Trainer View', icon: IconAttendance },
    ],
  },
  {
    label: 'Workspace',
    items: [{ id: Page.Settings, label: 'Settings', icon: IconSettings }],
  },
]

function canShowPage(page: PageValue, userRole: string) {
  const managerRoles = MANAGER_ROLES as readonly string[]
  const trainerPages = TRAINER_ALLOWED_PAGES as readonly string[]

  if (userRole === Role.Trainer) return trainerPages.includes(page)
  if (page === Page.Trainer) return false
  if (page === Page.StaffAttendance) return managerRoles.includes(userRole)
  if (page === Page.Engagement) return [...managerRoles, Role.Trainer].includes(userRole)
  return true
}

export default function Sidebar({ currentPage, onNavigate, onLogout, userName, userRole, health }: Props) {
  const initials = userName
    ? userName
        .split(' ')
        .map((word) => word[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'FO'

  const healthCopy =
    health === 'online'
      ? 'API connected'
      : health === 'offline'
        ? 'API unreachable'
        : 'Checking connection'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">FO</div>
        <div>
          <div className="sidebar-logo-text">FlowOS</div>
          <div className="sidebar-logo-sub">Club operations console</div>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        {navGroups.map((group) => (
          <div key={group.label}>
            <div className="nav-section-label">{group.label}</div>
            {group.items
              .filter((item) => canShowPage(item.id, userRole))
              .map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
                  onClick={() => onNavigate(item.id)}
                >
                  <item.icon />
                  <span>{item.label}</span>
                </button>
              ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="user-avatar">{initials}</div>
          <div className="user-info">
            <div className="user-name">{userName || 'FlowOS operator'}</div>
            <div className="user-role">{userRole.replaceAll('_', ' ') || 'staff session'}</div>
          </div>
        </div>

        <div className="sidebar-status">
          <div className={`status-dot ${health}`} />
          <span className="status-text">{healthCopy}</span>
        </div>

        <button className="nav-item" type="button" onClick={onLogout}>
          <IconLogout />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  )
}
