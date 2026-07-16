import { Link } from "react-router-dom";

export default function Breadcrumb({ items = [] }) {
  return (
    <nav aria-label="Breadcrumb" className="text-sm text-teal-deep/70 mb-6">
      <ol className="flex flex-wrap items-center gap-1.5">
        <li>
          <Link to="/" className="hover:text-mustard-deep">Home</Link>
        </li>
        {items.map((it, i) => (
          <li key={i} className="flex items-center gap-1.5">
            <span className="text-mustard-deep">/</span>
            {it.to ? (
              <Link to={it.to} className="hover:text-mustard-deep">{it.label}</Link>
            ) : (
              <span className="text-teal-deep font-semibold" aria-current="page">{it.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
