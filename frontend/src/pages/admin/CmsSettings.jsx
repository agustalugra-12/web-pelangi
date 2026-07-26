import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { useRefreshContent } from "@/context/ContentContext";
import { DEFAULT_CONTENT } from "@/data/content";
import SiteAssetInput from "@/components/admin/SiteAssetInput";
import { ChevronDown } from "lucide-react";

// Field jarang dipakai/teknis disembunyikan default di balik "Tampilkan Advanced"
// (2026-07-26, permintaan user - berlaku sama untuk semua situs/tenant, bukan cuma
// pelangi) - staf yang cuma perlu ganti kontak/hero/promo tidak perlu lihat field teknis
// seperti SEO meta atau embed URL Maps.
const FIELDS_CONTACT = [
  { key: "brand", label: "Nama Brand", type: "text" },
  { key: "tagline", label: "Tagline", type: "text" },
  { key: "address", label: "Alamat lengkap", type: "text" },
  { key: "whatsappDisplay", label: "WhatsApp (tampilan)", type: "text" },
  { key: "whatsapp", label: "WhatsApp (format wa.me, mis. 6285...)", type: "text" },
  { key: "email", label: "Email", type: "text" },
  { key: "hours", label: "Jam Operasional Reception", type: "text" },
  { key: "bookingUrl", label: "URL Booking Engine (tombol Book Now)", type: "text" },
  { key: "restaurantIntro", label: "Restaurant — Intro", type: "textarea" },
  { key: "restaurantHours", label: "Restaurant — Jam Operasional", type: "text" },
];

const FIELDS_HERO = [
  { key: "heroEyebrow", label: "Hero — Eyebrow (kata pembuka)", type: "text" },
  { key: "heroTitle", label: "Hero — Judul (mis. 'Bedugul')", type: "text" },
  { key: "heroSubtitle", label: "Hero — Sub-judul (mis. 'Tenang. Hangat.')", type: "text" },
  { key: "heroBody", label: "Hero — Isi paragraf", type: "textarea" },
];

const FIELDS_PROMO = [
  { key: "promoEyebrow", label: "Promo — Eyebrow", type: "text" },
  { key: "promoTitle", label: "Promo — Judul", type: "text" },
  { key: "promoBody", label: "Promo — Isi", type: "textarea" },
];

const FIELDS_ADVANCED = [
  { key: "mapEmbed", label: "Google Maps embed URL", type: "textarea" },
  { key: "seoTitle", label: "SEO — Meta Title", type: "text" },
  { key: "seoDescription", label: "SEO — Meta Description", type: "textarea" },
];

function FieldList({ fields, data, setData }) {
  return (
    <>
      {fields.map((f) => (
        <label key={f.key} className="block">
          <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{f.label}</span>
          {f.type === "textarea" ? (
            <textarea rows={3} value={data[f.key] || ""} onChange={(e) => setData({ ...data, [f.key]: e.target.value })}
              data-testid={`settings-${f.key}`}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-2.5 outline-none focus:border-teal resize-y text-sm" />
          ) : (
            <input type="text" value={data[f.key] || ""} onChange={(e) => setData({ ...data, [f.key]: e.target.value })}
              data-testid={`settings-${f.key}`}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-2.5 outline-none focus:border-teal text-sm" />
          )}
        </label>
      ))}
    </>
  );
}

export default function CmsSettings() {
  const refresh = useRefreshContent();
  const [data, setData] = useState(DEFAULT_CONTENT.site);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    api.get("/content/site")
      .then(({ data }) => setData({ ...DEFAULT_CONTENT.site, ...(data || {}) }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/admin/content/site", { data });
      await refresh?.();
      // update document title live
      if (data.seoTitle) document.title = data.seoTitle;
      toast.success("Pengaturan disimpan");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-teal-deep/70">Memuat…</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-end justify-between gap-4 mb-6 flex-wrap">
        <div>
          <p className="font-script text-2xl text-mustard-deep">Pengaturan</p>
          <h1 className="font-display text-3xl md:text-4xl text-teal-deep italic">Situs & Kontak.</h1>
          <p className="text-sm text-teal-deep/70 mt-1">Semua teks brand, hero, promo, kontak, dan SEO.</p>
        </div>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          data-testid="cms-settings-save"
          className="btn-lift rounded-full bg-leaf text-white px-6 py-2.5 font-semibold shadow-paper-sm disabled:opacity-60"
        >
          {saving ? "Menyimpan…" : "Simpan Pengaturan"}
        </button>
      </div>

      <div className="bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-6 space-y-4">
        <FieldList fields={FIELDS_CONTACT} data={data} setData={setData} />
      </div>

      <div className="bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-6 space-y-4 mt-6">
        <SiteAssetInput
          slot="hero"
          previewUrl="/assets/signage.webp"
          label="Foto Hero (halaman utama)"
          hint="Otomatis diresize & dikompres. Butuh beberapa detik sampai tampil di situs live."
          testid="settings-hero-photo-upload"
        />
        <FieldList fields={FIELDS_HERO} data={data} setData={setData} />
      </div>

      <div className="bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-6 space-y-4 mt-6">
        <FieldList fields={FIELDS_PROMO} data={data} setData={setData} />
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced((v) => !v)}
        data-testid="settings-toggle-advanced"
        className="mt-6 flex items-center gap-2 text-sm font-semibold text-teal-deep/70 hover:text-teal-deep"
      >
        <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`} />
        {showAdvanced ? "Sembunyikan Advanced" : "Tampilkan Advanced"}
      </button>

      {showAdvanced && (
        <div className="bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-6 space-y-4 mt-3">
          <SiteAssetInput
            slot="favicon"
            previewUrl="/assets/pelangi-logo.png"
            label="Logo / Favicon"
            hint="Dipakai untuk logo di Navbar & ikon tab browser. Otomatis dijadikan persegi 128x128."
            testid="settings-favicon-upload"
          />
          <FieldList fields={FIELDS_ADVANCED} data={data} setData={setData} />
        </div>
      )}
    </div>
  );
}
