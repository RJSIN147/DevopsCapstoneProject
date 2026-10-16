import { useState } from 'react';
import { api } from '../lib/api.js';
import { initials } from '../lib/format.js';

export default function DoctorsView({ doctors, onChanged }) {
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const add = async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    setSaving(true);
    try {
      await api.createDoctor({
        full_name: f.get('full_name'),
        specialty: f.get('specialty'),
        room: f.get('room'),
      });
      form.reset();
      setError('');
      onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const toggle = async (doc) => {
    try {
      await api.updateDoctor(doc.id, { active: !doc.active });
      onChanged();
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async (doc) => {
    if (!window.confirm(`Remove ${doc.full_name}?`)) return;
    try {
      await api.deleteDoctor(doc.id);
      onChanged();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Doctors</h2>
          <p className="muted">Pause a doctor to stop new bookings without losing their history.</p>
        </div>
      </div>

      {error && <div className="alert small">{error}</div>}

      <div className="doctor-grid">
        {doctors.map((d) => (
          <article key={d.id} className={`doctor ${d.active ? '' : 'inactive'}`}>
            <span className="avatar">{initials(d.full_name)}</span>
            <div className="doctor-info">
              <b>{d.full_name}</b>
              <small>
                {d.specialty}
                {d.room ? ` · Room ${d.room}` : ''}
              </small>
            </div>
            <div className="doctor-actions">
              <button className="btn small" onClick={() => toggle(d)}>
                {d.active ? 'Pause' : 'Resume'}
              </button>
              <button className="btn small ghost" onClick={() => remove(d)} title="Remove">
                ✕
              </button>
            </div>
          </article>
        ))}
      </div>

      <form className="inline-form" onSubmit={add}>
        <h3>Add a doctor</h3>
        <div className="form-row three">
          <label>
            Name
            <input name="full_name" required minLength={2} placeholder="Dr. Meera Iyer" />
          </label>
          <label>
            Specialty
            <input name="specialty" required minLength={2} placeholder="Cardiology" />
          </label>
          <label>
            Room
            <input name="room" maxLength={20} placeholder="202" />
          </label>
        </div>
        <button className="btn primary" disabled={saving}>
          {saving ? 'Saving...' : 'Add doctor'}
        </button>
      </form>
    </section>
  );
}
