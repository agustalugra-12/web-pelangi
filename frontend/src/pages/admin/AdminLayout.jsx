import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import BrandLogo from "@/components/site/BrandLogo";
import { ADMIN } from "@/constants/testIds";

const NAV = [
  { to: "/admin/blog", label: "Blog", icon: "fa-newspaper" },
  { to: "/admin/rooms", label: "Rooms", icon: "fa-bed" },
  { to: "/admin/menu", label: "Menu", icon: "fa-utensils" },
  { to: "/admin/gallery", label: "Gallery", icon: "fa-images" },
  { to: "/admin/attractions", label: "Explore Bedugul", icon: "fa-mountain-sun" },
  { to: "/admin/faqs", label: "FAQ", icon: "fa-circle-question" },
  { to: "/admin/testimonials", label: "Testimoni", icon: "fa-quote-left" },
  { to: "/admin/media", label: "Media", icon: "fa-photo-film" },
  { to: "/admin/settings", label: "Pengaturan Umum", icon: "fa-gear" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const doLogout = async () => {
    await logout();
    navigate("/admin/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-cream flex">
      <aside className="hidden md:flex flex-col w-64 bg-teal-deep text-cream sticky top-0 h-screen">
        <div className="p-5 border-b border-cream/10">
          <Link to="/" className="flex items-center gap-3 group">
            <BrandLogo size={44} variant="light" hoverFlip />
            <span className="flex flex-col leading-none">
              <span className="font-display italic text-lg">Pelangi</span>
              <span className="text-[10px] uppercase tracking-widest text-mustard-soft mt-1">Admin</span>
            </span>
          </Link>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-3">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              data-testid={`admin-nav-${n.to.split("/").pop()}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-mustard text-teal-deep"
                    : "text-cream/85 hover:bg-cream/10"
                }`
              }
              end={n.to === "/admin/blog"}
            >
              <i className={`fa-solid ${n.icon} w-4 text-center`} aria-hidden="true"></i>
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-cream/10 text-xs text-cream/70">
          <p className="truncate">{user?.email}</p>
          <button
            type="button"
            onClick={doLogout}
            data-testid={ADMIN.logoutBtn}
            className="mt-2 w-full rounded-full border border-cream/40 py-1.5 hover:bg-cream hover:text-teal-deep transition-colors"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile top-bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-teal-deep text-cream px-4 py-3 flex items-center justify-between shadow-paper-sm">
        <Link to="/admin" className="flex items-center gap-2">
          <BrandLogo size={32} variant="light" />
          <span className="font-display italic">Pelangi Admin</span>
        </Link>
        <button
          type="button"
          onClick={doLogout}
          className="text-xs rounded-full border border-cream/40 px-3 py-1"
        >
          Logout
        </button>
      </div>

      <main className="flex-1 min-w-0 md:pl-0 pt-16 md:pt-0">
        {/* Mobile nav pills */}
        <div className="md:hidden overflow-x-auto no-scrollbar border-b border-ink/10 bg-cream/80 backdrop-blur-md">
          <div className="flex gap-2 px-4 py-2">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/admin/blog"}
                className={({ isActive }) =>
                  `shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold border-2 ${
                    isActive
                      ? "bg-mustard text-teal-deep border-mustard"
                      : "border-teal-deep/20 text-teal-deep"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </div>
        </div>
        <div className="p-5 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
