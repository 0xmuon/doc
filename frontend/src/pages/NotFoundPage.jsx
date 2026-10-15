/** Any URL that is not a real page. */
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="panel mx-auto max-w-lg px-6 py-12 text-center">
      <p className="text-sm font-semibold tracking-wide text-red-600">ABC Shop</p>
      <h1 className="page-title mt-2">Page not found</h1>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        The page you are looking for does not exist.
      </p>
      <Link to="/products" className="btn-primary mt-6">Go to products</Link>
    </section>
  );
}
