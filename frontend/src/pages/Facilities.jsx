import { useLang } from "@/context/LanguageContext";
import { DICTIONARY } from "@/i18n/dictionary";
import SectionHeading from "@/components/site/SectionHeading";

export default function Facilities() {
  const { t, lang } = useLang();
  const facs = DICTIONARY[lang]?.facilityData || DICTIONARY.id.facilityData;
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("facilities.eyebrow")}
          title={t("facilities.title")}
          italicWord={t("facilities.italic")}
          subtitle={t("facilities.subtitle")}
        />
        <div className="mt-12 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {facs.map((f, i) => (
            <div key={f.title} className="bg-paper rounded-2xl p-6 border border-ink/5 shadow-paper-sm reveal" style={{ animationDelay: `${i * 60}ms` }} data-testid={`facility-${f.title}`}>
              <div className="h-12 w-12 rounded-full bg-teal-deep text-mustard-soft flex items-center justify-center mb-3">
                <i className={`fa-solid ${f.icon} text-lg`} aria-hidden="true"></i>
              </div>
              <h3 className="font-display text-lg text-teal-deep">{f.title}</h3>
              <p className="mt-1 text-sm text-teal-deep/75">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
