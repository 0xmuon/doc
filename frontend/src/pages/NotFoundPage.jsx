/** Any URL that is not a real page. */
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section>
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-3 text-sm">
        The page you are looking for does not exist. <Link to="/products" className="underline">Go to products</Link>
      </p>
    </section>
  );
}
