import LegalLayout from "@/components/site/LegalLayout";
import { useContent } from "@/context/ContentContext";

export default function RefundPolicy() {
  const { site } = useContent();
  return (
    <LegalLayout
      title="Kebijakan Refund"
      description="Kebijakan pengembalian dana (refund) atas reservasi kamar di Pelangi Homestay."
      breadcrumb={[{ label: "Kebijakan Refund" }]}
      hero="Refund merupakan pengembalian dana atas reservasi yang dibatalkan sesuai ketentuan yang berlaku."
    >
      <h2>1. Prinsip Refund</h2>
      <ul>
        <li>Refund hanya berlaku untuk pembatalan yang memenuhi ketentuan pada <a href="/cancellation-policy">Kebijakan Pembatalan</a>.</li>
        <li>Refund tidak berlaku untuk kasus no-show, over-stay, atau ketidakpuasan yang tidak dapat diverifikasi.</li>
        <li>Refund diberikan sesuai dengan nominal yang tercantum di kebijakan pembatalan (100%, 50%, atau 0%).</li>
      </ul>

      <h2>2. Metode Refund</h2>
      <p>Refund akan diproses menggunakan metode pembayaran yang sama dengan saat reservasi. Contoh:</p>
      <ul>
        <li>Pembayaran via <strong>Transfer Bank / Virtual Account</strong> → refund dikembalikan ke rekening bank yang digunakan.</li>
        <li>Pembayaran via <strong>QRIS / e-Wallet</strong> → refund dikembalikan ke saldo dompet digital terkait.</li>
        <li>Pembayaran via <strong>Kartu Kredit / Debit</strong> → refund dikembalikan sebagai reverse-charge ke kartu yang bersangkutan.</li>
      </ul>

      <h2>3. Estimasi Waktu Refund</h2>
      <ul>
        <li><strong>Transfer Bank / Virtual Account</strong>: 3 – 7 hari kerja setelah permintaan disetujui.</li>
        <li><strong>QRIS / e-Wallet</strong>: 1 – 3 hari kerja.</li>
        <li><strong>Kartu Kredit / Debit</strong>: 7 – 14 hari kerja (mengikuti kebijakan penerbit kartu).</li>
      </ul>
      <p>Waktu proses dihitung setelah dokumen dan verifikasi permintaan refund lengkap.</p>

      <h2>4. Biaya Administrasi Payment Gateway</h2>
      <p>Sebagian metode pembayaran dikenakan biaya administrasi oleh Payment Gateway atau bank penerbit. Biaya ini <strong>tidak</strong> dikembalikan karena berada di luar tanggung jawab Pelangi Homestay dan mengikuti ketentuan penyedia layanan pembayaran.</p>

      <h2>5. Cara Mengajukan Refund</h2>
      <p>Ajukan permintaan refund dengan menyertakan:</p>
      <ul>
        <li>Kode reservasi</li>
        <li>Nama pemesan</li>
        <li>Bukti pembayaran</li>
        <li>Nomor rekening tujuan / detail metode refund</li>
      </ul>
      <p>Kirimkan ke <a href={`mailto:${site.email}`}>{site.email}</a> atau <a href={`https://wa.me/${site.whatsapp}`}>{site.whatsappDisplay}</a>.</p>

      <h2>6. Refund Tidak Berlaku Untuk</h2>
      <ul>
        <li>No-show tanpa pemberitahuan.</li>
        <li>Early check-out (tamu meninggalkan lebih cepat dari tanggal check-out).</li>
        <li>Ketidakpuasan yang tidak dapat diverifikasi oleh manajemen.</li>
        <li>Kerusakan atau denda yang menjadi tanggung jawab tamu.</li>
      </ul>
    </LegalLayout>
  );
}
