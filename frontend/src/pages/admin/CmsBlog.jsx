import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ADMIN } from "@/constants/testIds";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";

export default function CmsBlog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [gsc, setGsc] = useState(null);
  const [queue, setQueue] = useState(null);
  const [dilewati, setDilewati] = useState(null);
  const [rules, setRules] = useState(null);
  const [rulesOpen, setRulesOpen] = useState(false);
  const [rulesSaving, setRulesSaving] = useState(false);
  const [basi, setBasi] = useState(null);
  const [cakupan, setCakupan] = useState(null);
  const [expandedCluster, setExpandedCluster] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [{ data }, { data: statsData }, { data: gscData }, { data: queueData }, { data: dilewatiData }, { data: rulesData }, { data: basiData }, { data: cakupanData }] = await Promise.all([
        api.get("/admin/blog"),
        api.get("/admin/seo-agent/stats").catch(() => ({ data: null })),
        api.get("/admin/gsc/summary").catch(() => ({ data: null })),
        api.get("/admin/seo-agent/queue").catch(() => ({ data: null })),
        api.get("/admin/seo-agent/dilewati").catch(() => ({ data: null })),
        api.get("/admin/editorial-rules").catch(() => ({ data: null })),
        api.get("/admin/seo-agent/basi").catch(() => ({ data: null })),
        api.get("/admin/seo-agent/cakupan").catch(() => ({ data: null })),
      ]);
      setPosts(data);
      setStats(statsData);
      setGsc(gscData);
      setQueue(queueData);
      setDilewati(dilewatiData);
      setRules(rulesData?.rules || []);
      setBasi(basiData);
      setCakupan(cakupanData);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    } finally {
      setLoading(false);
    }
  };

  const saveRules = async (nextRules) => {
    setRulesSaving(true);
    try {
      const { data } = await api.put("/admin/editorial-rules", { rules: nextRules });
      setRules(data.rules);
      toast.success("Aturan editorial disimpan");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    } finally {
      setRulesSaving(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Analytics Dashboard (2026-07-28) - performa per artikel dari Google Search Console
  // (GET /admin/gsc/summary, data disinkron harian lewat scripts/gsc_sync.py). Dicocokkan
  // ke baris tabel via slug - artikel yang belum ada datanya (mis. baru terbit, GSC punya
  // lag pelaporan ~2-3 hari) tampil "-" bukan 0, supaya tidak disalahartikan "0 klik nyata".
  const gscBySlug = Object.fromEntries((gsc?.articles || []).map((a) => [a.slug, a]));
  const fmtCtr = (v) => (v == null ? "-" : `${(v * 100).toFixed(1)}%`);
  const fmtPos = (v) => (v == null ? "-" : v.toFixed(1));

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

      {stats && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="seo-agent-stats">
          <div>
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Dibuat AI hari ini</p>
            <p className="text-2xl font-display text-teal-deep">{stats.generated_today}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Total dibuat AI</p>
            <p className="text-2xl font-display text-teal-deep">{stats.generated_total}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Keyword tersisa</p>
            <p className="text-2xl font-display text-teal-deep">{stats.keyword_belum_dibuat}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Keyword sudah dipakai</p>
            <p className="text-2xl font-display text-teal-deep">{stats.keyword_sudah_dibuat}</p>
          </div>
          {(stats.last_generated_title || stats.keyword_dilewati_mirip > 0 || stats.keyword_gagal_berulang > 0 || stats.keyword_ditolak_tipe_properti_salah > 0 || stats.usage_cost_today_total > 0) && (
            <div className="col-span-2 md:col-span-4 pt-2 border-t border-ink/10 text-sm text-teal-deep/70 space-y-1">
              {stats.last_generated_title && (
                <p>
                  Artikel AI terakhir: <span className="font-semibold text-teal-deep">{stats.last_generated_title}</span>
                  {stats.last_generated_at && (
                    <span> — {new Date(stats.last_generated_at).toLocaleString("id-ID")}</span>
                  )}
                </p>
              )}
              {stats.keyword_dilewati_mirip > 0 && (
                <p title="Keyword yang dilewati otomatis karena topiknya terlalu mirip artikel yang sudah terbit (cegah keyword cannibalization).">
                  {stats.keyword_dilewati_mirip} keyword dilewati otomatis (topik mirip artikel yang sudah ada)
                </p>
              )}
              {stats.keyword_gagal_berulang > 0 && (
                <p title="Keyword yang gagal lolos pengecekan kualitas (fact-check/editor/FAQ) berkali-kali, otomatis dihentikan supaya tidak terus dicoba ulang dan buang token.">
                  {stats.keyword_gagal_berulang} keyword dihentikan otomatis (gagal berulang kali, hemat token)
                </p>
              )}
              {stats.keyword_ditolak_tipe_properti_salah > 0 && (
                <p title="Khusus Pelangi Homestay: keyword yang menyebut 'villa' ditolak SEBELUM ditulis (Pelangi bukan villa) - mencegah biaya draft lengkap yang pasti gagal cek fakta di akhir.">
                  {stats.keyword_ditolak_tipe_properti_salah} keyword ditolak otomatis (salah tipe properti, hemat token)
                </p>
              )}
              {stats.usage_cost_today_total > 0 && (
                <p title="Total biaya OpenAI AI Blog hari ini (kedua situs gabung) - dipecah per model di bawah.">
                  Biaya AI Blog hari ini: <span className="font-semibold text-teal-deep">${stats.usage_cost_today_total.toFixed(4)}</span>
                  {stats.usage_by_model_today?.length > 0 && (
                    <span className="text-teal-deep/60">
                      {" "}({stats.usage_by_model_today.map((m) => `${m.model}: $${m.cost_usd.toFixed(4)}`).join(", ")})
                    </span>
                  )}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {gsc && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6" data-testid="gsc-analytics-summary">
          <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-3">
            Performa Google Search Console (28 hari terakhir)
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Total Klik</p>
              <p className="text-2xl font-display text-teal-deep">{gsc.total_clicks}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Total Impression</p>
              <p className="text-2xl font-display text-teal-deep">{gsc.total_impressions}</p>
            </div>
            <div className="col-span-2 md:col-span-2">
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Artikel Terbaik</p>
              <p className="text-lg font-display text-teal-deep truncate">
                {gsc.best_article ? `${gsc.best_article.title} (${gsc.best_article.clicks} klik)` : "Belum ada data"}
              </p>
            </div>
          </div>
          {gsc.last_synced_at && (
            <p className="mt-3 pt-3 border-t border-ink/10 text-xs text-teal-deep/60">
              Terakhir sinkron: {new Date(gsc.last_synced_at).toLocaleString("id-ID")}
            </p>
          )}
          {/* Papan performa (2026-07-29, permintaan user) - gsc.articles SUDAH lengkap &
              terurut (clicks desc, lihat admin_gsc_summary di server.py), sebelumnya cuma
              dipakai utk ambil best_article - sisanya belum pernah ditampilkan sama sekali.
              2 daftar: performa terbaik (clicks>0, biar tidak penuh nol di situs yg masih
              baru) & "kandidat perlu perbaikan" (SUDAH dapat impresi tapi 0 klik - sinyal
              judul/meta description kurang menarik utk di-klik, beda dari artikel yang
              memang belum pernah muncul di pencarian sama sekali). */}
          {gsc.articles && gsc.articles.length > 0 && (
            <div className="mt-4 pt-4 border-t border-ink/10 grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-2">
                  🏆 Performa Terbaik
                </p>
                {gsc.articles.filter((a) => a.clicks > 0).length === 0 ? (
                  <p className="text-xs text-teal-deep/50">Belum ada artikel yang dapat klik.</p>
                ) : (
                  <ol className="space-y-1.5">
                    {gsc.articles.filter((a) => a.clicks > 0).slice(0, 5).map((a, i) => (
                      <li key={a.slug} className="flex items-center gap-2 text-sm">
                        <span className="w-4 text-right text-teal-deep/40 font-mono text-xs shrink-0">{i + 1}.</span>
                        <span className="flex-1 text-teal-deep truncate">{a.title}</span>
                        <span className="text-xs font-semibold text-leaf shrink-0">{a.clicks} klik</span>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
              <div>
                <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-2">
                  ⚠️ Kandidat Perlu Perbaikan
                </p>
                {gsc.articles.filter((a) => a.impressions > 0 && a.clicks === 0).length === 0 ? (
                  <p className="text-xs text-teal-deep/50">Tidak ada - semua artikel yang dapat impresi juga dapat klik.</p>
                ) : (
                  <ol className="space-y-1.5">
                    {gsc.articles.filter((a) => a.impressions > 0 && a.clicks === 0)
                      .sort((a, b) => b.impressions - a.impressions).slice(0, 5).map((a, i) => (
                      <li key={a.slug} className="flex items-center gap-2 text-sm" title="Sudah tampil di pencarian Google tapi belum ada yang klik - coba perbaiki judul/deskripsi">
                        <span className="w-4 text-right text-teal-deep/40 font-mono text-xs shrink-0">{i + 1}.</span>
                        <span className="flex-1 text-teal-deep truncate">{a.title}</span>
                        <span className="text-xs font-semibold text-amber-600 shrink-0">{a.impressions} impresi, 0 klik</span>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {queue && queue.next_up.length > 0 && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6" data-testid="seo-agent-queue">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">
              Perencanaan Artikel — Antrean Berikutnya
            </p>
            <p className="text-xs text-teal-deep/60">{queue.total_belum_dibuat} keyword tersisa</p>
          </div>
          <ol className="space-y-2">
            {queue.next_up.slice(0, 8).map((k, i) => (
              <li key={k.keyword} className="flex items-center gap-3 text-sm">
                <span className="w-5 text-right text-teal-deep/40 font-mono text-xs shrink-0">{i + 1}.</span>
                <span className="flex-1 text-teal-deep font-medium">{k.keyword}</span>
                <span className="text-xs text-teal-deep/60 hidden sm:inline">{k.cluster}</span>
                {/* Intent Classifier (2026-08-02, PRD "AI Blog V2.0" modul 3) - field ini
                    sebelumnya ada di data tapi tidak pernah ditampilkan di mana pun (dead
                    data). Warna netral (bukan merah/kuning spt priority) krn ini bukan
                    sinyal urgensi, cuma kategori. */}
                {k.intent && (
                  <span className="text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 bg-teal-deep/8 text-teal-deep/70 hidden md:inline-block">
                    {k.intent}
                  </span>
                )}
                <span className={`text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 ${
                  k.priority === "High" ? "bg-red-100 text-red-700"
                    : k.priority === "Medium" ? "bg-mustard-soft/30 text-mustard-deep"
                    : "bg-ink/10 text-ink/60"
                }`}>
                  {k.priority}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {dilewati && dilewati.items.length > 0 && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6" data-testid="seo-agent-dilewati">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">
              ⚠️ Keyword Dilewati Otomatis (Risiko Cannibalization)
            </p>
            <p className="text-xs text-teal-deep/60">{dilewati.total} keyword</p>
          </div>
          <p className="text-xs text-teal-deep/50 mb-3">
            Keyword ini di-skip otomatis karena topiknya dianggap terlalu mirip artikel yang
            sudah ditulis (cek sesama cluster). Review manual kalau menurutmu sebenarnya beda
            angle - keyword bisa direset ke "belum_dibuat" lewat database kalau perlu ditulis.
          </p>
          <ol className="space-y-2">
            {dilewati.items.slice(0, 8).map((k, i) => (
              <li key={k.keyword} className="flex items-start gap-3 text-sm">
                <span className="w-5 text-right text-teal-deep/40 font-mono text-xs shrink-0 mt-0.5">{i + 1}.</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-teal-deep font-medium truncate">{k.keyword}</span>
                    <span className="text-xs text-teal-deep/60 shrink-0">{k.cluster}</span>
                  </div>
                  {k.cannibalization_note && (
                    <p className="text-xs text-teal-deep/50 truncate" title={k.cannibalization_note}>{k.cannibalization_note}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {rules && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6" data-testid="editorial-rules">
          <button
            type="button"
            className="w-full flex items-center justify-between"
            onClick={() => setRulesOpen((o) => !o)}
          >
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">
              📋 Aturan Editorial AI ({rules.length})
            </p>
            <span className="text-xs text-teal-deep/60">{rulesOpen ? "Tutup ▲" : "Buka ▼"}</span>
          </button>
          {rulesOpen && (
            <div className="mt-3 space-y-2">
              <p className="text-xs text-teal-deep/50 mb-2">
                Aturan ini disuntikkan ke prompt AI setiap kali menulis artikel baru - edit di
                sini, tidak perlu ubah kode.
              </p>
              {rules.map((r, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    className="flex-1 text-sm border border-ink/15 rounded-lg px-3 py-1.5 bg-white"
                    value={r}
                    onChange={(e) => {
                      const next = [...rules];
                      next[i] = e.target.value;
                      setRules(next);
                    }}
                  />
                  <button
                    type="button"
                    className="text-xs text-red-600 shrink-0"
                    onClick={() => setRules(rules.filter((_, k) => k !== i))}
                  >
                    Hapus
                  </button>
                </div>
              ))}
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  className="text-xs font-semibold text-teal-deep border border-teal-deep/20 rounded-full px-3 py-1"
                  onClick={() => setRules([...rules, ""])}
                >
                  + Tambah Aturan
                </button>
                <button
                  type="button"
                  disabled={rulesSaving}
                  className="text-xs font-semibold text-white bg-leaf rounded-full px-3 py-1 disabled:opacity-50"
                  onClick={() => saveRules(rules)}
                >
                  {rulesSaving ? "Menyimpan..." : "Simpan"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {basi && basi.total > 0 && (
        <div className="bg-paper rounded-2xl border border-ink/10 p-5 mb-6" data-testid="seo-agent-basi">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">
              🕐 Kandidat Artikel Perlu Ditinjau Ulang (Freshness)
            </p>
            <p className="text-xs text-teal-deep/60">{basi.total} artikel</p>
          </div>
          <p className="text-xs text-teal-deep/50 mb-3">
            Artikel ini menyebut harga tapi diterbitkan SEBELUM harga kamar terakhir diubah
            di CMS - cek apakah angka di dalamnya masih sesuai harga terbaru. Tidak
            di-update otomatis, ini cuma daftar kandidat buat ditinjau staf.
          </p>
          <ol className="space-y-1.5">
            {basi.items.map((a, i) => (
              <li key={a.slug} className="flex items-center gap-3 text-sm">
                <span className="w-5 text-right text-teal-deep/40 font-mono text-xs shrink-0">{i + 1}.</span>
                <span className="flex-1 text-teal-deep truncate">{a.title}</span>
                <span className="text-xs text-teal-deep/50 shrink-0">{new Date(a.created_at).toLocaleDateString("id-ID")}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {cakupan && cakupan.clusters?.length > 0 && (
        <div className="mb-6 space-y-4" data-testid="seo-agent-cakupan">
          {/* AI Recommendation Today (2026-08-03, permintaan Agus - "bagian paling
              penting", ditaruh paling atas) - reuse persis urutan get_next_keyword,
              alasan dihitung dari sinyal ASLI (priority/musim/demand GSC), bukan
              template kosong. */}
          {cakupan.rekomendasi_hari_ini?.length > 0 && (
            <div className="bg-teal-deep rounded-2xl p-5 text-white shadow-paper-sm" data-testid="cakupan-rekomendasi">
              <p className="text-xs uppercase tracking-widest text-white/70 font-semibold mb-2">
                🎯 Rekomendasi Hari Ini
              </p>
              <p className="text-sm text-white/90 mb-3">Hari ini disarankan menulis:</p>
              <ol className="space-y-2">
                {cakupan.rekomendasi_hari_ini.map((r, i) => (
                  <li key={i} className="text-sm">
                    <span className="font-display">{i + 1}. {r.keyword}</span>
                    <span className="block text-xs text-white/70 pl-4">↳ {r.alasan}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Ringkasan target (2026-08-03) */}
          <div className="bg-paper rounded-2xl border border-ink/10 p-5 grid grid-cols-2 md:grid-cols-5 gap-4" data-testid="cakupan-ringkasan">
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Coverage Editorial</p>
              <p className="text-2xl font-display text-teal-deep">{cakupan.persen_keseluruhan}%</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Keyword Selesai</p>
              <p className="text-2xl font-display text-teal-deep">{cakupan.total_sudah} / {cakupan.total_target}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Sisa Ditulis</p>
              <p className="text-2xl font-display text-teal-deep">{cakupan.total_sisa}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Cluster Terlemah</p>
              <p className="text-lg font-display text-red-500">{cakupan.cluster_terlemah || "-"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold">Cluster Terkuat</p>
              <p className="text-lg font-display text-leaf">{cakupan.cluster_terkuat || "-"}</p>
            </div>
          </div>

          {/* Insight (2026-08-03) */}
          {cakupan.insight?.length > 0 && (
            <div className="bg-paper rounded-2xl border border-ink/10 p-5" data-testid="cakupan-insight">
              <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-2">💡 Insight Hari Ini</p>
              <ul className="text-sm text-teal-deep/80 space-y-1 list-disc list-inside">
                {cakupan.insight.map((line, i) => <li key={i}>{line}</li>)}
              </ul>
            </div>
          )}

          {/* Per-cluster (2026-08-03) - progress lebih informatif + badge prioritas +
              expand utk keyword berikutnya, coverage, traffic/booking opportunity
              (estimasi internal - lihat CLUSTER_TRAFFIC_HEURISTIK/CLUSTER_BOOKING_
              HEURISTIK di backend, DITIMPA data GSC asli kalau sudah ada), & jaringan
              internal link. Sengaja "Cakupan Editorial/Keyword", BUKAN "Topical
              Authority" (label lama itu tidak akurat - lihat catatan backend). */}
          <div className="bg-paper rounded-2xl border border-ink/10 p-5">
            <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-1">
              📊 Cakupan Editorial per Cluster
            </p>
            <p className="text-xs text-teal-deep/50 mb-3">
              Keyword yang sudah ditulis dari yang MASIH BISA ditulis (keyword yang otomatis
              dilewati karena duplikat topik tidak dihitung sebagai "kurang" - lihat detail
              tiap cluster). Klik cluster untuk lihat keyword berikutnya & jaringan link internal.
            </p>
            <div className="space-y-2">
              {cakupan.clusters.map((c) => {
                const isOpen = expandedCluster === c.cluster;
                return (
                  <div key={c.cluster} className="border border-ink/10 rounded-xl overflow-hidden">
                    <button
                      onClick={() => setExpandedCluster(isOpen ? null : c.cluster)}
                      data-testid={`cakupan-cluster-${c.cluster}`}
                      className="w-full text-left p-3 hover:bg-ink/5"
                    >
                      <div className="flex items-center gap-3 text-sm">
                        <span className="w-28 shrink-0 text-teal-deep/80 truncate font-semibold">{c.cluster}</span>
                        <div className="flex-1 h-2.5 rounded-full bg-ink/10 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${c.persen >= 100 ? "bg-leaf" : c.persen >= 70 ? "bg-leaf" : c.persen >= 40 ? "bg-mustard-deep" : c.persen >= 20 ? "bg-orange-400" : "bg-red-400"}`}
                            style={{ width: `${Math.min(100, c.persen)}%` }}
                          />
                        </div>
                        <span className="w-16 shrink-0 text-xs font-semibold text-teal-deep text-right">{c.persen}%</span>
                        <span className="shrink-0 text-xs whitespace-nowrap">{c.status_emoji} {c.status_label}</span>
                        <i className={`fa-solid fa-chevron-${isOpen ? "up" : "down"} text-teal-deep/40 text-xs shrink-0`} aria-hidden="true"></i>
                      </div>
                      <div className="flex items-center gap-4 mt-1.5 pl-[7.5rem] text-[11px] text-teal-deep/60">
                        <span>{c.sudah_dibuat} / {c.total} artikel · sisa {c.sisa}</span>
                        {c.dilewati_mirip > 0 && (
                          <span title="Keyword yang otomatis dilewati karena topiknya duplikat artikel yang sudah ada">
                            ({c.dilewati_mirip} dilewati/duplikat)
                          </span>
                        )}
                        <span title={c.traffic_gsc_impressions ? `${c.traffic_gsc_impressions} impression nyata dari Google Search Console` : "Estimasi internal, bukan data pencarian nyata"}>
                          {c.traffic_gsc_impressions ? `${c.traffic_gsc_impressions} impresi (GSC)` : "🔥".repeat(c.traffic_level || 1) + " Traffic (estimasi)"}
                        </span>
                        <span title="Estimasi peluang booking - internal, bukan data nyata">
                          {"💰".repeat(c.booking_level || 1)} Booking (estimasi)
                        </span>
                      </div>
                    </button>
                    {isOpen && (
                      <div className="p-3 pt-0 border-t border-ink/10 bg-ink/[0.02] text-sm space-y-3">
                        <div>
                          <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mt-3 mb-1.5">
                            Belum Ditulis {c.belum_ditulis?.length ? `(${c.sisa})` : ""}
                          </p>
                          {c.belum_ditulis?.length ? (
                            <ul className="space-y-1">
                              {c.belum_ditulis.map((k, i) => (
                                <li key={i} className="flex items-center gap-1.5">
                                  <span className="text-teal-deep/30">✓</span>
                                  <span className="text-teal-deep/80">{k.keyword}</span>
                                  {k.priority === "High" && <span className="text-[10px] px-1.5 rounded bg-red-100 text-red-700 font-semibold">High</span>}
                                  {k.musiman && <span className="text-[10px] px-1.5 rounded bg-mustard-deep/20 text-mustard-deep font-semibold">Musiman</span>}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-teal-deep/50 italic">Tidak ada - semua keyword yang bisa ditulis di cluster ini sudah selesai.</p>
                          )}
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-widest text-teal-deep/60 font-semibold mb-1.5">
                            Jaringan Internal Link
                          </p>
                          {c.internal_links?.length ? (
                            <ul className="space-y-1.5">
                              {c.internal_links.map((l, i) => (
                                <li key={i} className="text-teal-deep/80">
                                  <span className="font-medium">{l.from_title}</span>
                                  {l.targets.map((t, j) => (
                                    <span key={j} className="block pl-4 text-xs text-teal-deep/60">↳ link ke: {t.title}</span>
                                  ))}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-teal-deep/50 italic">Belum ada link internal tercatat di cluster ini.</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

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
                {gsc && (
                  <>
                    <th className="px-5 py-3 font-medium hidden lg:table-cell text-right" title="Klik dari Google Search Console, 28 hari terakhir">Klik</th>
                    <th className="px-5 py-3 font-medium hidden lg:table-cell text-right" title="Impression dari Google Search Console, 28 hari terakhir">Impresi</th>
                    <th className="px-5 py-3 font-medium hidden lg:table-cell text-right" title="Click-through rate">CTR</th>
                    <th className="px-5 py-3 font-medium hidden lg:table-cell text-right" title="Posisi rata-rata di hasil pencarian Google">Posisi</th>
                  </>
                )}
                <th className="px-5 py-3 font-medium text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id} className="border-t border-ink/10" data-testid={`admin-post-row-${p.slug}`}>
                  <td className="px-5 py-3">
                    <div className="flex flex-col items-start gap-1.5">
                      <p className="font-semibold text-teal-deep">{p.title}</p>
                      <div className="flex flex-wrap items-center gap-1.5">
                      {p.seo_keyword && (
                        <span
                          className="text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 bg-mustard-soft/30 text-mustard-deep shrink-0"
                          title={`Dibuat otomatis AI SEO Agent - keyword: ${p.seo_keyword}`}
                        >
                          🤖 AI
                        </span>
                      )}
                      {p.competitor_analysis && (
                        <span
                          className="text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 bg-teal-deep/10 text-teal-deep shrink-0"
                          title={
                            `Analisis ${p.competitor_analysis.competitors.length} kompetitor, ` +
                            `rata-rata ${p.competitor_analysis.avg_word_count} kata:\n` +
                            p.competitor_analysis.competitors.map((c) => `• ${c.url} (${c.word_count} kata)`).join("\n")
                          }
                        >
                          🔍 {p.competitor_analysis.competitors.length} Kompetitor
                        </span>
                      )}
                      {p.competitor_analysis?.tingkat_persaingan && (
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 ${
                            p.competitor_analysis.tingkat_persaingan === "Tinggi" ? "bg-red-100 text-red-700"
                              : p.competitor_analysis.tingkat_persaingan === "Rendah" ? "bg-leaf/15 text-leaf"
                              : "bg-mustard-soft/30 text-mustard-deep"
                          }`}
                          title={
                            p.competitor_analysis.tingkat_persaingan === "Tinggi"
                              ? "Persaingan Tinggi - ada OTA besar (Booking.com/Traveloka/Agoda/dst) di hasil pencarian nyata utk keyword ini, sulit ditembus"
                              : p.competitor_analysis.tingkat_persaingan === "Rendah"
                              ? "Persaingan Rendah - kompetitor yang ditemukan sangat sedikit, keyword jarang dibahas"
                              : "Persaingan Sedang - tidak ada OTA besar terdeteksi, kompetitor cukup banyak"
                          }
                        >
                          Persaingan {p.competitor_analysis.tingkat_persaingan}
                        </span>
                      )}
                      {p.intent_coverage && (
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 ${
                            p.intent_coverage.skor_persen >= 80 ? "bg-leaf/15 text-leaf"
                              : p.intent_coverage.skor_persen >= 50 ? "bg-mustard-soft/30 text-mustard-deep"
                              : "bg-red-100 text-red-700"
                          }`}
                          title={
                            p.intent_coverage.kurang.length > 0
                              ? `Belum mencakup: ${p.intent_coverage.kurang.join(", ")}`
                              : "Semua kategori intent tercakup"
                          }
                        >
                          Intent {p.intent_coverage.skor_persen}%
                        </span>
                      )}
                      {p.content_health && (
                        // Content Health (2026-07-31, PRD "AI Blog V2" modul 15) - angka REAL
                        // & bisa diverifikasi, SENGAJA BUKAN "AI Detection %" (tidak ada metode
                        // AI-detection yang reliable, apalagi utk Bahasa Indonesia).
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 ${
                            p.content_health.slop_word_max_count >= 2 || (p.content_health.sentence_variance_cv != null && p.content_health.sentence_variance_cv < 0.32)
                              ? "bg-mustard-soft/30 text-mustard-deep"
                              : "bg-leaf/15 text-leaf"
                          }`}
                          title={`Kata hampa (menghadirkan/memberikan/menawarkan/memanjakan) muncul maks ${p.content_health.slop_word_max_count}x di artikel ini (batas blokir 3x). Variasi panjang kalimat (CV): ${p.content_health.sentence_variance_cv != null ? p.content_health.sentence_variance_cv.toFixed(2) : "-"} (makin tinggi makin bervariasi/manusiawi).`}
                        >
                          Health: Slop {p.content_health.slop_word_max_count}x · CV {p.content_health.sentence_variance_cv != null ? p.content_health.sentence_variance_cv.toFixed(2) : "-"}
                        </span>
                      )}
                      {p.expanded_at && (
                        <span
                          className="text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 bg-leaf/15 text-leaf shrink-0"
                          title={`Diperdalam AI karena terbukti dapat impression Google nyata — ${new Date(p.expanded_at).toLocaleString("id-ID")}`}
                        >
                          📈 Diperluas
                        </span>
                      )}
                      {(() => {
                        const wordCount = (p.content || "").trim().split(/\s+/).filter(Boolean).length;
                        // Alert cuma utk artikel AI (p.seo_keyword ada) - konten manual boleh
                        // pendek sengaja (2026-07-29, ditemukan saat backfill expand: blurb tips
                        // 45 kata itu memang sengaja singkat, bukan kegagalan kualitas).
                        const kurangDariSeribu = p.seo_keyword && wordCount < 1000;
                        return (
                          <span
                            className={`text-[10px] font-bold uppercase tracking-wide rounded-full px-2 py-0.5 shrink-0 ${
                              kurangDariSeribu ? "bg-red-100 text-red-700" : "bg-ink/5 text-teal-deep/60"
                            }`}
                            title={kurangDariSeribu ? "Di bawah 1000 kata - akan diperbaharui ke 1100-1200 kata di run mingguan berikutnya" : undefined}
                          >
                            {kurangDariSeribu && "⚠️ "}{wordCount} kata
                          </span>
                        );
                      })()}
                      </div>
                    </div>
                    <p className="text-xs text-teal-deep/60 md:hidden">{p.category}</p>
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell text-teal-deep/80">{p.category}</td>
                  <td className="px-5 py-3 hidden md:table-cell">
                    <span className={`text-xs font-semibold rounded-full px-2 py-1 ${p.published ? "bg-leaf/15 text-leaf" : "bg-ink/10 text-ink"}`}>
                      {p.published ? "Published" : "Draft"}
                    </span>
                    {p.noindex && (
                      <span className="ml-1.5 text-xs font-semibold rounded-full px-2 py-1 bg-amber-100 text-amber-700" title="Tetap bisa diakses via link langsung, tapi disembunyikan dari hasil pencarian Google">
                        Noindex
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell text-xs text-teal-deep/70">
                    {new Date(p.created_at).toLocaleDateString("id-ID")}
                  </td>
                  {gsc && (
                    <>
                      <td className="px-5 py-3 hidden lg:table-cell text-right text-teal-deep/80">
                        {gscBySlug[p.slug]?.clicks ?? "-"}
                      </td>
                      <td className="px-5 py-3 hidden lg:table-cell text-right text-teal-deep/80">
                        {gscBySlug[p.slug]?.impressions ?? "-"}
                      </td>
                      <td className="px-5 py-3 hidden lg:table-cell text-right text-teal-deep/80">
                        {fmtCtr(gscBySlug[p.slug]?.ctr)}
                      </td>
                      <td className="px-5 py-3 hidden lg:table-cell text-right text-teal-deep/80">
                        {fmtPos(gscBySlug[p.slug]?.position)}
                      </td>
                    </>
                  )}
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
