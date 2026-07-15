import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SectionHeading from "@/components/site/SectionHeading";
import api from "@/lib/api";

export default function Blog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/blog").then(({ data }) => {
      setPosts(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="Blog" title="Cerita &" italicWord="tips" subtitle="Panduan wisata, itinerary, dan cerita dari Bedugul." />

        {loading ? (
          <p className="mt-12 text-center text-teal-deep/70">Memuat…</p>
        ) : posts.length === 0 ? (
          <p className="mt-12 text-center text-teal-deep/70">Belum ada artikel.</p>
        ) : (
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((p, i) => (
              <Link
                key={p.id}
                to={`/blog/${p.slug}`}
                data-testid={`blog-card-${p.slug}`}
                className="group bg-paper rounded-3xl overflow-hidden shadow-paper-sm border border-ink/5 reveal"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="aspect-[16/10] bg-teal-deep flex items-center justify-center text-mustard-soft font-display italic text-3xl">
                  {p.category}
                </div>
                <div className="p-5">
                  <span className="text-[11px] font-semibold uppercase tracking-widest text-mustard-deep">{p.category}</span>
                  <h3 className="mt-1 font-display text-xl text-teal-deep group-hover:text-mustard-deep transition-colors">
                    {p.title}
                  </h3>
                  <p className="mt-2 text-sm text-teal-deep/75 line-clamp-3">{p.excerpt}</p>
                  <p className="mt-4 text-xs text-teal-deep/60">
                    {new Date(p.created_at).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
