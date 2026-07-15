import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ADMIN } from "@/constants/testIds";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";

const CATEGORIES = ["Wisata", "Tips", "Itinerary", "Kuliner", "Event", "General"];

export default function PostEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id || id === "new";

  const [form, setForm] = useState({
    title: "",
    excerpt: "",
    content: "",
    category: "Wisata",
    cover_image: "",
    tags: "",
    published: true,
  });
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(!isNew);

  useEffect(() => {
    if (isNew) return;
    api
      .get(`/admin/blog/${id}`)
      .then(({ data }) => {
        setForm({
          title: data.title,
          excerpt: data.excerpt,
          content: data.content,
          category: data.category || "Wisata",
          cover_image: data.cover_image || "",
          tags: (data.tags || []).join(", "),
          published: !!data.published,
        });
      })
      .catch((e) => toast.error(formatApiError(e.response?.data?.detail) || e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const change = (k) => (e) => {
    const v = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [k]: v }));
  };

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...form,
      tags: form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };
    try {
      if (isNew) {
        await api.post("/admin/blog", payload);
        toast.success("Artikel dibuat");
      } else {
        await api.put(`/admin/blog/${id}`, payload);
        toast.success("Artikel diperbarui");
      }
      navigate("/admin/dashboard");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="min-h-[60vh] flex items-center justify-center text-teal-deep">Memuat…</div>;

  return (
    <div className="min-h-screen bg-cream">
      <header className="border-b border-ink/10 bg-paper">
        <div className="max-w-4xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link to="/admin/dashboard" className="text-teal-deep font-semibold text-sm">← Dashboard</Link>
          <span className="font-display italic text-teal-deep">{isNew ? "Artikel Baru" : "Edit Artikel"}</span>
        </div>
      </header>

      <form onSubmit={save} className="max-w-4xl mx-auto px-5 py-10 space-y-5">
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Judul</span>
          <input
            data-testid={ADMIN.postTitle}
            required value={form.title} onChange={change("title")}
            className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal font-display text-lg"
          />
        </label>

        <div className="grid md:grid-cols-2 gap-4">
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Kategori</span>
            <select
              data-testid={ADMIN.postCategory}
              value={form.category} onChange={change("category")}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal"
            >
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Tags (pisahkan dengan koma)</span>
            <input
              value={form.tags} onChange={change("tags")}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal"
              placeholder="bedugul, wisata"
            />
          </label>
        </div>

        <label className="block">
          <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Cover Image URL</span>
          <input
            value={form.cover_image} onChange={change("cover_image")}
            className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal"
            placeholder="https://..."
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Ringkasan</span>
          <textarea
            data-testid={ADMIN.postExcerpt}
            value={form.excerpt} onChange={change("excerpt")} rows={2}
            className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal resize-none"
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Konten</span>
          <textarea
            data-testid={ADMIN.postContent}
            required value={form.content} onChange={change("content")} rows={16}
            className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-paper px-4 py-3 outline-none focus:border-teal resize-y font-mono text-sm"
            placeholder="Tulis konten artikel di sini. Gunakan baris kosong untuk memisahkan paragraf."
          />
        </label>

        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={form.published} onChange={change("published")} />
          <span className="text-sm text-teal-deep">Publikasikan sekarang</span>
        </label>

        <div className="flex items-center gap-3 pt-4">
          <button
            type="submit"
            data-testid={ADMIN.postSave}
            disabled={saving}
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm disabled:opacity-60"
          >
            {saving ? "Menyimpan…" : "Simpan"}
          </button>
          <Link to="/admin/dashboard" className="text-teal-deep font-semibold text-sm">Batal</Link>
        </div>
      </form>
    </div>
  );
}
