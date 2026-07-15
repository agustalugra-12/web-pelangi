import { useContent } from "@/context/ContentContext";
import SectionHeading from "@/components/site/SectionHeading";

const byCat = (arr, c) => arr.find((g) => g.category === c) || arr[0];

const values = [
  { icon: "fa-hand-holding-heart", title: "Tulus", desc: "Kami melayani seperti menerima keluarga sendiri." },
  { icon: "fa-leaf", title: "Lestari", desc: "Menggunakan produk lokal dan meminimalkan jejak plastik." },
  { icon: "fa-mug-hot", title: "Hangat", desc: "Setiap sudut dirancang untuk pagi yang lambat dan tenang." },
];

export default function About() {
  const { gallery } = useContent();
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="About" title="Rumah kecil" italicWord="di Bedugul" />

        <div className="mt-12 grid md:grid-cols-2 gap-10 items-center">
          <div className="grid grid-cols-2 gap-3">
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm">
              <img src={byCat(gallery, "View").src} alt="View" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-[3/4] rounded-3xl overflow-hidden shadow-paper-sm mt-8">
              <img src={byCat(gallery, "Restaurant").src} alt="Restaurant" className="w-full h-full object-cover" />
            </div>
          </div>
          <div>
            <p className="text-teal-deep/85 leading-relaxed">
              Pelangi Homestay lahir dari cinta sederhana pada Bedugul — kabut pagi, suara jangkrik, dan cangkir kopi yang mengepul. Kami adalah keluarga kecil yang ingin membagikan ketenangan itu kepada tamu-tamu kami.
            </p>
            <p className="mt-4 text-teal-deep/85 leading-relaxed">
              Setiap kamar kami rawat dengan hati. Setiap breakfast kami masak dengan bahan lokal. Kami tidak menjanjikan kemewahan, tetapi kami menjanjikan pengalaman menginap yang membuat Anda ingin kembali.
            </p>

            <div className="mt-8 grid grid-cols-2 gap-4">
              <div className="bg-teal-deep text-cream rounded-2xl p-5">
                <p className="font-script text-xl text-mustard-soft">Visi</p>
                <p className="mt-1 text-sm leading-relaxed">Menjadi rumah kedua yang paling dirindukan di dataran tinggi Bali.</p>
              </div>
              <div className="bg-mustard text-teal-deep rounded-2xl p-5">
                <p className="font-script text-xl">Misi</p>
                <p className="mt-1 text-sm leading-relaxed">Melayani dengan tulus, merawat alam, dan memberdayakan komunitas Bedugul.</p>
              </div>
            </div>
          </div>
        </div>

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
      </section>
    </div>
  );
}
