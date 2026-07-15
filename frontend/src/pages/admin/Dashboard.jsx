import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ADMIN } from "@/constants/testIds";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import BrandLogo from "@/components/site/BrandLogo";

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
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

  useEffect(() => {
    load();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/admin/login", { replace: true });
  };

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
    <div className="min-h-screen bg-cream">
      <header className="border-b border-ink/10 bg-paper">
        <div className="max-w-6xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <BrandLogo size={44} hoverFlip />
            <span className="flex flex-col leading-none">
              <span className="font-display italic text-lg text-teal-deep">Pelangi Homestay</span>
              <span className="text-[10px] uppercase tracking-widest text-mustard-deep mt-1">Admin</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-sm text-teal-deep/70 hidden sm:block">{user?.email}</span>
            <button
              type="button"
              onClick={handleLogout}
              data-testid={ADMIN.logoutBtn}
              className="rounded-full border-2 border-teal-deep text-teal-deep px-4 py-1.5 text-sm font-semibold hover:bg-teal-deep hover:text-cream"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 py-10">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <p className="font-script text-2xl text-mustard-deep">Kelola konten</p>
            <h1 className="font-display text-3xl md:text-4xl text-teal-deep italic">Blog posts.</h1>
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

        <div className="mt-10 bg-paper rounded-2xl border border-ink/10 overflow-hidden">
          {loading ? (
            <p className="p-8 text-center text-teal-deep/70">Memuat…</p>
          ) : posts.length === 0 ? (
            <p className="p-8 text-center text-teal-deep/70">Belum ada artikel. Mulai dengan menekan “Artikel Baru”.</p>
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
                      <Link
                        to={`/admin/posts/${p.id}`}
                        className="text-teal-deep hover:text-mustard-deep font-semibold text-sm mr-3"
                        data-testid={`admin-edit-${p.slug}`}
                      >
                        Edit
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleDelete(p.id, p.title)}
                        data-testid={`${ADMIN.postDelete}-${p.slug}`}
                        className="text-red-600 hover:text-red-800 font-semibold text-sm"
                      >
                        Hapus
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
