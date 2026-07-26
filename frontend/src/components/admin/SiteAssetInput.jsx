// Upload widget khusus hero photo & favicon/logo (2026-07-26) - beda dari ImageInput:
// path file TETAP (/assets/signage.webp, /assets/pelangi-logo.png), upload di sini cuma
// MENGGANTI ISI file itu (lihat POST /admin/site-asset/{slot} di server.py) supaya
// optimasi kecepatan loading yang sudah dikerjakan (preload hint, hardcoded di Home.jsx)
// tidak perlu diubah tiap admin ganti foto. Tidak ada field URL manual seperti ImageInput
// - path-nya memang tidak bisa diubah, cuma isinya.
import { useRef, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";

export default function SiteAssetInput({ slot, previewUrl, label, hint, testid }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [bust, setBust] = useState(0);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.post(`/admin/site-asset/${slot}`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBust(Date.now()); // cache-bust cuma preview di panel ini, bukan situs live
      toast.success("Foto tersimpan — sudah aktif di situs live");
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div>
      <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{label}</span>
      {hint && <p className="text-xs text-teal-deep/50 mt-0.5">{hint}</p>}
      <div className="mt-2 flex items-center gap-3">
        <div className="w-20 h-20 rounded-lg overflow-hidden border border-ink/10 bg-paper shrink-0">
          <img src={`${previewUrl}${bust ? `?t=${bust}` : ""}`} alt="" className="w-full h-full object-cover" />
        </div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          data-testid={testid}
          className="rounded-xl bg-teal-deep text-cream px-4 py-2.5 text-sm font-semibold disabled:opacity-60 whitespace-nowrap"
        >
          {uploading ? "Mengunggah…" : "Ganti Foto"}
        </button>
      </div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
    </div>
  );
}
