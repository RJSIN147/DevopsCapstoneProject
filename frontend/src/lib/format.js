export const STATUS_LABELS = {
  BOOKED: 'Booked',
  CHECKED_IN: 'Checked in',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
};

// What the front desk can do next with an appointment in a given state
export function nextActions(status) {
  switch (status) {
    case 'BOOKED':
      return [
        { status: 'CHECKED_IN', label: 'Check in' },
        { status: 'CANCELLED', label: 'Cancel' },
      ];
    case 'CHECKED_IN':
      return [{ status: 'COMPLETED', label: 'Complete' }];
    default:
      return [];
  }
}

export function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatDay(iso) {
  return new Date(iso).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
}

export function initials(name = '') {
  return name
    .replace(/^Dr\.?\s+/i, '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join('');
}

// <input type="date"> gives "YYYY-MM-DD" and <input type="time"> gives "HH:MM" in local time.
// The API stores UTC, so build a local Date and let toISOString convert.
export function toIsoFromLocal(day, time) {
  if (!day || !time) return null;
  const [y, m, d] = day.split('-').map(Number);
  const [hh, mm] = time.split(':').map(Number);
  return new Date(y, m - 1, d, hh, mm).toISOString();
}

export function todayLocal(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function greeting(hour = new Date().getHours()) {
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}
