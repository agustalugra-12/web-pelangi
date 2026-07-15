import { rooms, SITE } from "@/data/content";
import RoomCard from "@/components/site/RoomCard";
import SectionHeading from "@/components/site/SectionHeading";

export default function Rooms() {
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="Rooms" title="Pilih kamar" italicWord="Anda" subtitle="Dua tipe akomodasi, semuanya dirawat dengan hati." />
        <div className="mt-12 grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {rooms.map((r, i) => (
            <RoomCard key={r.slug} room={r} index={i} />
          ))}
        </div>
        <div className="mt-16 bg-paper rounded-3xl p-8 md:p-12 border border-ink/5 shadow-paper-sm">
          <h3 className="font-display text-2xl text-teal-deep">Kebijakan Umum</h3>
          <ul className="mt-4 grid md:grid-cols-2 gap-3 text-sm text-teal-deep/85 list-disc pl-5">
            <li>Check-in mulai 14:00 WITA · Check-out 12:00 WITA</li>
            <li>Extra bed Rp 50.000 / malam termasuk sarapan</li>
            <li>Anak di bawah 6 tahun gratis tanpa extra bed</li>
            <li>Pembatalan gratis hingga 3 hari sebelum check-in</li>
          </ul>
          <a href={SITE.bookingUrl} target="_blank" rel="noopener noreferrer" className="btn-lift inline-flex mt-6 items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm">
            Cek Ketersediaan
            <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
          </a>
        </div>
      </section>
    </div>
  );
}
