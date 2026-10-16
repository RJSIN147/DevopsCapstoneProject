import { useCallback, useEffect, useState } from 'react';
import { api } from './lib/api.js';
import { greeting } from './lib/format.js';
import Sidebar from './components/Sidebar.jsx';
import StatCard from './components/StatCard.jsx';
import AppointmentsView from './components/AppointmentsView.jsx';
import DoctorsView from './components/DoctorsView.jsx';
import BookingModal from './components/BookingModal.jsx';

const EMPTY_STATS = { total: 0, today: 0, booked: 0, checkedIn: 0, completed: 0, cancelled: 0, activeDoctors: 0 };

export default function App() {
  const [view, setView] = useState('schedule');
  const [doctors, setDoctors] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [error, setError] = useState('');
  const [showBooking, setShowBooking] = useState(false);
  // bumping this makes the appointment list refetch after a change made elsewhere
  const [refreshKey, setRefreshKey] = useState(0);

  const loadShared = useCallback(async () => {
    try {
      const [docs, s] = await Promise.all([api.listDoctors(), api.stats()]);
      setDoctors(docs);
      setStats(s);
      setError('');
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    loadShared();
  }, [loadShared]);

  const changed = () => {
    loadShared();
    setRefreshKey((k) => k + 1);
  };

  const today = new Date().toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="app">
      <Sidebar view={view} onChange={setView} doctorsOnDuty={stats.activeDoctors} />

      <main className="main">
        <header className="page-head">
          <div>
            <p className="eyebrow">{today}</p>
            <h1>{greeting()}, front desk</h1>
            <p className="muted">
              {stats.today} appointment{stats.today === 1 ? '' : 's'} on the books today, {stats.checkedIn} waiting.
            </p>
          </div>
          <button className="btn primary" onClick={() => setShowBooking(true)} disabled={!doctors.length}>
            + New appointment
          </button>
        </header>

        {error && (
          <div className="alert" role="alert">
            Could not reach the API ({error}). Check that the backend and Postgres are running, then reload.
          </div>
        )}

        <section className="stats">
          <StatCard label="Today" value={stats.today} hint="excluding cancelled" tone="teal" />
          <StatCard label="Waiting room" value={stats.checkedIn} hint="checked in" tone="amber" />
          <StatCard label="Completed" value={stats.completed} hint="all time" tone="green" />
          <StatCard label="Cancelled" value={stats.cancelled} hint="all time" tone="rose" />
        </section>

        {view === 'schedule' ? (
          <AppointmentsView doctors={doctors} refreshKey={refreshKey} onChanged={changed} />
        ) : (
          <DoctorsView doctors={doctors} onChanged={changed} />
        )}
      </main>

      {showBooking && (
        <BookingModal
          doctors={doctors.filter((d) => d.active)}
          onClose={() => setShowBooking(false)}
          onBooked={() => {
            setShowBooking(false);
            changed();
          }}
        />
      )}
    </div>
  );
}
