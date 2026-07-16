import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import RoomCard from "@/components/site/RoomCard";
import SectionHeading from "@/components/site/SectionHeading";

export default function Rooms() {
  const { site, rooms } = useContent();
  const { t } = useLang();
  const policy = t("rooms.policy") || [];
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("rooms.eyebrow")}
          title={t("rooms.title")}
          italicWord={t("rooms.italic")}
          subtitle={t("rooms.subtitle")}
        />
        <div className="mt-12 grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {rooms.map((r, i) => <RoomCard key={r.id || r.slug} room={r} index={i} />)}
        </div>
        <div className="mt-16 bg-paper rounded-3xl p-8 md:p-12 border border-ink/5 shadow-paper-sm">
          <h3 className="font-display text-2xl text-teal-deep">{t("rooms.policyTitle")}</h3>
          <ul className="mt-4 grid md:grid-cols-2 gap-3 text-sm text-teal-deep/85 list-disc pl-5">
            {policy.map((line, i) => <li key={i}>{line}</li>)}
          </ul>
          <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer"
            className="btn-lift inline-flex mt-6 items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm">
            {t("common.checkAvailability")}
            <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
          </a>
        </div>
      </section>
    </div>
  );
}
