import LegalLayout from "@/components/site/LegalLayout";

export default function HouseRules() {
  return (
    <LegalLayout
      title="Aturan Menginap"
      description="Aturan menginap (house rules) di Pelangi Homestay untuk kenyamanan bersama seluruh tamu."
      breadcrumb={[{ label: "House Rules" }]}
      hero="Untuk menjaga kenyamanan seluruh tamu dan kelestarian penginapan, kami memiliki beberapa aturan menginap yang wajib diikuti."
    >
      <h2>1. Check-in</h2>
      <ul>
        <li>Waktu check-in: mulai 14:00 WITA.</li>
        <li>Tamu wajib menunjukkan identitas resmi (KTP / Paspor).</li>
        <li>Reception buka 07:00–22:00 WITA.</li>
      </ul>

      <h2>2. Check-out</h2>
      <ul>
        <li>Waktu check-out: paling lambat 12:00 WITA.</li>
        <li>Late check-out dikenakan biaya menyesuaikan tarif kamar.</li>
      </ul>

      <h2>3. Kebijakan Merokok</h2>
      <ul>
        <li>Merokok <strong>tidak diperkenankan</strong> di dalam kamar.</li>
        <li>Merokok hanya diperbolehkan di area terbuka yang telah disediakan (teras, taman).</li>
        <li>Pelanggaran dikenakan denda pembersihan sebesar Rp 500.000.</li>
      </ul>

      <h2>4. Kebijakan Kebisingan</h2>
      <ul>
        <li>Jam tenang: 22:00 – 06:00 WITA.</li>
        <li>Musik dan suara keras di luar jam tersebut wajib diredam agar tidak mengganggu tamu lain.</li>
        <li>Pesta atau pertemuan besar tidak diperkenankan tanpa persetujuan sebelumnya.</li>
      </ul>

      <h2>5. Kebijakan Hewan Peliharaan</h2>
      <p>Hewan peliharaan <strong>tidak diperbolehkan</strong> menginap di kamar, kecuali telah mendapat persetujuan tertulis dari manajemen sebelum reservasi.</p>

      <h2>6. Kebijakan Tamu Kunjungan (Visitor)</h2>
      <ul>
        <li>Tamu kunjungan hanya diperbolehkan di area lobby dan taman.</li>
        <li>Tamu kunjungan yang menginap di kamar wajib melapor ke reception dan dikenakan biaya tambahan sesuai kapasitas kamar.</li>
        <li>Kunjungan setelah pukul 22:00 WITA tidak diperkenankan.</li>
      </ul>

      <h2>7. Kebijakan Kerusakan (Damage Policy)</h2>
      <p>Kerusakan atau kehilangan properti kamar (furniture, elektronik, perlengkapan mandi, dsb.) yang disebabkan oleh tamu akan dibebankan biaya penggantian sesuai nilai kerusakan.</p>

      <h2>8. Barang Hilang / Tertinggal</h2>
      <ul>
        <li>Kami tidak bertanggung jawab atas kehilangan barang berharga yang tidak disimpan di brankas atau tempat aman.</li>
        <li>Barang tertinggal akan disimpan maksimal 30 hari.</li>
        <li>Pengiriman barang tertinggal (jika diminta) dibebankan kepada tamu.</li>
      </ul>

      <h2>9. Keamanan & Kebakaran</h2>
      <ul>
        <li>Dilarang menyalakan api terbuka (lilin, kompor portable) di dalam kamar.</li>
        <li>Ikuti rambu evakuasi jika terjadi keadaan darurat.</li>
      </ul>

      <h2>10. Etika Umum</h2>
      <ul>
        <li>Hormati staff, tamu lain, dan lingkungan sekitar.</li>
        <li>Buang sampah pada tempatnya. Kami mendorong penggunaan botol minum reusable.</li>
        <li>Manajemen berhak menolak atau mengeluarkan tamu yang melanggar aturan tanpa refund.</li>
      </ul>
    </LegalLayout>
  );
}
