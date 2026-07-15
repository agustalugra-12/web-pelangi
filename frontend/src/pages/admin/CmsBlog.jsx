import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ADMIN } from "@/constants/testIds";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";

export default function CmsBlog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/blog");
      setPosts(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id, title) => {
    if (!window.confirm(`Hapus artikel "${title}"?`)) return;
    try {
      await api.delete(`/admin/blog/${id}`);
      toast.success("Artikel dihapus");
      setPosts((prev) => prev.filter((p) => p.id !== id));
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="flex items-end justify-between gap-4 flex-wrap mb-6">
        <div>
          <p className="font-script text-2xl text-mustard-deep">Konten SEO</p>
          <h1 className="font-display text-3xl md:text-4xl text-teal-deep italic">Blog.</h1>
          <p className="text-sm text-teal-deep/70 mt-1">Publikasikan artikel untuk meningkatkan SEO dan menarik trafik organik.</p>
        </div>
        <Link
          to="/admin/posts/new"
          data-testid={ADMIN.createBtn}
          className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-5 py-2.5 font-semibold shadow-paper-sm"
        >
          <i className="fa-solid fa-plus text-xs" aria-hidden="true"></i>
          Artikel Baru
        </Link>
      </div>

      <div className="bg-paper rounded-2xl border border-ink/10 overflow-hidden">
        {loading ? (
          <p className="p-8 text-center text-teal-deep/70">Memuat…</p>
        ) : posts.length === 0 ? (
          <p className="p-8 text-center text-teal-deep/70">Belum ada artikel. Klik &quot;Artikel Baru&quot; untuk mulai.</p>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-teal-deep text-cream text-sm">
              <tr>
                <th className="px-5 py-3 font-medium">Judul</th>
                <th className="px-5 py-3 font-medium hidden md:table-cell">Kategori</th>
                <th className="px-5 py-3 font-medium hidden md:table-cell">Status</th>
                <th className="px-5 py-3 font-medium hidden md:table-cell">Tanggal</th>
                <th className="px-5 py-3 font-medium text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id} className="border-t border-ink/10" data-testid={`admin-post-row-${p.slug}`}>
                  <td className="px-5 py-3">
                    <p className="font-semibold text-teal-deep">{p.title}</p>
                    <p className="text-xs text-teal-deep/60 md:hidden">{p.category}</p>
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell text-teal-deep/80">{p.category}</td>
                  <td className="px-5 py-3 hidden md:table-cell">
                    <span className={`text-xs font-semibold rounded-full px-2 py-1 ${p.published ? "bg-leaf/15 text-leaf" : "bg-ink/10 text-ink"}`}>
                      {p.published ? "Published" : "Draft"}
                    </span>
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell text-xs text-teal-deep/70">
                    {new Date(p.created_at).toLocaleDateString("id-ID")}
                  </td>
                  <td className="px-5 py-3 text-right whitespace-nowrap">
                    <Link to={`/admin/posts/${p.id}`} data-testid={`admin-edit-${p.slug}`}
                      className="text-teal-deep hover:text-mustard-deep font-semibold text-sm mr-3">
                      Edit
                    </Link>
                    <button type="button" onClick={() => handleDelete(p.id, p.title)}
                      data-testid={`${ADMIN.postDelete}-${p.slug}`}
                      className="text-red-600 hover:text-red-800 font-semibold text-sm">
                      Hapus
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
