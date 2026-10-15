/** Shared loading and error panels so every page reports the same way. */
import PropTypes from "prop-types";

export function LoadingState({ label }) {
  return (
    <div className="panel mt-4 flex items-center gap-3 px-4 py-5" role="status" aria-live="polite">
      <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" aria-hidden="true" />
      <p className="text-sm text-slate-600">{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="panel mt-4 px-4 py-5" role="alert">
      <p className="text-sm font-semibold text-red-700">Something went wrong</p>
      <p className="mt-1 text-sm leading-6 text-red-700">{message}</p>
      {onRetry ? (
        <button type="button" className="btn-primary mt-4" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}

export function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
      {message}
    </p>
  );
}

LoadingState.propTypes = {
  label: PropTypes.string.isRequired,
};

ErrorState.propTypes = {
  message: PropTypes.string.isRequired,
  onRetry: PropTypes.func,
};

ErrorNote.propTypes = {
  message: PropTypes.string,
};
