import { Link } from "react-router-dom";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import BrandLogo from "@/components/site/BrandLogo";
import RainbowAccent from "@/components/site/RainbowAccent";

export default function Footer() {
  const { site } = useContent();
  const { t, pick } = useLang();
  const tagline = pick(site, "tagline");
  return (
    <footer className="relative bg-teal-deep text-cream mt-24">
      <div className="absolute -top-10 left-0 right-0 h-10 pointer-events-none">
        <svg viewBox="0 0 1200 40" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0 40 C80 25 140 38 220 22 C300 8 360 34 440 20 C520 6 580 34 660 22 C740 8 800 34 880 22 C960 8 1020 34 1100 20 C1150 12 1180 26 1200 22 V40 Z"
            fill="#083D38"
          />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-16 pb-10 grid gap-10 md:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Link to="/" className="group inline-flex items-center gap-3">
            <BrandLogo size={64} variant="light" hoverFlip />
            <span className="flex flex-col leading-none">
              <span className="font-display italic text-2xl text-cream">
                Pelangi <span className="text-mustard-soft">Homestay</span>
              </span>
              <span className="mt-1 font-script text-mustard-soft text-sm">Bedugul, Bali</span>
            </span>
          </Link>
          <RainbowAccent width="w-24" className="mt-4" />
          <p className="text-cream/75 text-sm leading-relaxed max-w-xs mt-4">
            {tagline} {t("footer.taglineSuffix")}
          </p>
          <p className="text-cream/60 text-xs mt-4">{t("footer.roomsInfo")}</p>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">{t("footer.explore")}</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li><Link to="/rooms" className="hover:text-mustard-soft">{t("footer.links.rooms")}</Link></li>
            <li><Link to="/facilities" className="hover:text-mustard-soft">{t("footer.links.facilities")}</Link></li>
            <li><Link to="/gallery" className="hover:text-mustard-soft">{t("footer.links.gallery")}</Link></li>
            <li><Link to="/restaurant" className="hover:text-mustard-soft">{t("footer.links.restaurant")}</Link></li>
            <li><Link to="/explore-bedugul" className="hover:text-mustard-soft">{t("footer.links.explore")}</Link></li>
            <li><Link to="/blog" className="hover:text-mustard-soft">{t("footer.links.blog")}</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">{t("footer.information")}</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li><Link to="/about" className="hover:text-mustard-soft">{t("footer.links.about")}</Link></li>
            <li><Link to="/payment-information" className="hover:text-mustard-soft">{t("footer.links.paymentInfo")}</Link></li>
            <li><Link to="/house-rules" className="hover:text-mustard-soft">{t("footer.links.houseRules")}</Link></li>
            <li><Link to="/faq" className="hover:text-mustard-soft">{t("footer.links.faq")}</Link></li>
            <li><Link to="/contact" className="hover:text-mustard-soft">{t("footer.links.contact")}</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-display text-lg mb-3 text-mustard-soft">{t("footer.legal")}</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li><Link to="/privacy-policy" className="hover:text-mustard-soft">{t("footer.links.privacy")}</Link></li>
            <li><Link to="/terms-and-conditions" className="hover:text-mustard-soft">{t("footer.links.terms")}</Link></li>
            <li><Link to="/cancellation-policy" className="hover:text-mustard-soft">{t("footer.links.cancellation")}</Link></li>
            <li><Link to="/refund-policy" className="hover:text-mustard-soft">{t("footer.links.refund")}</Link></li>
          </ul>

          <h4 className="font-display text-lg mt-6 mb-3 text-mustard-soft">{t("footer.contactHeading")}</h4>
          <ul className="space-y-2 text-sm text-cream/85">
            <li className="flex gap-2"><i className="fa-solid fa-location-dot mt-1 text-mustard-soft" aria-hidden="true"></i>{pick(site, "address")}</li>
            <li className="flex gap-2"><i className="fa-brands fa-whatsapp mt-1 text-mustard-soft" aria-hidden="true"></i>{site.whatsappDisplay}</li>
            <li className="flex gap-2"><i className="fa-solid fa-envelope mt-1 text-mustard-soft" aria-hidden="true"></i>{site.email}</li>
            <li className="flex gap-2"><i className="fa-regular fa-clock mt-1 text-mustard-soft" aria-hidden="true"></i>{pick(site, "hours")}</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-cream/10">
        <div className="max-w-7xl mx-auto px-6 py-5 text-xs text-cream/60 flex flex-col md:flex-row justify-between gap-2">
          <span>© {new Date().getFullYear()} {site.brand}. {t("footer.copyright")}</span>
          <span>{t("footer.madeWith")} <span className="text-mustard-soft">♥</span> {t("footer.forBedugul")}</span>
        </div>
      </div>
    </footer>
  );
}
