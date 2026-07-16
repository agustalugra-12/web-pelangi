import { NavLink, Link } from "react-router-dom";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { NAV, HOME } from "@/constants/testIds";
import BrandLogo from "@/components/site/BrandLogo";
import LanguageSwitcher from "@/components/site/LanguageSwitcher";

const linkDefs = [
  { to: "/", key: "home", id: NAV.home },
  { to: "/rooms", key: "rooms", id: NAV.rooms },
  { to: "/facilities", key: "facilities", id: NAV.facilities },
  { to: "/gallery", key: "gallery", id: NAV.gallery },
  { to: "/explore-bedugul", key: "explore", id: NAV.explore },
  { to: "/restaurant", key: "restaurant", id: NAV.restaurant },
  { to: "/about", key: "about", id: NAV.about },
  { to: "/blog", key: "blog", id: NAV.blog },
  { to: "/contact", key: "contact", id: NAV.contact },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { site } = useContent();
  const { t } = useLang();

  return (
    <header className="sticky top-0 z-50 bg-cream/85 backdrop-blur-md border-b border-ink/5">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-5 md:px-8 py-2.5">
        <Link
          to="/"
          className="flex items-center gap-3 group"
          data-testid="nav-brand"
        >
          <BrandLogo size={56} hoverFlip className="shrink-0" />
          <span className="hidden sm:flex flex-col leading-none">
            <span className="font-display italic text-xl md:text-2xl text-teal-deep tracking-tight">
              Pelangi <span className="text-mustard-deep">Homestay</span>
            </span>
            <span className="mt-1 font-script text-mustard-deep text-sm">
              Bedugul, Bali
            </span>
          </span>
        </Link>

        <nav className="hidden lg:flex items-center gap-6">
          {linkDefs.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              data-testid={l.id}
              end={l.to === "/"}
              className={({ isActive }) =>
                `text-sm font-medium tracking-wide transition-colors ${
                  isActive
                    ? "text-mustard-deep"
                    : "text-teal-deep/80 hover:text-teal-deep"
                }`
              }
            >
              {t(`nav.${l.key}`)}
            </NavLink>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <LanguageSwitcher />
          <a
            href={site.bookingUrl}
            target="_blank"
            rel="noopener noreferrer"
            data-testid={HOME.navBookBtn}
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-5 py-2.5 text-sm font-semibold shadow-paper-sm"
          >
            {t("common.bookNow")}
            <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
          </a>
        </div>

        <button
          type="button"
          className="lg:hidden inline-flex items-center justify-center h-10 w-10 rounded-full bg-teal-deep text-cream"
          onClick={() => setOpen((v) => !v)}
          data-testid={HOME.mobileMenuBtn}
          aria-label={t("common.toggleMenu")}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="lg:hidden border-t border-ink/5 bg-cream">
          <div className="px-5 py-4 flex flex-col gap-2">
            {linkDefs.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                data-testid={`${l.id}-mobile`}
                end={l.to === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg font-medium ${
                    isActive
                      ? "bg-teal-deep text-cream"
                      : "text-teal-deep hover:bg-mustard-soft/40"
                  }`
                }
              >
                {t(`nav.${l.key}`)}
              </NavLink>
            ))}
            <div className="mt-2 flex items-center justify-between gap-3">
              <LanguageSwitcher />
              <a
                href={site.bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-lift inline-flex items-center justify-center rounded-full bg-leaf text-white px-5 py-3 font-semibold flex-1"
              >
                {t("common.bookNow")}
              </a>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
