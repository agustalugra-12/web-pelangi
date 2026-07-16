import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { HOME } from "@/constants/testIds";

export default function WhatsAppButton() {
  const { site } = useContent();
  const { t } = useLang();
  const href = `https://wa.me/${site.whatsapp}?text=${encodeURIComponent(t("whatsapp.prefill"))}`;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      data-testid={HOME.whatsappBtn}
      className="fixed bottom-6 right-6 z-40 group"
      aria-label={t("whatsapp.label")}
    >
      <span className="absolute inset-0 rounded-full bg-leaf/60 animate-pulseRing" aria-hidden="true"></span>
      <span className="relative inline-flex h-14 w-14 items-center justify-center rounded-full bg-leaf text-white shadow-paper hover:scale-105 transition-transform">
        <i className="fa-brands fa-whatsapp text-2xl" aria-hidden="true"></i>
      </span>
    </a>
  );
}
