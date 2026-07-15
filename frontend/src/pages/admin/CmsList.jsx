// Generic array-content editor used for Rooms, Menu, Gallery, Attractions, FAQ, Testimoni.
// Each section describes its fields via SECTION_SCHEMAS below.
import { useEffect, useMemo, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { useRefreshContent } from "@/context/ContentContext";
import { DEFAULT_CONTENT } from "@/data/content";
import ImageInput from "@/components/admin/ImageInput";

const uid = () => Math.random().toString(36).slice(2, 10);

const SECTION_SCHEMAS = {
  rooms: {
    title: "Rooms",
    subtitle: "Kelola tipe kamar, harga, foto & fasilitas.",
    itemLabel: (r) => r.name || r.slug || "Kamar",
    newItem: () => ({ id: uid(), slug: "new-room", name: "Kamar Baru", capacity: "2 Dewasa + 1 Anak", size: "3 × 3 m", priceFrom: "IDR 175.000", image: "", gallery: [], facilities: ["Double Bed","WiFi","Breakfast"], description: "" }),
    fields: [
      { key: "name", label: "Nama", type: "text" },
      { key: "slug", label: "Slug (URL)", type: "text" },
      { key: "capacity", label: "Kapasitas", type: "text" },
      { key: "size", label: "Ukuran", type: "text" },
      { key: "priceFrom", label: "Harga mulai", type: "text" },
      { key: "image", label: "Foto Utama", type: "image" },
      { key: "gallery", label: "Foto Tambahan (satu URL per baris)", type: "list" },
      { key: "facilities", label: "Fasilitas (satu per baris)", type: "list" },
      { key: "description", label: "Deskripsi", type: "textarea" },
    ],
  },
  menu: {
    title: "Menu Restaurant",
    subtitle: "Item menu, deskripsi, dan harga.",
    itemLabel: (m) => m.name || "Menu",
    newItem: () => ({ id: uid(), name: "Menu Baru", desc: "", price: "IDR 15k" }),
    fields: [
      { key: "name", label: "Nama Menu", type: "text" },
      { key: "desc", label: "Deskripsi", type: "textarea" },
      { key: "price", label: "Harga", type: "text" },
    ],
  },
  gallery: {
    title: "Gallery",
    subtitle: "Foto galeri dengan kategori.",
    itemLabel: (g) => `${g.category || "-"} · ${g.src?.split("/").pop() || ""}`,
    newItem: () => ({ id: uid(), category: "Standard Room", src: "" }),
    fields: [
      { key: "category", label: "Kategori", type: "select", options: ["Standard Room","Cottage","Bathroom","Restaurant","Garden","View","Lobby"] },
      { key: "src", label: "Foto", type: "image" },
    ],
  },
  attractions: {
    title: "Explore Bedugul",
    subtitle: "Destinasi wisata sekitar homestay.",
    itemLabel: (a) => a.title || "Destinasi",
    newItem: () => ({ id: uid(), title: "Tempat Baru", distance: "10 menit", image: "", desc: "" }),
    fields: [
      { key: "title", label: "Nama Destinasi", type: "text" },
      { key: "distance", label: "Jarak (mis. '5 menit')", type: "text" },
      { key: "image", label: "Foto", type: "image" },
      { key: "desc", label: "Deskripsi", type: "textarea" },
    ],
  },
  faqs: {
    title: "FAQ",
    subtitle: "Pertanyaan yang sering ditanyakan tamu.",
    itemLabel: (f) => f.q || "Pertanyaan",
    newItem: () => ({ id: uid(), q: "Pertanyaan?", a: "Jawaban." }),
    fields: [
      { key: "q", label: "Pertanyaan", type: "text" },
      { key: "a", label: "Jawaban", type: "textarea" },
    ],
  },
  testimonials: {
    title: "Testimoni",
    subtitle: "Ulasan tamu untuk ditampilkan di beranda.",
    itemLabel: (t) => `${t.name || "-"} · ${t.origin || "-"}`,
    newItem: () => ({ id: uid(), name: "Nama Tamu", origin: "Asal", text: "" }),
    fields: [
      { key: "name", label: "Nama", type: "text" },
      { key: "origin", label: "Asal", type: "text" },
      { key: "text", label: "Testimoni", type: "textarea" },
    ],
  },
};

export default function CmsList({ section }) {
  const schema = SECTION_SCHEMAS[section];
  const refresh = useRefreshContent();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [openId, setOpenId] = useState(null);

  useEffect(() => {
    setLoading(true);
    api.get(`/content/${section}`)
      .then(({ data }) => setItems(Array.isArray(data) ? data : (DEFAULT_CONTENT[section] || [])))
      .catch(() => setItems(DEFAULT_CONTENT[section] || []))
      .finally(() => setLoading(false));
  }, [section]);

  const setItem = (id, patch) => setItems((arr) => arr.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const addItem = () => {
    const it = schema.newItem();
    setItems((arr) => [it, ...arr]);
    setOpenId(it.id);
  };
  const removeItem = (id) => {
    if (!window.confirm("Hapus item ini?")) return;
    setItems((arr) => arr.filter((x) => x.id !== id));
  };
  const moveItem = (idx, dir) => {
    setItems((arr) => {
      const next = [...arr];
      const target = idx + dir;
      if (target < 0 || target >= next.length) return next;
      [next[idx], next[target]] = [next[target], next[idx]];
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.put(`/admin/content/${section}`, { data: items });
      await refresh?.();
      toast.success("Perubahan disimpan");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!schema) return <p>Section tidak ditemukan.</p>;
  if (loading) return <p className="text-teal-deep/70">Memuat…</p>;

  return (
    <div className="max-w-4xl">
      <div className="flex items-end justify-between gap-4 mb-6 flex-wrap">
        <div>
          <p className="font-script text-2xl text-mustard-deep">Kelola</p>
          <h1 className="font-display text-3xl md:text-4xl text-teal-deep italic">{schema.title}.</h1>
          <p className="text-sm text-teal-deep/70 mt-1">{schema.subtitle}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={addItem}
            data-testid="cms-add-item"
            className="btn-lift inline-flex items-center gap-2 rounded-full border-2 border-teal-deep text-teal-deep px-4 py-2 text-sm font-semibold hover:bg-teal-deep hover:text-cream"
          >
            <i className="fa-solid fa-plus text-xs" aria-hidden="true"></i>
            Tambah
          </button>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            data-testid="cms-save"
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-5 py-2 text-sm font-semibold shadow-paper-sm disabled:opacity-60"
          >
            {saving ? "Menyimpan…" : "Simpan"}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item, idx) => (
          <div key={item.id} className="bg-paper rounded-2xl border border-ink/10 shadow-paper-sm">
            <div className="p-4 flex items-center justify-between gap-3">
              <button
                type="button"
                className="flex-1 text-left"
                onClick={() => setOpenId(openId === item.id ? null : item.id)}
                data-testid={`cms-item-toggle-${item.id}`}
              >
                <p className="text-xs uppercase tracking-widest text-mustard-deep">#{idx + 1}</p>
                <p className="font-display text-lg text-teal-deep">{schema.itemLabel(item)}</p>
              </button>
              <div className="flex items-center gap-1">
                <button type="button" onClick={() => moveItem(idx, -1)} className="w-8 h-8 rounded-full hover:bg-teal-deep/10" title="Naik">
                  <i className="fa-solid fa-arrow-up text-xs text-teal-deep" aria-hidden="true"></i>
                </button>
                <button type="button" onClick={() => moveItem(idx, 1)} className="w-8 h-8 rounded-full hover:bg-teal-deep/10" title="Turun">
                  <i className="fa-solid fa-arrow-down text-xs text-teal-deep" aria-hidden="true"></i>
                </button>
                <button type="button" onClick={() => removeItem(item.id)} className="w-8 h-8 rounded-full hover:bg-red-100" title="Hapus" data-testid={`cms-delete-${item.id}`}>
                  <i className="fa-solid fa-trash text-xs text-red-600" aria-hidden="true"></i>
                </button>
              </div>
            </div>

            {openId === item.id && (
              <div className="border-t border-ink/10 p-4 space-y-3">
                {schema.fields.map((f) => (
                  <FieldRow key={f.key} field={f} value={item[f.key]} onChange={(v) => setItem(item.id, { [f.key]: v })} />
                ))}
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-teal-deep/70 text-center py-10">Belum ada data. Klik <b>Tambah</b>.</p>
        )}
      </div>
    </div>
  );
}

function FieldRow({ field, value, onChange }) {
  if (field.type === "image") {
    return <ImageInput label={field.label} value={value} onChange={onChange} testid={`field-${field.key}`} />;
  }
  if (field.type === "textarea") {
    return (
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{field.label}</span>
        <textarea rows={4} value={value || ""} onChange={(e) => onChange(e.target.value)}
          className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-2.5 outline-none focus:border-teal resize-y text-sm" />
      </label>
    );
  }
  if (field.type === "select") {
    return (
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{field.label}</span>
        <select value={value || ""} onChange={(e) => onChange(e.target.value)}
          className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-2.5 outline-none focus:border-teal text-sm">
          {field.options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </label>
    );
  }
  if (field.type === "list") {
    const text = Array.isArray(value) ? value.join("\n") : (value || "");
    return (
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{field.label}</span>
        <textarea rows={4} value={text} onChange={(e) => onChange(e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
          className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-2.5 outline-none focus:border-teal resize-y text-sm font-mono" />
      </label>
    );
  }
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{field.label}</span>
      <input type="text" value={value || ""} onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-2.5 outline-none focus:border-teal text-sm" />
    </label>
  );
}
