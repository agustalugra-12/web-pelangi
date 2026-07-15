import { Link } from "react-router-dom";
import { SITE } from "@/data/content";
import BrandLogo from "@/components/site/BrandLogo";
import RainbowAccent from "@/components/site/RainbowAccent";

export default function Footer() {
  return (
    <footer className="relative bg-teal-deep text-cream mt-24">
      {/* Torn top edge */}
      <div className="absolute -top-10 left-0 right-0 h-10 pointer-events-none">
        <svg viewBox="0 0 1200 40" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0 40 C80 25 140 38 220 22 C300 8 360 34 440 20 C520 6 580 34 660 22 C740 8 800 34 880 22 C960 8 1020 34 1100 20 C1150 12 1180 26 1200 22 V40 Z"
            fill="#083D38"
          />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-16 pb-10 grid gap-10 md:grid-cols-4">
        <div>
          <Link to="/" className="group inline-flex items-center gap-3">
            <BrandLogo size={64} variant="light" hoverFlip />
            <span className="flex flex-col leading-none">
              <span className="font-display italic text-2xl text-cream">
                Pelangi <span className="text-mustard-soft">Homestay</span>
              </span>
              <span className="mt-1 font-script text-mustard-soft text-sm">
                Bedugul, Bali
              </span>
            </span>
          </Link>
          <RainbowAccent width="w-24" className="mt-4" />
          <p className="text-cream/75 text-sm leading-relaxed max-w-xs mt-4">
            Rumah hangat di jantung Bedugul — kabut pagi, kopi lokal, dan pelayanan tulus.
          </p>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">Jelajahi</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li><Link to="/rooms" className="hover:text-mustard-soft">Rooms</Link></li>
            <li><Link to="/facilities" className="hover:text-mustard-soft">Facilities</Link></li>
            <li><Link to="/gallery" className="hover:text-mustard-soft">Gallery</Link></li>
            <li><Link to="/explore-bedugul" className="hover:text-mustard-soft">Explore Bedugul</Link></li>
            <li><Link to="/restaurant" className="hover:text-mustard-soft">Restaurant</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">Info</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li><Link to="/about" className="hover:text-mustard-soft">About</Link></li>
            <li><Link to="/blog" className="hover:text-mustard-soft">Blog</Link></li>
            <li><Link to="/faq" className="hover:text-mustard-soft">FAQ</Link></li>
            <li><Link to="/contact" className="hover:text-mustard-soft">Contact</Link></li>
            <li><Link to="/admin/login" className="hover:text-mustard-soft text-cream/50">Admin</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">Hubungi</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li className="flex gap-2"><i className="fa-solid fa-location-dot mt-1 text-mustard-soft" aria-hidden="true"></i>{SITE.address}</li>
            <li className="flex gap-2"><i className="fa-brands fa-whatsapp mt-1 text-mustard-soft" aria-hidden="true"></i>{SITE.whatsappDisplay}</li>
            <li className="flex gap-2"><i className="fa-solid fa-envelope mt-1 text-mustard-soft" aria-hidden="true"></i>{SITE.email}</li>
            <li className="flex gap-2"><i className="fa-regular fa-clock mt-1 text-mustard-soft" aria-hidden="true"></i>{SITE.hours}</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-cream/10">
        <div className="max-w-7xl mx-auto px-6 py-5 text-xs text-cream/60 flex flex-col md:flex-row justify-between gap-2">
          <span>© {new Date().getFullYear()} Pelangi Homestay. Semua hak dilindungi.</span>
          <span>Made with <span className="text-mustard-soft">♥</span> for Bedugul.</span>
        </div>
      </div>
    </footer>
  );
}
