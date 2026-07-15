import { Link } from "react-router-dom";
import { SITE, rooms, facilities, attractions, testimonials, faqs, galleryItems, galleryByCategory } from "@/data/content";
import RoomCard from "@/components/site/RoomCard";
import SectionHeading from "@/components/site/SectionHeading";
import { HOME } from "@/constants/testIds";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function Home() {
  return (
    <div>
      {/* HERO */}
      <section
        data-testid={HOME.hero}
        className="relative overflow-hidden pt-8 pb-24 md:pb-32"
      >
        <div className="max-w-7xl mx-auto px-5 md:px-8 grid lg:grid-cols-12 gap-10 items-center">
          {/* LEFT: teal torn panel */}
          <div className="lg:col-span-7 relative">
            <div className="relative bg-teal-deep text-cream rounded-[36px] p-8 md:p-12 shadow-paper overflow-hidden">
              {/* airplane doodle */}
              <svg viewBox="0 0 400 120" className="absolute top-4 right-4 w-40 h-12 text-mustard-soft opacity-80">
                <path d="M10 100 Q120 20 260 40 T390 30" stroke="currentColor" strokeWidth="2" fill="none" className="doodle-dash" />
                <path d="M380 20 L400 30 L378 42 L385 30 Z" fill="currentColor" />
              </svg>

              <p className="font-script text-3xl md:text-4xl text-mustard-soft mb-1">Discover</p>
              <h1 className="font-display font-semibold text-5xl md:text-6xl lg:text-7xl leading-[0.95]">
                Bedugul<span className="text-mustard-soft">.</span>
                <br />
                <span className="italic font-light">Tenang.</span> Hangat.
              </h1>
              <p className="mt-5 max-w-md text-cream/85 text-base md:text-lg leading-relaxed">
                Rumah kedua Anda di dataran tinggi Bali. Kabut pagi, kopi lokal, dan
                pelayanan tulus dari keluarga Pelangi.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a
                  href={SITE.bookingUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid={HOME.bookNowBtn}
                  className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-7 py-3.5 font-semibold shadow-paper-sm"
                >
                  Book Now
                  <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
                </a>
                <Link
                  to="/rooms"
                  className="btn-lift inline-flex items-center gap-2 rounded-full border-2 border-mustard-soft text-mustard-soft px-6 py-3 font-semibold hover:bg-mustard-soft hover:text-teal-deep"
                >
                  Lihat Kamar
                </Link>
              </div>

              {/* Ripped bottom edge inside panel */}
              <svg viewBox="0 0 800 40" preserveAspectRatio="none" className="absolute -bottom-1 left-0 right-0 w-full h-8">
                <path d="M0 40 C60 20 100 34 160 22 C220 10 260 30 320 20 C380 10 420 32 480 22 C540 12 580 30 640 22 C700 12 740 30 800 20 V40 Z" fill="#F7F3EA"/>
              </svg>
            </div>
          </div>

          {/* RIGHT: images */}
          <div className="lg:col-span-5 relative">
            <div className="relative">
              <div className="blob overflow-hidden shadow-paper w-full aspect-[4/5] max-w-sm mx-auto">
                <img src={rooms[1].image} alt="Cottage Pelangi" className="w-full h-full object-cover" />
              </div>
              <div className="absolute -bottom-8 -left-6 w-40 h-40 rounded-full overflow-hidden shadow-paper border-4 border-cream hidden md:block">
                <img src={attractions[0].image} alt="Pura Ulun Danu" className="w-full h-full object-cover" />
              </div>
              <div className="absolute -top-6 -right-4 w-28 h-28 rounded-full overflow-hidden shadow-paper border-4 border-cream hidden md:block">
                <img src={attractions[2].image} alt="Danau Beratan" className="w-full h-full object-cover" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ABOUT STRIP */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="grid md:grid-cols-2 gap-10 items-center">
          <div>
            <p className="font-script text-3xl text-mustard-deep">Tentang kami</p>
            <h2 className="font-display text-4xl md:text-5xl text-teal-deep leading-tight mt-1">
              Rumah <span className="italic text-mustard-deep">hangat</span> untuk perjalanan tenang.
            </h2>
            <p className="mt-4 text-teal-deep/80 leading-relaxed">
              Pelangi Homestay adalah keluarga kecil di Bedugul. Kami percaya liburan
              terbaik bukan tentang kemewahan, melainkan tentang kopi yang mengepul,
              percakapan yang tulus, dan pagi yang tak terburu-buru.
            </p>
            <Link to="/about" className="btn-lift inline-flex mt-6 items-center gap-2 rounded-full border-2 border-teal text-teal-deep px-5 py-2.5 font-semibold hover:bg-teal-deep hover:text-cream">
              Cerita Kami
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 aspect-[4/3] rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory("Garden").src} alt="Garden" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory("Restaurant").src} alt="Restaurant" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-square rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={galleryByCategory("View").src} alt="View" className="w-full h-full object-cover" />
            </div>
            <div className="col-span-2 aspect-[4/3] rounded-2xl overflow-hidden shadow-paper-sm">
              <img src={rooms[0].image} alt="Room" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      </section>

      {/* ROOMS */}
      <section className="bg-paper py-20">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading eyebrow="Pilihan Kamar" title="Tempat" italicWord="beristirahat" subtitle="Tiga tipe akomodasi, masing-masing dengan karakternya sendiri." />
          <div className="mt-12 grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {rooms.map((r, i) => (
              <RoomCard key={r.slug} room={r} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* FACILITIES */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24">
        <SectionHeading eyebrow="Fasilitas" title="Kenyamanan yang" italicWord="menemani" />
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          {facilities.map((f, i) => (
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

      {/* PROMO STRIP */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="relative bg-mustard rounded-3xl p-8 md:p-12 flex flex-col md:flex-row items-center gap-6 shadow-paper">
          <div className="flex-1">
            <p className="font-script text-3xl text-teal-deep">Special offer</p>
            <h3 className="font-display text-3xl md:text-4xl text-teal-deep italic">Menginap 10 malam, gratis 1 malam.</h3>
            <p className="mt-2 text-teal-deep/85">Berlaku untuk pemesanan langsung melalui website resmi. Berlaku akumulatif — kumpulkan malam Anda.</p>
          </div>
          <a
            href={SITE.bookingUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-teal-deep text-cream px-6 py-3 font-semibold shadow-paper-sm"
          >
            Book Now
            <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
          </a>
        </div>
      </section>

      {/* GALLERY PREVIEW */}
      <section className="bg-teal-deep text-cream py-24 relative">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading light eyebrow="Galeri" title="Sudut" italicWord="favorit" subtitle="Sekilas suasana Pelangi Homestay dan Bedugul di sekitarnya." />
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
            {galleryItems.slice(0, 8).map((g, i) => (
              <div key={i} className={`overflow-hidden rounded-2xl shadow-paper-sm ${i % 3 === 0 ? "aspect-[3/4]" : "aspect-square"}`}>
                <img src={g.src} alt={g.category} className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" />
              </div>
            ))}
          </div>
          <div className="mt-10 text-center">
            <Link to="/gallery" className="btn-lift inline-flex rounded-full bg-mustard text-teal-deep px-6 py-3 font-semibold shadow-paper-sm">
              Lihat Semua
            </Link>
          </div>
        </div>
      </section>

      {/* EXPLORE BEDUGUL */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24">
        <SectionHeading eyebrow="Explore" title="Jelajahi" italicWord="Bedugul" subtitle="Tempat-tempat favorit yang bisa dicapai dalam hitungan menit dari kamar Anda." />
        <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {attractions.slice(0, 6).map((a, i) => (
            <article key={a.title} className="group relative rounded-3xl overflow-hidden shadow-paper-sm reveal" style={{ animationDelay: `${i * 80}ms` }}>
              <img src={a.image} alt={a.title} className="w-full h-64 object-cover group-hover:scale-105 transition-transform duration-500" />
              <div className="absolute inset-0 bg-gradient-to-t from-teal-deep/90 via-teal-deep/20 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-5 text-cream">
                <span className="inline-block text-[11px] font-semibold uppercase tracking-widest bg-mustard text-teal-deep rounded-full px-2.5 py-1">{a.distance}</span>
                <h3 className="font-display text-2xl mt-2">{a.title}</h3>
                <p className="text-sm text-cream/85 mt-1 line-clamp-2">{a.desc}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="bg-paper py-24">
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <SectionHeading eyebrow="Kata Tamu" title="Cerita" italicWord="mereka" />
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {testimonials.map((t, i) => (
              <blockquote key={t.name} className="bg-cream rounded-2xl p-6 border border-ink/5 shadow-paper-sm relative reveal" style={{ animationDelay: `${i * 90}ms` }} data-testid={`testimonial-${i}`}>
                <i className="fa-solid fa-quote-left text-mustard-deep text-2xl" aria-hidden="true"></i>
                <p className="mt-3 text-teal-deep/90 leading-relaxed text-sm">{t.text}</p>
                <footer className="mt-4">
                  <p className="font-display text-teal-deep italic">{t.name}</p>
                  <p className="text-xs text-teal-deep/60">{t.origin}</p>
                </footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      {/* LOCATION */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24 grid md:grid-cols-2 gap-10 items-center">
        <div>
          <p className="font-script text-3xl text-mustard-deep">Temukan kami</p>
          <h2 className="font-display text-4xl md:text-5xl text-teal-deep italic">Di jantung Bedugul.</h2>
          <p className="mt-4 text-teal-deep/80 leading-relaxed">
            5 menit dari Pura Ulun Danu Beratan, 8 menit ke Kebun Raya Bali. Akses mudah lewat jalur utama Denpasar–Singaraja.
          </p>
          <ul className="mt-5 space-y-2 text-teal-deep/85 text-sm">
            <li><i className="fa-solid fa-location-dot text-mustard-deep mr-2" aria-hidden="true"></i>{SITE.address}</li>
            <li><i className="fa-brands fa-whatsapp text-mustard-deep mr-2" aria-hidden="true"></i>{SITE.whatsappDisplay}</li>
            <li><i className="fa-solid fa-envelope text-mustard-deep mr-2" aria-hidden="true"></i>{SITE.email}</li>
          </ul>
        </div>
        <div className="rounded-3xl overflow-hidden shadow-paper border border-ink/5">
          <iframe
            title="Pelangi Homestay Map"
            src={SITE.mapEmbed}
            className="w-full h-80"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-teal-deep text-cream py-24">
        <div className="max-w-4xl mx-auto px-5 md:px-8">
          <SectionHeading light eyebrow="FAQ" title="Pertanyaan" italicWord="sering ditanya" />
          <Accordion type="single" collapsible className="mt-10">
            {faqs.slice(0, 5).map((f, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="border-cream/15" data-testid={`faq-item-${i}`}>
                <AccordionTrigger className="text-left text-cream hover:text-mustard-soft font-display text-lg">
                  {f.q}
                </AccordionTrigger>
                <AccordionContent className="text-cream/80 leading-relaxed">
                  {f.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
          <div className="text-center mt-10">
            <Link to="/faq" className="btn-lift inline-flex rounded-full bg-mustard text-teal-deep px-6 py-3 font-semibold shadow-paper-sm">
              Semua Pertanyaan
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
