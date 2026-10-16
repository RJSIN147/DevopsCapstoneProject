const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (res.status === 204) return null;

  let body = null;
  try {
    body = await res.json();
  } catch {
    // non-json error page from nginx etc.
  }
  if (!res.ok) {
    throw new Error(errorMessage(body) || `Request failed (${res.status})`);
  }
  return body;
}

// FastAPI returns either {detail: "text"} or {detail: [{msg, loc}, ...]} for validation errors
export function errorMessage(body) {
  if (!body || !body.detail) return '';
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((d) => `${d.loc?.slice(-1)[0] ?? 'field'}: ${d.msg}`)
      .join(', ');
  }
  return '';
}

export const api = {
  listAppointments: (params = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/appointments${q ? `?${q}` : ''}`);
  },
  stats: () => request('/appointments/stats'),
  createAppointment: (data) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  updateAppointment: (id, data) => request(`/appointments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),

  listDoctors: () => request('/doctors'),
  createDoctor: (data) => request('/doctors', { method: 'POST', body: JSON.stringify(data) }),
  updateDoctor: (id, data) => request(`/doctors/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: 'DELETE' }),
};
