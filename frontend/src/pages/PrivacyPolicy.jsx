import LegalLayout from "@/components/site/LegalLayout";
import { useContent } from "@/context/ContentContext";

export default function PrivacyPolicy() {
  const { site } = useContent();
  return (
    <LegalLayout
      title="Kebijakan Privasi"
      description="Kebijakan privasi Pelangi Homestay: bagaimana kami mengumpulkan, menggunakan, dan melindungi data tamu."
      breadcrumb={[{ label: "Kebijakan Privasi" }]}
      hero="Kami menghormati privasi Anda. Halaman ini menjelaskan bagaimana Pelangi Homestay mengumpulkan, menggunakan, dan melindungi data pribadi yang Anda berikan saat menggunakan website ini atau melakukan reservasi."
    >
      <p><em>Terakhir diperbarui: {new Date().toLocaleDateString("id-ID", { year: "numeric", month: "long" })}.</em></p>

      <h2>1. Pengumpulan Data</h2>
      <p>Kami mengumpulkan data pribadi yang Anda berikan secara sukarela melalui form kontak, form reservasi (melalui Booking Engine resmi), interaksi WhatsApp, dan email. Data juga dapat dikumpulkan secara otomatis melalui cookies dan log server standar (alamat IP, jenis browser, halaman yang dikunjungi).</p>

      <h2>2. Data yang Dikumpulkan</h2>
      <ul>
        <li>Nama lengkap</li>
        <li>Alamat email</li>
        <li>Nomor WhatsApp / telepon</li>
        <li>Tanggal check-in dan check-out</li>
        <li>Jumlah tamu (dewasa & anak)</li>
        <li>Kartu identitas saat check-in (dilihat, tidak disimpan digital)</li>
        <li>Data transaksi (dikelola oleh Payment Gateway resmi)</li>
      </ul>

      <h2>3. Cara Penggunaan Data</h2>
      <p>Data yang kami kumpulkan digunakan untuk:</p>
      <ul>
        <li>Memproses reservasi dan pembayaran</li>
        <li>Menghubungi tamu terkait status reservasi, konfirmasi, dan perubahan</li>
        <li>Melayani pertanyaan dan permintaan khusus</li>
        <li>Meningkatkan pengalaman menginap dan pelayanan</li>
        <li>Mengirimkan penawaran promo (hanya jika tamu memberikan persetujuan)</li>
        <li>Memenuhi kewajiban hukum yang berlaku di Indonesia</li>
      </ul>

      <h2>4. Cookies</h2>
      <p>Website kami menggunakan cookies untuk mempertahankan preferensi tampilan, melakukan analitik pengunjung, dan meningkatkan performa. Anda dapat menonaktifkan cookies melalui pengaturan browser. Menonaktifkan cookies tidak akan menghentikan reservasi, namun beberapa fitur website mungkin tidak berfungsi optimal.</p>

      <h2>5. Berbagi Data dengan Pihak Ketiga</h2>
      <p>Kami tidak menjual atau menyewakan data pribadi Anda. Data hanya dibagikan kepada pihak ketiga tepercaya untuk kepentingan operasional, misalnya:</p>
      <ul>
        <li>Booking Engine resmi kami untuk memproses reservasi</li>
        <li>Payment Gateway resmi untuk memproses pembayaran (Tripay, Midtrans, atau penyedia serupa)</li>
        <li>Otoritas pemerintah bila diwajibkan oleh hukum</li>
      </ul>

      <h2>6. Keamanan Data</h2>
      <p>Website kami memakai koneksi HTTPS terenkripsi. Data internal disimpan dengan akses terbatas hanya untuk tim yang berwenang. Kami tidak menyimpan detail kartu kredit — pembayaran diproses langsung oleh Payment Gateway.</p>

      <h2>7. Hak Pengguna</h2>
      <p>Anda berhak untuk:</p>
      <ul>
        <li>Meminta salinan data pribadi yang kami simpan</li>
        <li>Meminta koreksi data yang tidak akurat</li>
        <li>Meminta penghapusan data (sepanjang tidak melanggar kewajiban hukum)</li>
        <li>Menarik persetujuan penggunaan data untuk keperluan pemasaran</li>
      </ul>

      <h2>8. Perubahan Kebijakan</h2>
      <p>Kebijakan ini dapat diperbarui sewaktu-waktu. Perubahan akan dipublikasikan di halaman ini dengan tanggal pembaruan terbaru.</p>

      <h2>9. Kontak</h2>
      <p>Untuk pertanyaan terkait privasi data, silakan hubungi kami di:</p>
      <ul>
        <li>Email: <a href={`mailto:${site.email}`}>{site.email}</a></li>
        <li>WhatsApp: <a href={`https://wa.me/${site.whatsapp}`}>{site.whatsappDisplay}</a></li>
        <li>Alamat: {site.address}</li>
      </ul>
    </LegalLayout>
  );
}
