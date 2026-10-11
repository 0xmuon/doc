export default function QuantityStepper({ name, quantity, max, busy, onChange }) {
  return (
    <div className="flex items-center rounded border border-slate-300 bg-white">
      <button
        type="button"
        aria-label={`Decrease quantity of ${name}`}
        className="px-3 py-1 text-lg leading-none text-slate-800 hover:bg-slate-50 disabled:opacity-50"
        onClick={() => onChange(quantity - 1)}
        disabled={busy || quantity < 1}
      >
        −
      </button>
      <span className="min-w-8 text-center text-sm" aria-live="polite">{quantity}</span>
      <button
        type="button"
        aria-label={`Increase quantity of ${name}`}
        className="px-3 py-1 text-lg leading-none text-slate-800 hover:bg-slate-50 disabled:opacity-50"
        onClick={() => onChange(quantity + 1)}
        disabled={busy || quantity >= max}
      >
        +
      </button>
    </div>
  );
}
