import { Link } from "react-router-dom";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import RoomCard from "@/components/site/RoomCard";
import SectionHeading from "@/components/site/SectionHeading";
import { DICTIONARY } from "@/i18n/dictionary";
import { HOME } from "@/constants/testIds";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const galleryByCategory = (arr, cat) => arr.find((g) => g.category === cat) || arr[0];

export default function Home() {
  const { site, rooms, gallery, attractions, testimonials, faqs } = useContent();
  const { t, lang, pick } = useLang();
  const facs = DICTIONARY[lang]?.facilityData || DICTIONARY.id.facilityData;

  return (
    <div>
      <section data-testid={HOME.hero} className="relative overflow-hidden pt-8 pb-24 md:pb-32">
        <div className="max-w-7xl mx-auto px-5 md:px-8 grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 relative">
            <div className="relative bg-teal-deep text-cream rounded-[36px] p-8 md:p-12 shadow-paper overflow-hidden">
              <svg viewBox="0 0 400 120" className="absolute top-4 right-4 w-40 h-12 text-mustard-soft opacity-80">
                <path d="M10 100 Q120 20 260 40 T390 30" stroke="currentColor" strokeWidth="2" fill="none" className="doodle-dash" />
                <path d="M380 20 L400 30 L378 42 L385 30 Z" fill="currentColor" />
              </svg>

              <p className="font-script text-3xl md:text-4xl text-mustard-soft mb-1">{pick(site, "heroEyebrow")}</p>
              <h1 className="font-display font-semibold text-5xl md:text-6xl lg:text-7xl leading-[0.95]">
                {pick(site, "heroTitle")}<span className="text-mustard-soft">.</span>
                <br />
                <span className="italic font-light">{pick(site, "heroSubtitle")}</span>
              </h1>
              <p className="mt-5 max-w-md text-cream/85 text-base md:text-lg leading-relaxed">
                {pick(site, "heroBody")}
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer" data-testid={HOME.bookNowBtn}
                  className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-7 py-3.5 font-semibold shadow-paper-sm">
                  {t("common.bookNow")}
                  <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
                </a>
                <Link to="/rooms" className="btn-lift inline-flex items-center gap-2 rounded-full border-2 border-mustard-soft text-mustard-soft px-6 py-3 font-semibold hover:bg-mustard-soft hover:text-teal-deep">
                  {t("common.viewRooms")}
                </Link>
              </div>

              <svg viewBox="0 0 800 40" preserveAspectRatio="none" className="absolute -bottom-1 left-0 right-0 w-full h-8">
                <path d="M0 40 C60 20 100 34 160 22 C220 10 260 30 320 20 C380 10 420 32 480 22 C540 12 580 30 640 22 C700 12 740 30 800 20 V40 Z" fill="#F7F3EA"/>
              </svg>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="relative">
              <div className="blob overflow-hidden shadow-paper w-full aspect-[4/5] max-w-sm mx-auto">
                <img src="/assets/signage.jpg" alt="Pelangi Homestay signage" className="w-full h-full object-cover" loading="eager" fetchpriority="high" />
              </div>
              {attractions[0] && (
                <div className="absolute -bottom-8 -left-6 w-40 h-40 rounded-full overflow-hidden shadow-paper border-4 border-cream hidden md:block">
                  <img src={attractions[0].image} alt={pick(attractions[0], "title")} className="w-full h-full object-cover" loading="lazy" />
                </div>
              )}
              {attractions[attractions.length - 1] && (
                <div className="absolute -top-6 -right-4 w-28 h-28 rounded-full overflow-hidden shadow-paper border-4 border-cream hidden md:block">
                  <img src={attractions[attractions.length - 1].image} alt={pick(attractions[attractions.length - 1], "title")} className="w-full h-full object-cover" loading="lazy" />
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="grid md:grid-cols-2 gap-10 items-center">
          <div>
            <p className="font-script text-3xl text-mustard-deep">{t("home.aboutEyebrow")}</p>
            <h2 className="font-display text-4xl md:text-5xl text-teal-deep leading-tight mt-1">
              {t("home.aboutTitle")} <span className="italic text-mustard-deep">{t("home.aboutTitleItalic")}</span> {t("home.aboutTitleSuffix")}
            </h2>
            <p className="mt-4 text-teal-deep/80 leading-relaxed">
              {site.brand} {t("home.aboutBody")}
            </p>
            <Link to="/about" className="btn-lift inline-flex mt-6 items-center gap-2 rounded-full border-2 border-teal text-teal-deep px-5 py-2.5 font-semibold hover:bg-teal-deep hover:text-cream">
              {t("common.ourStory")}
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 aspect-[4/3] rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory(gallery, "Garden").src} alt="Garden" className="w-full h-full object-cover" loading="lazy" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory(gallery, "Restaurant").src} alt="Restaurant" className="w-full h-full object-cover" loading="lazy" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory(gallery, "View").src} alt="View" className="w-full h-full object-cover" loading="lazy" />
            </div>
            <div className="col-span-2 aspect-[4/3] rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={rooms[0]?.image} alt="Room" className="w-full h-full object-cover" loading="lazy" />
            </div>
          </div>
        </div>
      </section>

      <section className="bg-paper py-20">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading eyebrow={t("home.roomsEyebrow")} title={t("home.roomsTitle")} italicWord={t("home.roomsItalic")} subtitle={t("home.roomsSub")} />
          <div className="mt-12 grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {rooms.map((r, i) => <RoomCard key={r.id || r.slug} room={r} index={i} />)}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24">
        <SectionHeading eyebrow={t("home.facilitiesEyebrow")} title={t("home.facilitiesTitle")} italicWord={t("home.facilitiesItalic")} />
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          {facs.map((f, i) => (
            <div key={f.title} className="bg-paper rounded-2xl p-6 border border-ink/5 shadow-paper-sm text-center reveal" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="mx-auto h-12 w-12 rounded-full bg-teal-deep text-mustard-soft flex items-center justify-center mb-3">
                <i className={`fa-solid ${f.icon} text-lg`} aria-hidden="true"></i>
              </div>
              <h3 className="font-display text-lg text-teal-deep">{f.title}</h3>
              <p className="mt-1 text-sm text-teal-deep/70">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="relative bg-mustard rounded-3xl p-8 md:p-12 flex flex-col md:flex-row items-center gap-6 shadow-paper">
          <div className="flex-1">
            <p className="font-script text-3xl text-teal-deep">{pick(site, "promoEyebrow")}</p>
            <h3 className="font-display text-3xl md:text-4xl text-teal-deep italic">{pick(site, "promoTitle")}</h3>
            <p className="mt-2 text-teal-deep/85">{pick(site, "promoBody")}</p>
          </div>
          <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer"
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-teal-deep text-cream px-6 py-3 font-semibold shadow-paper-sm">
            {t("common.bookNow")}
            <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
          </a>
        </div>
      </section>

      <section className="bg-teal-deep text-cream py-24 relative">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading light eyebrow={t("home.galleryEyebrow")} title={t("home.galleryTitle")} italicWord={t("home.galleryItalic")} subtitle={t("home.gallerySub")} />
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
            {gallery.slice(0, 8).map((g, i) => (
              <div key={g.id || i} className={`overflow-hidden rounded-2xl shadow-paper-sm ${i % 3 === 0 ? "aspect-[3/4]" : "aspect-square"}`}>
                <img src={g.src} alt={g.category} className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" loading="lazy" />
              </div>
            ))}
          </div>
          <div className="mt-10 text-center">
            <Link to="/gallery" className="btn-lift inline-flex rounded-full bg-mustard text-teal-deep px-6 py-3 font-semibold shadow-paper-sm">
              {t("common.viewAll")}
            </Link>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24">
        <SectionHeading eyebrow={t("home.exploreEyebrow")} title={t("home.exploreTitle")} italicWord={t("home.exploreItalic")} subtitle={t("home.exploreSub")} />
        <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {attractions.slice(0, 6).map((a, i) => (
            <article key={a.id || a.title} className="group relative rounded-3xl overflow-hidden shadow-paper-sm reveal" style={{ animationDelay: `${i * 80}ms` }}>
              <img src={a.image} alt={pick(a, "title")} className="w-full h-64 object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
              <div className="absolute inset-0 bg-gradient-to-t from-teal-deep/90 via-teal-deep/20 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-5 text-cream">
                <span className="inline-block text-[11px] font-semibold uppercase tracking-widest bg-mustard text-teal-deep rounded-full px-2.5 py-1">{pick(a, "distance")}</span>
                <h3 className="font-display text-2xl mt-2">{pick(a, "title")}</h3>
                <p className="text-sm text-cream/85 mt-1 line-clamp-2">{pick(a, "desc")}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="bg-paper py-24">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading eyebrow={t("home.testimonialsEyebrow")} title={t("home.testimonialsTitle")} italicWord={t("home.testimonialsItalic")} />
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {testimonials.map((tm, i) => (
              <blockquote key={tm.id || i} className="bg-cream rounded-2xl p-6 border border-ink/5 shadow-paper-sm relative reveal" style={{ animationDelay: `${i * 90}ms` }} data-testid={`testimonial-${i}`}>
                <i className="fa-solid fa-quote-left text-mustard-deep text-2xl" aria-hidden="true"></i>
                <p className="mt-3 text-teal-deep/90 leading-relaxed text-sm">{pick(tm, "text")}</p>
                <footer className="mt-4">
                  <p className="font-display text-teal-deep italic">{tm.name}</p>
                  <p className="text-xs text-teal-deep/60">{pick(tm, "origin")}</p>
                </footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24 grid md:grid-cols-2 gap-10 items-center">
        <div>
          <p className="font-script text-3xl text-mustard-deep">{t("home.findEyebrow")}</p>
          <h2 className="font-display text-4xl md:text-5xl text-teal-deep italic">{t("home.findTitle")}</h2>
          <p className="mt-4 text-teal-deep/80 leading-relaxed">{t("home.findBody")}</p>
          <ul className="mt-5 space-y-2 text-teal-deep/85 text-sm">
            <li><i className="fa-solid fa-location-dot text-mustard-deep mr-2" aria-hidden="true"></i>{pick(site, "address")}</li>
            <li><i className="fa-brands fa-whatsapp text-mustard-deep mr-2" aria-hidden="true"></i>{site.whatsappDisplay}</li>
            <li><i className="fa-solid fa-envelope text-mustard-deep mr-2" aria-hidden="true"></i>{site.email}</li>
          </ul>
        </div>
        <div className="rounded-3xl overflow-hidden shadow-paper border border-ink/5">
          <iframe title="Pelangi Homestay Map" src={site.mapEmbed} className="w-full h-80" loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
        </div>
      </section>

      <section className="bg-teal-deep text-cream py-24">
        <div className="max-w-4xl mx-auto px-5 md:px-8">
          <SectionHeading light eyebrow={t("home.faqEyebrow")} title={t("home.faqTitle")} italicWord={t("home.faqItalic")} />
          <Accordion type="single" collapsible className="mt-10">
            {faqs.slice(0, 5).map((f, i) => (
              <AccordionItem key={f.id || i} value={`item-${i}`} className="border-cream/15" data-testid={`faq-item-${i}`}>
                <AccordionTrigger className="text-left text-cream hover:text-mustard-soft font-display text-lg">
                  {pick(f, "q")}
                </AccordionTrigger>
                <AccordionContent className="text-cream/80 leading-relaxed">
                  {pick(f, "a")}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
          <div className="text-center mt-10">
            <Link to="/faq" className="btn-lift inline-flex rounded-full bg-mustard text-teal-deep px-6 py-3 font-semibold shadow-paper-sm">
              {t("common.allQuestions")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
