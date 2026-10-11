import { Link } from "react-router-dom";

const areas = [
  {
    title: "Products",
    text: "Browse the catalog, search by name or category, and open a product to see its details.",
    to: "/products",
    label: "View products",
  },
  {
    title: "Cart",
    text: "Add items, change quantities, remove a line, and see the item count and total.",
    to: "/cart",
    label: "View cart",
  },
  {
    title: "Orders",
    text: "Check out with a credit card or cash on delivery, then open past orders and their details.",
    to: "/orders",
    label: "View orders",
  },
];

export default function HomePage() {
  return (
    <section>
      <h1 className="text-2xl font-semibold">Home</h1>
      <p className="mt-3 max-w-2xl text-slate-700">
        ABC Shop is the online shop. Look through products, add what you need to the cart, and check out.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {areas.map((area) => (
          <article key={area.title} className="flex flex-col rounded border border-rose-100 bg-white p-4 shadow-sm">
            <h2 className="text-base font-semibold">{area.title}</h2>
            <p className="mt-2 flex-1 text-sm text-slate-700">{area.text}</p>
            <Link to={area.to} className="mt-4 inline-block rounded bg-blue-600 px-3 py-2 text-center text-sm text-white hover:bg-blue-700">
              {area.label}
            </Link>
          </article>
        ))}
      </div>
      <article className="mt-4 rounded border border-rose-100 bg-white p-4 shadow-sm">
        <h2 className="text-base font-semibold">Account</h2>
        <p className="mt-2 text-sm text-slate-700">
          New shoppers register with a name, email, and password. Returning shoppers log in with email and password.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/login" className="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
            Login
          </Link>
          <Link to="/register" className="rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 hover:bg-slate-50">
            Register
          </Link>
        </div>
      </article>
    </section>
  );
}
