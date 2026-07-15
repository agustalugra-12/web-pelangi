// Reusable image upload widget. Uploads to /api/admin/media, returns URL.
// Also allows entering a manual URL / path.
import { useRef, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";

export default function ImageInput({ value, onChange, label = "Gambar", testid }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post("/admin/media", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onChange(data.url);
      toast.success("Gambar terunggah");
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div>
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">{label}</span>
        <div className="mt-1 flex gap-2">
          <input
            data-testid={testid ? `${testid}-url` : undefined}
            type="text"
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder="/assets/... atau /api/media/..."
            className="flex-1 rounded-xl border-2 border-ink/10 bg-paper px-4 py-2.5 outline-none focus:border-teal text-sm"
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            data-testid={testid ? `${testid}-upload` : undefined}
            className="rounded-xl bg-teal-deep text-cream px-4 py-2.5 text-sm font-semibold disabled:opacity-60 whitespace-nowrap"
          >
            {uploading ? "Mengunggah…" : "Upload"}
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFile}
        />
      </label>
      {value ? (
        <div className="mt-2 relative w-32 h-24 rounded-lg overflow-hidden border border-ink/10 bg-paper">
          <img src={value} alt="" className="w-full h-full object-cover" onError={(e) => { e.currentTarget.style.opacity = "0.2"; }} />
        </div>
      ) : null}
    </div>
  );
}
