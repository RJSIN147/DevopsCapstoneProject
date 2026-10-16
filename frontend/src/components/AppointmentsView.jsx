import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { STATUS_LABELS, formatDay, formatTime, nextActions, todayLocal } from '../lib/format.js';

const FILTERS = ['ALL', 'BOOKED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED'];

export default function AppointmentsView({ doctors, refreshKey, onChanged }) {
  const [appointments, setAppointments] = useState([]);
  const [status, setStatus] = useState('ALL');
  const [doctorId, setDoctorId] = useState('');
  const [day, setDay] = useState(todayLocal());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listAppointments({
        status: status === 'ALL' ? '' : status,
        doctor_id: doctorId,
        // the API works out the day in the clinic's timezone (CLINIC_TIMEZONE on the backend)
        on: day,
      })
      .then((rows) => {
        if (cancelled) return;
        setAppointments(rows);
        setError('');
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [status, doctorId, day, refreshKey]);

  const move = async (appt, next) => {
    try {
      await api.updateAppointment(appt.id, { status: next });
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  };

  const remove = async (appt) => {
    if (!window.confirm(`Delete the appointment for ${appt.patient_name}?`)) return;
    try {
      await api.deleteAppointment(appt.id);
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Appointments</h2>
          <p className="muted">Check patients in as they arrive and close the visit when they leave.</p>
        </div>
        <div className="toolbar">
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} aria-label="Day" />
          <button className="btn ghost small" onClick={() => setDay('')} disabled={!day}>
            All days
          </button>
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)} aria-label="Doctor">
            <option value="">All doctors</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filters" role="tablist">
        {FILTERS.map((f) => (
          <button key={f} className={status === f ? 'selected' : ''} onClick={() => setStatus(f)}>
            {f === 'ALL' ? 'All' : STATUS_LABELS[f]}
          </button>
        ))}
      </div>

      {error && <div className="alert small">{error}</div>}

      {loading ? (
        <div className="empty">Loading appointments...</div>
      ) : appointments.length === 0 ? (
        <div className="empty">Nothing here for this filter.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td data-label="Time">
                    <b>{formatTime(a.scheduled_at)}</b>
                    <small>
                      {formatDay(a.scheduled_at)} · {a.duration_minutes} min
                    </small>
                  </td>
                  <td data-label="Patient">
                    <b>{a.patient_name}</b>
                    <small>{a.reason || a.patient_phone || '-'}</small>
                  </td>
                  <td data-label="Doctor">
                    <b>{a.doctor_name}</b>
                    <small>{a.specialty}</small>
                  </td>
                  <td data-label="Status">
                    <span className={`badge ${a.status.toLowerCase()}`}>{STATUS_LABELS[a.status]}</span>
                  </td>
                  <td className="actions">
                    {nextActions(a.status).map((act) => (
                      <button key={act.status} className="btn small" onClick={() => move(a, act.status)}>
                        {act.label}
                      </button>
                    ))}
                    <button className="btn small ghost" onClick={() => remove(a)} title="Delete">
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
