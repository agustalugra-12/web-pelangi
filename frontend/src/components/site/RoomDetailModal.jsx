import { useState } from "react";
import { facilityIcons } from "@/data/content";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { HOME } from "@/constants/testIds";

export default function RoomDetailModal({ room, onClose }) {
  const { site } = useContent();
  const { t, pick } = useLang();
  const name = pick(room, "name");
  const description = pick(room, "description");
  const photos = room.gallery?.length ? room.gallery : [room.image];
  const [active, setActive] = useState(0);

  const prev = () => setActive((i) => (i - 1 + photos.length) % photos.length);
  const next = () => setActive((i) => (i + 1) % photos.length);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/70 backdrop-blur-sm p-4"
      data-testid={`room-detail-modal-${room.slug}`}
      onClick={onClose}
    >
      <div
        className="bg-paper rounded-3xl overflow-hidden shadow-paper-sm w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Photo carousel */}
        <div className="relative shrink-0">
          <img src={photos[active]} alt={`${name} ${active + 1}`} className="w-full h-64 md:h-80 object-cover" />
          <button
            type="button"
            onClick={onClose}
            data-testid={`room-detail-close-${room.slug}`}
            aria-label="Close"
            className="absolute top-3 right-3 w-9 h-9 rounded-full bg-ink/50 text-white grid place-items-center hover:bg-ink/70 transition-colors"
          >
            <i className="fa-solid fa-xmark" aria-hidden="true"></i>
          </button>
          {photos.length > 1 && (
            <>
              <button
                type="button"
                onClick={prev}
                data-testid={`room-detail-prev-${room.slug}`}
                aria-label="Previous photo"
                className="absolute left-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/80 text-teal-deep grid place-items-center hover:bg-white transition-colors"
              >
                <i className="fa-solid fa-chevron-left text-xs" aria-hidden="true"></i>
              </button>
              <button
                type="button"
                onClick={next}
                data-testid={`room-detail-next-${room.slug}`}
                aria-label="Next photo"
                className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/80 text-teal-deep grid place-items-center hover:bg-white transition-colors"
              >
                <i className="fa-solid fa-chevron-right text-xs" aria-hidden="true"></i>
              </button>
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                {photos.map((_, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setActive(i)}
                    aria-label={`Photo ${i + 1}`}
                    className={`w-1.5 h-1.5 rounded-full transition-all ${i === active ? "w-4 bg-white" : "bg-white/50"}`}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        {/* Details */}
        <div className="p-6 md:p-8 overflow-y-auto">
          <h3 className="font-display text-2xl md:text-3xl text-teal-deep">{name}</h3>
          <p className="mt-1 text-xs text-teal-deep/60">{room.capacity} · {room.size}</p>
          <p className="mt-3 text-sm text-teal-deep/75 leading-relaxed">{description}</p>

          <h4 className="mt-5 text-xs font-semibold uppercase tracking-wide text-teal-deep/60">{t("common.facilities")}</h4>
          <ul className="mt-2 flex flex-wrap gap-2">
            {(room.facilities || []).map((f) => (
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

          <div className="mt-6 flex items-end justify-between gap-4">
            <div>
              <p className="text-xs text-teal-deep/60">{t("rooms.startFrom")}</p>
              <p className="font-display text-2xl text-mustard-deep italic">{room.priceFrom}</p>
              <p className="text-[11px] text-teal-deep/60">{t("rooms.perNight")}</p>
            </div>
            <a
              href={site.bookingUrl}
              target="_blank"
              rel="noopener noreferrer"
              data-testid={`${HOME.bookNowBtn}-detail-${room.slug}`}
              className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-5 py-2.5 text-sm font-semibold shadow-paper-sm shrink-0"
            >
              {t("common.bookNow")}
              <i className="fa-solid fa-arrow-right text-[10px]" aria-hidden="true"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
