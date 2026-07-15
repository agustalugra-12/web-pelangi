import { useState } from "react";
import SectionHeading from "@/components/site/SectionHeading";
import { useContent } from "@/context/ContentContext";
import { CONTACT } from "@/constants/testIds";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";

export default function Contact() {
  const { site } = useContent();
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/contact", form);
      toast.success("Terima kasih! Tim kami akan segera menghubungi Anda.");
      setForm({ name: "", email: "", subject: "", message: "" });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="Contact" title="Sapa" italicWord="kami" subtitle="Punya pertanyaan atau permintaan khusus? Tim kami dengan senang hati membantu." />

        <div className="mt-12 grid md:grid-cols-5 gap-8">
          <div className="md:col-span-2 space-y-4">
            <div className="bg-teal-deep text-cream rounded-2xl p-6">
              <p className="font-script text-2xl text-mustard-soft">Kunjungi</p>
              <h3 className="font-display text-xl italic">Alamat</h3>
              <p className="mt-2 text-cream/85 text-sm">{site.address}</p>
            </div>
            <div className="bg-mustard text-teal-deep rounded-2xl p-6">
              <p className="font-script text-2xl">Chat</p>
              <h3 className="font-display text-xl italic">WhatsApp</h3>
              <a href={`https://wa.me/${site.whatsapp}`} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-teal-deep font-semibold underline underline-offset-4">
                {site.whatsappDisplay}
              </a>
            </div>
            <div className="bg-paper text-teal-deep rounded-2xl p-6 border border-ink/5">
              <p className="font-script text-2xl text-mustard-deep">Email</p>
              <h3 className="font-display text-xl italic">Kirim pesan</h3>
              <a href={`mailto:${site.email}`} className="mt-2 inline-block font-semibold underline underline-offset-4">
                {site.email}
              </a>
              <p className="mt-3 text-sm text-teal-deep/70"><i className="fa-regular fa-clock mr-1" aria-hidden="true"></i>{site.hours}</p>
            </div>
          </div>

          <form onSubmit={submit} className="md:col-span-3 bg-paper rounded-3xl p-6 md:p-8 border border-ink/5 shadow-paper-sm space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <label className="block">
                <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Nama</span>
                <input data-testid={CONTACT.name} required name="name" value={form.name} onChange={handleChange}
                  className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal" />
              </label>
              <label className="block">
                <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Email</span>
                <input data-testid={CONTACT.email} required type="email" name="email" value={form.email} onChange={handleChange}
                  className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal" />
              </label>
            </div>
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Subjek</span>
              <input name="subject" value={form.subject} onChange={handleChange}
                className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal" />
            </label>
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Pesan</span>
              <textarea data-testid={CONTACT.message} required name="message" value={form.message} onChange={handleChange} rows={6}
                className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal resize-none" />
            </label>
            <button type="submit" data-testid={CONTACT.submit} disabled={loading}
              className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm disabled:opacity-60">
              {loading ? "Mengirim…" : "Kirim Pesan"}
              <i className="fa-solid fa-paper-plane text-xs" aria-hidden="true"></i>
            </button>
          </form>
        </div>

        <div className="mt-12 rounded-3xl overflow-hidden shadow-paper border border-ink/5">
          <iframe title="Map" src={site.mapEmbed} className="w-full h-96" loading="lazy" />
        </div>
      </section>
    </div>
  );
}
