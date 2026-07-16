import LegalLayout from "@/components/site/LegalLayout";
import { useContent } from "@/context/ContentContext";

export default function PaymentInformation() {
  const { site } = useContent();
  return (
    <LegalLayout
      title="Informasi Pembayaran"
      eyebrow="Payment"
      description="Metode pembayaran resmi untuk reservasi kamar Pelangi Homestay — Transfer Bank, QRIS, Virtual Account, e-Wallet, Kartu Kredit."
      breadcrumb={[{ label: "Informasi Pembayaran" }]}
      hero="Kami menerima berbagai metode pembayaran melalui Payment Gateway resmi untuk memastikan setiap transaksi berjalan aman, cepat, dan transparan."
    >
      <h2>1. Alur Reservasi & Pembayaran</h2>
      <ol>
        <li>Tamu melakukan pemesanan melalui <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer">Booking Engine resmi</a> di website kami.</li>
        <li>Setelah memilih kamar dan tanggal, tamu diarahkan ke halaman pembayaran yang aman (HTTPS) yang dikelola oleh Payment Gateway resmi.</li>
        <li>Tamu memilih metode pembayaran yang diinginkan.</li>
        <li>Setelah pembayaran sukses, sistem mengirimkan konfirmasi otomatis via email berikut kode reservasi.</li>
        <li>Tunjukkan kode reservasi saat check-in.</li>
      </ol>

      <h2>2. Metode Pembayaran</h2>
      <p>Metode pembayaran yang tersedia (menyesuaikan dukungan Payment Gateway saat transaksi):</p>
      <ul>
        <li><strong>Transfer Bank</strong> — BCA, BNI, Mandiri, BRI, dan bank utama lainnya.</li>
        <li><strong>Virtual Account (VA)</strong> — pembayaran instan dengan nomor VA unik per transaksi.</li>
        <li><strong>QRIS</strong> — scan-and-pay yang mendukung semua e-Wallet dan mobile banking di Indonesia.</li>
        <li><strong>e-Wallet</strong> — GoPay, OVO, DANA, ShopeePay, LinkAja (mengikuti ketersediaan).</li>
        <li><strong>Kartu Kredit / Debit</strong> — Visa, Mastercard, JCB (jika didukung oleh gateway aktif).</li>
        <li><strong>Retail Outlet</strong> — Indomaret / Alfamart untuk pembayaran tunai (jika didukung).</li>
      </ul>

      <h2>3. Payment Gateway Resmi</h2>
      <p>Kami hanya menerima pembayaran melalui Payment Gateway resmi yang berlisensi di Indonesia (misal: Tripay, Midtrans, Xendit, DOKU, atau Duitku). Kami <strong>tidak</strong> menerima transfer langsung ke rekening pribadi karyawan atau pihak yang tidak berwenang.</p>
      <p>Bila Anda menerima permintaan pembayaran di luar Booking Engine resmi kami, harap segera laporkan ke <a href={`mailto:${site.email}`}>{site.email}</a>.</p>

      <h2>4. Keamanan Transaksi</h2>
      <ul>
        <li>Seluruh transaksi menggunakan koneksi terenkripsi <strong>HTTPS/TLS</strong>.</li>
        <li>Data kartu kredit/debit <strong>tidak</strong> disimpan di server Pelangi Homestay. Data tersebut ditangani langsung oleh Payment Gateway yang telah bersertifikat PCI DSS.</li>
        <li>Payment Gateway menerapkan protokol 3-D Secure (3DS) untuk transaksi kartu.</li>
      </ul>

      <h2>5. Konfirmasi Pembayaran</h2>
      <p>Konfirmasi pembayaran akan dikirimkan otomatis via email dalam beberapa menit setelah transaksi berhasil. Jika Anda belum menerima konfirmasi dalam 1 jam, silakan hubungi:</p>
      <ul>
        <li>WhatsApp: <a href={`https://wa.me/${site.whatsapp}`}>{site.whatsappDisplay}</a></li>
        <li>Email: <a href={`mailto:${site.email}`}>{site.email}</a></li>
      </ul>

      <h2>6. Mata Uang & Pajak</h2>
      <p>Semua harga ditampilkan dalam <strong>Rupiah (IDR)</strong> dan sudah termasuk pajak dan biaya layanan yang berlaku. Rincian pajak/biaya dapat dilihat pada halaman ringkasan reservasi sebelum pembayaran diproses.</p>

      <h2>7. Refund</h2>
      <p>Kebijakan pengembalian dana atas reservasi yang dibatalkan diatur pada halaman <a href="/refund-policy">Kebijakan Refund</a>.</p>
    </LegalLayout>
  );
}
