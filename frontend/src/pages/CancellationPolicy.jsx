import LegalLayout from "@/components/site/LegalLayout";
import { useContent } from "@/context/ContentContext";

export default function CancellationPolicy() {
  const { site } = useContent();
  return (
    <LegalLayout
      title="Kebijakan Pembatalan"
      description="Kebijakan pembatalan reservasi kamar di Pelangi Homestay — cara, waktu, biaya, dan no-show policy."
      breadcrumb={[{ label: "Kebijakan Pembatalan" }]}
      hero="Kami memahami bahwa rencana perjalanan dapat berubah. Berikut adalah kebijakan pembatalan yang berlaku di Pelangi Homestay."
    >
      <h2>1. Cara Pembatalan</h2>
      <p>Pembatalan reservasi dapat dilakukan melalui:</p>
      <ul>
        <li>Booking Engine resmi (melalui email konfirmasi reservasi Anda).</li>
        <li>WhatsApp resmi: <a href={`https://wa.me/${site.whatsapp}`}>{site.whatsappDisplay}</a></li>
        <li>Email: <a href={`mailto:${site.email}`}>{site.email}</a></li>
      </ul>
      <p>Sertakan <strong>kode reservasi</strong>, <strong>nama pemesan</strong>, dan <strong>alasan pembatalan</strong> saat mengajukan permintaan.</p>

      <h2>2. Waktu Pembatalan</h2>
      <ul>
        <li><strong>≥ 3 hari sebelum check-in</strong>: Pembatalan gratis, refund penuh (100%).</li>
        <li><strong>1–2 hari sebelum check-in</strong>: Dikenakan biaya sebesar 50% dari total reservasi.</li>
        <li><strong>Hari-H atau tidak hadir (no-show)</strong>: Dikenakan biaya 100% (tidak ada refund).</li>
      </ul>

      <h2>3. Biaya Pembatalan</h2>
      <p>Biaya pembatalan resmi mengikuti kebijakan Booking Engine dan Payment Gateway. Biaya administrasi payment gateway (jika ada) berada di luar tanggung jawab Pelangi Homestay dan mengikuti kebijakan penyedia layanan.</p>

      <h2>4. Kebijakan No-Show</h2>
      <p>Tamu yang tidak hadir tanpa pemberitahuan sampai dengan pukul <strong>23:59 WITA pada hari check-in</strong> akan dianggap sebagai no-show. Tidak ada refund untuk kasus no-show.</p>

      <h2>5. Perubahan Tanggal</h2>
      <p>Perubahan tanggal (reschedule) dapat diajukan minimal 3 hari sebelum check-in, tanpa biaya tambahan, sepanjang kamar tersedia pada tanggal baru dan tidak melebihi harga kamar pada periode baru. Jika terdapat selisih harga, tamu bertanggung jawab atas selisih tersebut.</p>

      <h2>6. Kondisi Khusus (Force Majeure)</h2>
      <p>Pembatalan akibat bencana alam, kondisi darurat, atau pembatasan pemerintah yang menghalangi perjalanan akan dievaluasi kasus per kasus. Silakan hubungi kami secepatnya dengan dokumen pendukung.</p>
    </LegalLayout>
  );
}
