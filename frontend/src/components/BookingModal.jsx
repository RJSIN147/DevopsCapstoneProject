import { useState } from 'react';
import { api } from '../lib/api.js';
import { toIsoFromLocal, todayLocal } from '../lib/format.js';

export default function BookingModal({ doctors, onClose, onBooked }) {
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setSaving(true);
    try {
      await api.createAppointment({
        patient_name: f.get('patient_name'),
        patient_phone: f.get('patient_phone'),
        doctor_id: Number(f.get('doctor_id')),
        scheduled_at: toIsoFromLocal(f.get('day'), f.get('time')),
        duration_minutes: Number(f.get('duration')),
        reason: f.get('reason'),
      });
      onBooked();
    } catch (err) {
      // 409 from the API means the slot clashes, show it as is
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <p className="eyebrow">New appointment</p>
            <h2>Book a visit</h2>
          </div>
          <button type="button" className="close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <div className="alert small">{error}</div>}

        <div className="form-row">
          <label>
            Patient name
            <input name="patient_name" required minLength={2} autoFocus placeholder="Full name" />
          </label>
          <label>
            Phone
            <input name="patient_phone" pattern="[0-9+\-\s]*" placeholder="+91 98765 43210" />
          </label>
        </div>

        <label>
          Doctor
          <select name="doctor_id" required>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name} ({d.specialty})
              </option>
            ))}
          </select>
        </label>

        <div className="form-row three">
          <label>
            Date
            <input type="date" name="day" required defaultValue={todayLocal()} min={todayLocal()} />
          </label>
          <label>
            Time
            <input type="time" name="time" required defaultValue="10:00" step={300} />
          </label>
          <label>
            Length
            <select name="duration" defaultValue="20">
              <option value="10">10 min</option>
              <option value="20">20 min</option>
              <option value="30">30 min</option>
              <option value="45">45 min</option>
              <option value="60">60 min</option>
            </select>
          </label>
        </div>

        <label>
          Reason for visit
          <textarea name="reason" maxLength={500} placeholder="Follow-up, fever, consultation..." />
        </label>

        <button className="btn primary full" disabled={saving}>
          {saving ? 'Booking...' : 'Book appointment'}
        </button>
      </form>
    </div>
  );
}
