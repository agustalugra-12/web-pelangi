import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { DICTIONARY } from "@/i18n/dictionary";
import SectionHeading from "@/components/site/SectionHeading";
import Seo from "@/components/site/Seo";
import Breadcrumb from "@/components/site/Breadcrumb";

const byCat = (arr, c) => arr.find((g) => g.category === c) || arr[0];

// Renders inline `**bold**` markers into <strong>.
function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) => {
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={i}>{p.slice(2, -2)}</strong>;
    return <span key={i}>{p}</span>;
  });
}

export default function About() {
  const { gallery } = useContent();
  const { lang } = useLang();
  const a = DICTIONARY[lang]?.about || DICTIONARY.id.about;

  return (
    <div className="pt-14 pb-24">
      <Seo title={a.seoTitle} description={a.seoDesc} />
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <Breadcrumb items={[{ label: a.breadcrumb }]} />
        <div className="text-center max-w-2xl mx-auto">
          <p className="font-script text-2xl text-mustard-deep">{a.eyebrow}</p>
          <h1 className="font-display font-semibold text-teal-deep text-4xl md:text-5xl lg:text-6xl leading-tight">
            {a.title} <span className="italic text-mustard-deep">{a.titleItalic}</span> {a.titleSuffix}
          </h1>
        </div>

        <div className="mt-14 grid md:grid-cols-2 gap-10 items-center">
          <div className="grid grid-cols-2 gap-3">
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "Lobby").src} alt="Pelangi Homestay" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm mt-8">
              <img src={byCat(gallery, "Restaurant").src} alt="Pelangi Homestay Restaurant" className="w-full h-full object-cover" />
            </div>
          </div>
          <div className="prose-pelangi">
            <h2 className="font-display text-3xl text-teal-deep">{a.storyHeading}</h2>
            {a.story.map((para, i) => (
              <p key={i}>{renderInline(para)}</p>
            ))}
          </div>
        </div>

        {/* Vision & Mission */}
        <div className="mt-16 grid md:grid-cols-2 gap-6">
          <div className="bg-teal-deep text-cream rounded-3xl p-8 shadow-paper-sm">
            <p className="font-script text-2xl text-mustard-soft">{a.visionScript}</p>
            <h3 className="font-display italic text-2xl mt-1">{a.visionTitle}</h3>
            <p className="mt-4 text-cream/85 leading-relaxed">{a.visionBody}</p>
          </div>
          <div className="bg-mustard text-teal-deep rounded-3xl p-8 shadow-paper-sm">
            <p className="font-script text-2xl">{a.missionScript}</p>
            <h3 className="font-display italic text-2xl mt-1">{a.missionTitle}</h3>
            <ul className="mt-4 space-y-1.5 text-teal-deep/90 leading-relaxed list-disc pl-5 text-sm">
              {a.mission.map((li, i) => <li key={i}>{li}</li>)}
            </ul>
          </div>
        </div>

        {/* Why Choose Us */}
        <div className="mt-20">
          <SectionHeading eyebrow={a.whyEyebrow} title={a.whyTitle} italicWord={a.whyItalic} subtitle={a.whySub} />
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {a.whyChooseUs.map((w, i) => (
              <div key={w.title} className="bg-paper rounded-2xl p-6 border border-ink/5 shadow-paper-sm reveal" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="h-12 w-12 rounded-full bg-teal-deep text-mustard-soft flex items-center justify-center mb-3">
                  <i className={`fa-solid ${w.icon} text-lg`} aria-hidden="true"></i>
                </div>
                <h3 className="font-display text-xl text-teal-deep">{w.title}</h3>
                <p className="mt-1 text-sm text-teal-deep/75">{w.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Nilai / Values */}
        <div className="mt-16 grid md:grid-cols-3 gap-5">
          {a.values.map((v, i) => (
            <div key={v.title} className="bg-paper rounded-2xl p-6 border border-ink/5 shadow-paper-sm reveal" style={{ animationDelay: `${i * 80}ms` }}>
              <div className="h-12 w-12 rounded-full bg-teal-deep text-mustard-soft flex items-center justify-center mb-3">
                <i className={`fa-solid ${v.icon} text-lg`} aria-hidden="true"></i>
              </div>
              <h3 className="font-display text-xl text-teal-deep italic">{v.title}</h3>
              <p className="mt-1 text-sm text-teal-deep/75">{v.desc}</p>
            </div>
          ))}
        </div>

        {/* Fact strip */}
        <div className="mt-16 bg-teal-deep text-cream rounded-3xl p-8 md:p-10 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {a.facts.map((f) => (
            <div key={f.label}>
              <p className="font-display text-4xl text-mustard-soft">{f.value}</p>
              <p className="text-xs uppercase tracking-widest mt-1">{f.label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
