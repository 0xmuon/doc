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
      <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-red-700 via-red-600 to-rose-500 px-6 py-10 text-white shadow-sm sm:px-10 sm:py-14">
        <p className="text-sm font-semibold tracking-wide text-rose-100">ABC Shop</p>
        <h1 className="mt-2 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">Everyday products, ready when you are.</h1>
        <p className="mt-3 max-w-xl text-base leading-7 text-rose-50">
          ABC Shop is the online shop. Look through products, add what you need to the cart, and check out.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/products" className="btn-cart">Browse products</Link>
          <Link to="/login" className="btn bg-white text-slate-900 hover:bg-rose-50">Login</Link>
        </div>
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {areas.map((area) => (
          <article key={area.title} className="panel flex flex-col p-5">
            <h2 className="text-lg font-semibold text-slate-900">{area.title}</h2>
            <p className="mt-2 flex-1 text-sm leading-6 text-slate-600">{area.text}</p>
            <Link to={area.to} className="btn-primary mt-5">
              {area.label}
            </Link>
          </article>
        ))}
      </div>
      <article className="panel mt-4 p-5">
        <h2 className="text-lg font-semibold text-slate-900">Account</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          New shoppers register with a name, email, and password. Returning shoppers log in with email and password.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/login" className="btn-primary">Login</Link>
          <Link to="/register" className="btn-outline">Register</Link>
        </div>
      </article>
    </section>
  );
}
