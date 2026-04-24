export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return 'Pending'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en-IN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

export function formatRole(role: string): string {
  return role.replaceAll('_', ' ')
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Unexpected error'
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}
