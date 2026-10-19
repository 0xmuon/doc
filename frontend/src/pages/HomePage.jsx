import { Link } from "react-router-dom";
import { useAuth } from "../context/auth-context";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=2000&q=80";

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

const signedInActions = [
  {
    title: "Browse products",
    text: "Search the catalog and add items to your cart.",
    to: "/products",
    label: "Go to products",
  },
  {
    title: "Review your cart",
    text: "Check quantities and totals, then continue to checkout.",
    to: "/cart",
    label: "Go to cart",
  },
  {
    title: "Track your orders",
    text: "Open past orders, payment status, and order details.",
    to: "/orders",
    label: "Go to orders",
  },
  {
    title: "Open your profile",
    text: "See your account details and placed orders.",
    to: "/profile",
    label: "Go to profile",
  },
];

function Hero({ title, text, primary, secondary }) {
  return (
    <section className="shop-hero">
      <div className="shop-hero__media" aria-hidden="true">
        <img src={HERO_IMAGE} alt="" />
      </div>
      <div className="shop-hero__shade" aria-hidden="true" />
      <div className="shop-hero__content">
        <p className="shop-hero__brand">
          ABC <span>Shop</span>
        </p>
        <h1 className="mt-5 font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h1>
        <p className="mt-3 max-w-md text-[0.95rem] leading-6 text-neutral-200">{text}</p>
        <div className="mt-7 flex flex-wrap gap-2.5">
          <Link to={primary.to} className="btn-cart px-5 py-2.5 text-sm">
            {primary.label}
          </Link>
          <Link to={secondary.to} className="btn-ghost-light px-5 py-2.5 text-sm">
            {secondary.label}
          </Link>
        </div>
      </div>
    </section>
  );
}

export default function HomePage() {
  const { user, ready } = useAuth();

  if (!ready && !user) {
    return (
      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="panel px-6 py-10 text-center text-sm text-neutral-600">Loading your home page...</div>
      </section>
    );
  }

  if (user) {
    const firstName = user.name.trim().split(/\s+/)[0] || user.name;
    return (
      <section>
        <Hero
          title={`Hi ${firstName}`}
          text="You are signed in. Here is what you can do next."
          primary={{ to: "/products", label: "Browse products" }}
          secondary={{ to: "/cart", label: "View cart" }}
        />
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <h2 className="page-title">You can do the following things</h2>
          <p className="page-lead">Pick a step below to keep shopping or manage your account.</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {signedInActions.map((action) => (
              <article key={action.title} className="panel-interactive flex flex-col p-5">
                <h3 className="font-display text-lg font-semibold text-neutral-900">{action.title}</h3>
                <p className="mt-1.5 flex-1 text-sm leading-6 text-neutral-600">{action.text}</p>
                <Link to={action.to} className="btn-primary mt-5 w-fit">
                  {action.label}
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section>
      <Hero
        title="Everyday products, ready when you are."
        text="Look through products, add what you need to the cart, and check out with card or cash on delivery."
        primary={{ to: "/products", label: "Browse products" }}
        secondary={{ to: "/login", label: "Login" }}
      />
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="grid gap-3 sm:grid-cols-3">
          {areas.map((area) => (
            <article key={area.title} className="panel-interactive flex flex-col p-5">
              <h2 className="font-display text-lg font-semibold text-neutral-900">{area.title}</h2>
              <p className="mt-1.5 flex-1 text-sm leading-6 text-neutral-600">{area.text}</p>
              <Link to={area.to} className="btn-primary mt-5 w-fit">
                {area.label}
              </Link>
            </article>
          ))}
        </div>
        <article className="panel mt-3 p-5">
          <h2 className="font-display text-lg font-semibold text-neutral-900">Account</h2>
          <p className="mt-1.5 text-sm leading-6 text-neutral-600">
            New shoppers register with a name, email, and password. Returning shoppers log in with email and password.
          </p>
          <div className="mt-4 flex flex-wrap gap-2.5">
            <Link to="/login" className="btn-primary">
              Login
            </Link>
            <Link to="/register" className="btn-outline">
              Register
            </Link>
          </div>
        </article>
      </div>
    </section>
  );
}
