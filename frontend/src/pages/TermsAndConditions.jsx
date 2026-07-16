import LegalLayout from "@/components/site/LegalLayout";
import { useContent } from "@/context/ContentContext";

export default function TermsAndConditions() {
  const { site } = useContent();
  return (
    <LegalLayout
      title="Syarat & Ketentuan"
      description="Syarat dan ketentuan reservasi serta menginap di Pelangi Homestay, Bedugul, Bali."
      breadcrumb={[{ label: "Syarat & Ketentuan" }]}
      hero="Dengan melakukan reservasi di Pelangi Homestay, Anda dianggap telah membaca, memahami, dan menyetujui syarat dan ketentuan berikut."
    >
      <h2>1. Reservasi</h2>
      <ul>
        <li>Reservasi resmi dilakukan melalui Booking Engine di <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer">{site.bookingUrl}</a>.</li>
        <li>Reservasi dianggap sah setelah pembayaran (down payment atau lunas) berhasil dikonfirmasi oleh sistem.</li>
        <li>Tamu wajib mengisi data lengkap dan benar saat reservasi.</li>
        <li>Kode konfirmasi reservasi wajib ditunjukkan saat check-in.</li>
      </ul>

      <h2>2. Pembayaran</h2>
      <ul>
        <li>Pembayaran diproses melalui Payment Gateway resmi (Tripay / Midtrans / setara).</li>
        <li>Metode yang tersedia: Transfer Bank, Virtual Account, QRIS, e-Wallet, dan Kartu Kredit/Debit (bila tersedia).</li>
        <li>Semua transaksi menggunakan koneksi terenkripsi HTTPS.</li>
        <li>Bukti pembayaran akan dikirim otomatis ke email tamu.</li>
      </ul>

      <h2>3. Check-in</h2>
      <ul>
        <li>Waktu check-in mulai pukul 14:00 WITA.</li>
        <li>Early check-in menyesuaikan ketersediaan kamar dan tidak dijamin.</li>
        <li>Tamu wajib menunjukkan identitas resmi (KTP / Paspor).</li>
        <li>Reception buka 07:00–22:00 WITA. Check-in di luar jam operasional harus diinformasikan sebelumnya.</li>
      </ul>

      <h2>4. Check-out</h2>
      <ul>
        <li>Waktu check-out paling lambat pukul 12:00 WITA.</li>
        <li>Late check-out tersedia dengan biaya tambahan dan menyesuaikan ketersediaan.</li>
      </ul>

      <h2>5. Extra Bed</h2>
      <ul>
        <li>Extra bed tersedia dengan biaya Rp 50.000 / malam sudah termasuk sarapan tambahan.</li>
        <li>Permintaan extra bed wajib diinformasikan sebelum kedatangan.</li>
      </ul>

      <h2>6. Kebijakan Anak</h2>
      <ul>
        <li>Anak di bawah 6 tahun menginap gratis tanpa extra bed.</li>
        <li>Anak 6–12 tahun dikenakan biaya extra bed sesuai ketentuan.</li>
        <li>Setiap kamar maksimal 2 dewasa + 1 anak.</li>
      </ul>

      <h2>7. Force Majeure</h2>
      <p>Pelangi Homestay tidak bertanggung jawab atas ketidaknyamanan yang diakibatkan oleh keadaan kahar (bencana alam, gangguan listrik/air dari penyedia, pandemi, tindakan pemerintah, dan sebab lain di luar kendali kami). Dalam kondisi ini, kami akan berupaya memberikan solusi terbaik.</p>

      <h2>8. Perubahan Harga</h2>
      <p>Harga kamar yang ditampilkan dapat berubah sewaktu-waktu tanpa pemberitahuan sebelumnya, khususnya pada musim liburan (high season). Harga yang berlaku adalah harga pada saat reservasi dikonfirmasi.</p>

      <h2>9. Hak Pelanggan</h2>
      <ul>
        <li>Menerima kamar sesuai deskripsi yang tercantum di website.</li>
        <li>Menerima pelayanan yang ramah dan profesional.</li>
        <li>Mengajukan komplain resmi melalui WhatsApp {site.whatsappDisplay} atau email {site.email}.</li>
      </ul>

      <h2>10. Hak Pelangi Homestay</h2>
      <ul>
        <li>Menolak tamu yang terbukti melakukan kekerasan, penggunaan narkoba, atau melanggar norma hukum yang berlaku.</li>
        <li>Meminta ganti rugi atas kerusakan properti yang disebabkan oleh tamu.</li>
        <li>Memindahkan tamu ke kamar setara jika terjadi kondisi teknis mendesak.</li>
      </ul>
    </LegalLayout>
  );
}
