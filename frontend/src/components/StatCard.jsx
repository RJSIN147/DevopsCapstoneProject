export default function StatCard({ label, value, hint, tone }) {
  return (
    <div className={`stat tone-${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
      <span>{hint}</span>
    </div>
  );
}
