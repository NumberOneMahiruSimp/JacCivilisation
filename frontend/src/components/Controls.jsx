export function Controls({ controls }) {
  return (
    <div className="control-stack">
      {controls.map(({ label, icon: Icon, onClick, tone }) => (
        <button className={`control-button ${tone ?? ""}`} key={label} onClick={onClick} title={label}>
          <Icon size={17} />
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}

