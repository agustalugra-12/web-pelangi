import { useContent } from "@/context/ContentContext";
import SectionHeading from "@/components/site/SectionHeading";
import Seo from "@/components/site/Seo";
import Breadcrumb from "@/components/site/Breadcrumb";

const byCat = (arr, c) => arr.find((g) => g.category === c) || arr[0];

const values = [
  { icon: "fa-hand-holding-heart", title: "Tulus", desc: "Kami melayani seperti menerima keluarga sendiri." },
  { icon: "fa-leaf", title: "Lestari", desc: "Menggunakan produk lokal dan meminimalkan jejak plastik." },
  { icon: "fa-mug-hot", title: "Hangat", desc: "Setiap sudut dirancang untuk pagi yang lambat dan tenang." },
];

const whyChooseUs = [
  { icon: "fa-bed", title: "18 Kamar Nyaman", desc: "10 Standard Room + 8 Cottage — semua dengan air panas, WiFi, dan Smart TV." },
  { icon: "fa-map-location-dot", title: "Lokasi Strategis", desc: "5 menit dari Pura Ulun Danu, 8 menit ke Kebun Raya Bali." },
  { icon: "fa-users", title: "Ramah Keluarga", desc: "Kapasitas 2 dewasa + 1 anak, taman aman untuk anak-anak." },
  { icon: "fa-wifi", title: "WiFi Gratis", desc: "Fiber optic di seluruh area, cocok untuk work-from-Bali." },
  { icon: "fa-utensils", title: "Sarapan Termasuk", desc: "Menu hangat khas dataran tinggi untuk mulai hari." },
  { icon: "fa-car", title: "Parkir Pribadi", desc: "Area parkir luas dan aman untuk mobil maupun motor." },
];

export default function About() {
  const { gallery } = useContent();
  return (
    <div className="pt-14 pb-24">
      <Seo
        title="Tentang Kami"
        description="Pelangi Homestay Bedugul — penginapan keluarga sejak 2012 dengan 18 kamar (10 Standard + 8 Cottage) di jantung dataran tinggi Bali."
      />
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <Breadcrumb items={[{ label: "Tentang Kami" }]} />
        <div className="text-center max-w-2xl mx-auto">
          <p className="font-script text-2xl text-mustard-deep">Tentang Kami</p>
          <h1 className="font-display font-semibold text-teal-deep text-4xl md:text-5xl lg:text-6xl leading-tight">
            Rumah <span className="italic text-mustard-deep">Hangat</span> di Jantung Bedugul sejak 2012.
          </h1>
        </div>

        <div className="mt-14 grid md:grid-cols-2 gap-10 items-center">
          <div className="grid grid-cols-2 gap-3">
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "Lobby").src} alt="Fasad Pelangi Homestay" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm mt-8">
              <img src={byCat(gallery, "Restaurant").src} alt="Ruang makan Pelangi Homestay" className="w-full h-full object-cover" />
            </div>
          </div>
          <div className="prose-pelangi">
            <h2 className="font-display text-3xl text-teal-deep">Cerita Kami</h2>
            <p>
              Pelangi Homestay didirikan pada tahun <strong>2012</strong> sebagai penginapan keluarga di kawasan Bedugul, Kecamatan Baturiti, Kabupaten Tabanan, Bali. Berawal dari beberapa kamar sederhana untuk wisatawan domestik, kami terus berkembang dengan mengutamakan pelayanan yang ramah, kebersihan, dan kenyamanan.
            </p>
            <p>
              Saat ini kami memiliki <strong>18 kamar aktif</strong> — terdiri dari <strong>10 Standard Room</strong> dan <strong>8 Cottage Room</strong> — yang dirancang untuk memberikan pengalaman menginap yang nyaman bagi pasangan, keluarga, maupun wisatawan yang ingin menikmati suasana sejuk Bedugul.
            </p>
            <p>
              Kami percaya bahwa pengalaman menginap terbaik bukan hanya tentang kamar, tetapi juga tentang keramahan, ketenangan, serta kemudahan menjelajahi destinasi wisata di sekitar Bedugul.
            </p>
          </div>
        </div>

        {/* Vision & Mission */}
        <div className="mt-16 grid md:grid-cols-2 gap-6">
          <div className="bg-teal-deep text-cream rounded-3xl p-8 shadow-paper-sm">
            <p className="font-script text-2xl text-mustard-soft">Visi</p>
            <h3 className="font-display italic text-2xl mt-1">Rumah kedua yang terpercaya.</h3>
            <p className="mt-4 text-cream/85 leading-relaxed">
              Menjadi pilihan penginapan terpercaya di Bedugul dengan pelayanan yang hangat dan pengalaman menginap yang berkesan.
            </p>
          </div>
          <div className="bg-mustard text-teal-deep rounded-3xl p-8 shadow-paper-sm">
            <p className="font-script text-2xl">Misi</p>
            <h3 className="font-display italic text-2xl mt-1">Melayani dengan tulus.</h3>
            <ul className="mt-4 space-y-1.5 text-teal-deep/90 leading-relaxed list-disc pl-5 text-sm">
              <li>Memberikan pelayanan terbaik.</li>
              <li>Menjaga kebersihan dan kenyamanan seluruh area.</li>
              <li>Mendukung pariwisata dan komunitas lokal Bedugul.</li>
              <li>Menyediakan pengalaman menginap yang nyaman dan berkesan.</li>
            </ul>
          </div>
        </div>

        {/* Why Choose Us */}
        <div className="mt-20">
          <SectionHeading eyebrow="Why choose us" title="Kenapa memilih" italicWord="Pelangi?" subtitle="Beberapa alasan tamu kembali menginap di rumah kecil kami." />
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {whyChooseUs.map((w, i) => (
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
          {values.map((v, i) => (
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
          <div><p className="font-display text-4xl text-mustard-soft">2012</p><p className="text-xs uppercase tracking-widest mt-1">Berdiri</p></div>
          <div><p className="font-display text-4xl text-mustard-soft">18</p><p className="text-xs uppercase tracking-widest mt-1">Total Kamar</p></div>
          <div><p className="font-display text-4xl text-mustard-soft">10 + 8</p><p className="text-xs uppercase tracking-widest mt-1">Standard + Cottage</p></div>
          <div><p className="font-display text-4xl text-mustard-soft">10+</p><p className="text-xs uppercase tracking-widest mt-1">Tahun Melayani</p></div>
        </div>
      </section>
    </div>
  );
}
