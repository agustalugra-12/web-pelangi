import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import SectionHeading from "@/components/site/SectionHeading";

const byCat = (arr, c) => arr.find((g) => g.category === c) || arr[0];

export default function Restaurant() {
  const { site, gallery, menu } = useContent();
  const { t, pick } = useLang();
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("restaurant.eyebrow")}
          title={t("restaurant.title")}
          italicWord={t("restaurant.italic")}
          subtitle={pick(site, "restaurantIntro")}
        />

        <div className="mt-12 grid md:grid-cols-5 gap-6 items-start">
          <div className="md:col-span-3 grid grid-cols-2 gap-3">
            <div className="col-span-2 aspect-[16/9] rounded-3xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "Restaurant").src} alt="Restaurant" className="w-full h-full object-cover" loading="lazy" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "Garden").src} alt="Garden" className="w-full h-full object-cover" loading="lazy" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "View").src} alt="View" className="w-full h-full object-cover" loading="lazy" />
            </div>
          </div>

          <div className="md:col-span-2 bg-paper rounded-3xl p-6 shadow-paper-sm border border-ink/5">
            <p className="font-script text-2xl text-mustard-deep">{t("restaurant.menuScript")}</p>
            <h3 className="font-display text-2xl text-teal-deep italic">{t("restaurant.menuTitle")}</h3>
            <ul className="mt-4 divide-y divide-ink/10">
              {menu.map((m) => (
                <li key={m.id || m.name} className="py-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="font-semibold text-teal-deep">{pick(m, "name")}</p>
                    <p className="font-display italic text-mustard-deep">{m.price}</p>
                  </div>
                  <p className="text-sm text-teal-deep/75">{pick(m, "desc")}</p>
                </li>
              ))}
            </ul>
            <p className="mt-5 text-sm text-teal-deep/75">
              {t("restaurant.hoursLabel")} <span className="font-semibold text-teal-deep">{pick(site, "restaurantHours")}</span>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
