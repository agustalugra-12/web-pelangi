import { useState } from "react";
import { facilityIcons } from "@/data/content";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { HOME } from "@/constants/testIds";
import RoomDetailModal from "./RoomDetailModal";

export default function RoomCard({ room, index = 0 }) {
  const { site } = useContent();
  const { t, pick } = useLang();
  const name = pick(room, "name");
  const description = pick(room, "description");
  const capacity = pick(room, "capacity");
  const [detailOpen, setDetailOpen] = useState(false);
  return (
    <article
      className="relative bg-paper rounded-3xl overflow-hidden shadow-paper-sm border border-ink/5 flex flex-col reveal group"
      style={{ animationDelay: `${index * 100}ms` }}
      data-testid={`room-card-${room.slug}`}
    >
      <div className="flex" aria-hidden="true">
        <span className="flex-1 h-1.5 bg-emerald-600"></span>
        <span className="flex-1 h-1.5 bg-yellow-400"></span>
        <span className="flex-1 h-1.5 bg-red-500"></span>
      </div>

      <button
        type="button"
        onClick={() => setDetailOpen(true)}
        data-testid={`room-photo-${room.slug}`}
        className="relative block w-full text-left cursor-zoom-in"
        aria-label={`${t("rooms.viewDetails")} — ${name}`}
      >
        <img src={room.image} alt={name} className="w-full h-56 object-cover" loading="lazy" />
        <span className="absolute top-4 left-4 bg-mustard text-teal-deep font-semibold text-xs px-3 py-1 rounded-full shadow-paper-sm">
          {capacity} · {room.size}
        </span>
        <span className="absolute inset-0 bg-ink/0 group-hover:bg-ink/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
          <span className="bg-white/90 text-teal-deep text-xs font-semibold px-3 py-1.5 rounded-full inline-flex items-center gap-1.5">
            <i className="fa-solid fa-images text-[10px]" aria-hidden="true"></i>
            {t("rooms.viewDetails")}
          </span>
        </span>
      </button>
      {detailOpen && <RoomDetailModal room={room} onClose={() => setDetailOpen(false)} />}
      <div className="p-6 flex-1 flex flex-col">
        <h3 className="font-display text-2xl text-teal-deep">{name}</h3>
        <p className="mt-2 text-sm text-teal-deep/75 leading-relaxed">{description}</p>

        <ul className="mt-4 flex flex-wrap gap-2">
          {(room.facilities || []).slice(0, 8).map((f) => (
            <li
              key={f}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-teal-soft bg-teal/5 border border-teal/15 rounded-full px-2.5 py-1"
            >
              {facilityIcons[f] && (
                <i className={`fa-solid ${facilityIcons[f]} text-[10px] text-mustard-deep`} aria-hidden="true"></i>
              )}
              <span>{f}</span>
            </li>
          ))}
        </ul>

        <div className="mt-6 flex items-end justify-between">
          <div>
            <p className="text-xs text-teal-deep/60">{t("rooms.startFrom")}</p>
            <p className="font-display text-2xl text-mustard-deep italic">{room.priceFrom}</p>
            <p className="text-[11px] text-teal-deep/60">{t("rooms.perNight")}</p>
          </div>
          <a
            href={site.bookingUrl}
            target="_blank"
            rel="noopener noreferrer"
            data-testid={`${HOME.bookNowBtn}-${room.slug}`}
            className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-4 py-2 text-sm font-semibold shadow-paper-sm"
          >
            {t("common.bookNow")}
            <i className="fa-solid fa-arrow-right text-[10px]" aria-hidden="true"></i>
          </a>
        </div>
      </div>
    </article>
  );
}
