import { restaurant, galleryItems, SITE } from "@/data/content";
import SectionHeading from "@/components/site/SectionHeading";

export default function Restaurant() {
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="Restaurant" title="Cerita rasa" italicWord="Bedugul" subtitle={restaurant.intro} />

        <div className="mt-12 grid md:grid-cols-5 gap-6 items-start">
          <div className="md:col-span-3 grid grid-cols-2 gap-3">
            <div className="col-span-2 aspect-[16/9] rounded-3xl overflow-hidden shadow-paper-sm">
              <img src={galleryItems[6].src} alt="Restaurant" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryItems[7].src} alt="Garden" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryItems[11].src} alt="Corner" className="w-full h-full object-cover" />
            </div>
          </div>

          <div className="md:col-span-2 bg-paper rounded-3xl p-6 shadow-paper-sm border border-ink/5">
            <p className="font-script text-2xl text-mustard-deep">Menu</p>
            <h3 className="font-display text-2xl text-teal-deep italic">Favorit tamu</h3>
            <ul className="mt-4 divide-y divide-ink/10">
              {restaurant.menu.map((m) => (
                <li key={m.name} className="py-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="font-semibold text-teal-deep">{m.name}</p>
                    <p className="font-display italic text-mustard-deep">{m.price}</p>
                  </div>
                  <p className="text-sm text-teal-deep/75">{m.desc}</p>
                </li>
              ))}
            </ul>
            <p className="mt-5 text-sm text-teal-deep/75">
              Jam operasional <span className="font-semibold text-teal-deep">{restaurant.hours}</span>
            </p>
            <a
              href={`https://wa.me/${SITE.whatsapp}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-lift inline-flex mt-4 rounded-full bg-leaf text-white px-5 py-2.5 text-sm font-semibold shadow-paper-sm"
            >
              Reservasi Meja
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
