// Media library — list & delete uploaded images. Copy URL for use in editors.
import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import ImageInput from "@/components/admin/ImageInput";

export default function CmsMedia() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/media");
      setItems(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async () => {
    await load();
  };

  const remove = async (id) => {
    if (!window.confirm("Hapus foto ini?")) return;
    try {
      await api.delete(`/admin/media/${id}`);
      setItems((arr) => arr.filter((x) => x.id !== id));
      toast.success("Foto dihapus");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    }
  };

  const copyUrl = (url) => {
    navigator.clipboard?.writeText(url);
    toast.success("URL disalin");
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <p className="font-script text-2xl text-mustard-deep">Perpustakaan</p>
        <h1 className="font-display text-3xl md:text-4xl text-teal-deep italic">Media.</h1>
        <p className="text-sm text-teal-deep/70 mt-1">Unggah foto sekali, gunakan di banyak tempat. Klik URL untuk menyalin.</p>
      </div>

      <div className="bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-5 mb-6">
        <ImageInput label="Unggah foto baru" value="" onChange={handleUpload} testid="media-uploader" />
        <p className="text-xs text-teal-deep/60 mt-2">Format: JPG, PNG, WebP. Maks 6 MB.</p>
      </div>

      {loading ? (
        <p className="text-teal-deep/70">Memuat…</p>
      ) : items.length === 0 ? (
        <p className="text-teal-deep/70">Belum ada media. Unggah gambar pertama Anda.</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {items.map((m) => (
            <div key={m.id} className="bg-paper rounded-2xl overflow-hidden border border-ink/10 shadow-paper-sm">
              <div className="aspect-square bg-cream overflow-hidden">
                <img src={m.url} alt={m.original_filename} className="w-full h-full object-cover" loading="lazy" />
              </div>
              <div className="p-3 space-y-1">
                <p className="text-xs text-teal-deep truncate" title={m.original_filename}>{m.original_filename}</p>
                <div className="flex gap-1">
                  <button type="button" onClick={() => copyUrl(m.url)}
                    className="flex-1 text-[11px] rounded-full bg-teal-deep text-cream px-2 py-1 font-semibold"
                    data-testid={`media-copy-${m.id}`}
                  >
                    Salin URL
                  </button>
                  <button type="button" onClick={() => remove(m.id)}
                    className="rounded-full bg-red-100 text-red-700 px-2 py-1 text-[11px] font-semibold"
                    data-testid={`media-delete-${m.id}`}
                  >
                    Hapus
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
