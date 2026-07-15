import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ADMIN } from "@/constants/testIds";
import { toast } from "sonner";

export default function AdminLogin() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user && user !== false) navigate("/admin/dashboard", { replace: true });
  }, [user, navigate]);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const res = await login(form.email, form.password);
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      toast.error(res.error);
      return;
    }
    toast.success("Selamat datang kembali!");
    navigate("/admin/dashboard", { replace: true });
  };

  return (
    <div className="min-h-screen grain flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-md bg-paper rounded-3xl shadow-paper border border-ink/10 p-8 md:p-10">
        <div className="flex items-center gap-2 mb-6">
          <span className="inline-flex h-9 w-9 rounded-full bg-teal-deep text-mustard-soft items-center justify-center font-display italic">P</span>
          <span className="font-display italic text-xl text-teal-deep">Pelangi Admin</span>
        </div>
        <p className="font-script text-2xl text-mustard-deep">Welcome back</p>
        <h1 className="font-display text-3xl text-teal-deep italic">Sign in.</h1>

        <form onSubmit={submit} className="mt-8 space-y-4">
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Email</span>
            <input
              data-testid={ADMIN.loginEmail}
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal"
              autoComplete="email"
            />
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-teal-deep/70 font-semibold">Password</span>
            <input
              data-testid={ADMIN.loginPassword}
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="mt-1 w-full rounded-xl border-2 border-ink/10 bg-cream px-4 py-3 outline-none focus:border-teal"
              autoComplete="current-password"
            />
          </label>
          {error && <p className="text-sm text-red-600" data-testid="admin-login-error">{error}</p>}
          <button
            type="submit"
            data-testid={ADMIN.loginSubmit}
            disabled={loading}
            className="btn-lift w-full rounded-full bg-leaf text-white px-5 py-3 font-semibold shadow-paper-sm disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="mt-6 text-xs text-teal-deep/60 text-center">
          Halaman ini hanya untuk pengelola konten Pelangi Homestay.
        </p>
      </div>
    </div>
  );
}
