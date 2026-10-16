const NAV = [
  { id: 'schedule', label: 'Schedule', icon: '▤' },
  { id: 'doctors', label: 'Doctors', icon: '✚' },
];

export default function Sidebar({ view, onChange, doctorsOnDuty }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">✚</span>
        <div>
          <b>ClinicDesk</b>
          <small>Reception</small>
        </div>
      </div>

      <nav>
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${view === item.id ? 'active' : ''}`}
            onClick={() => onChange(item.id)}
          >
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="side-bottom">
        <div className="duty">
          <strong>{doctorsOnDuty}</strong>
          <span>doctors taking bookings</span>
        </div>
        <p className="build">build {import.meta.env.VITE_APP_VERSION || 'local'}</p>
      </div>
    </aside>
  );
}
