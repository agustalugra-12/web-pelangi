// Long-form legal content (Privacy, Terms, Cancellation, Refund, House Rules,
// Payment). Kept separate from dictionary.js because it's large.
// Each entry: { title, hero, description, sections: [{h, body: [str|list]}] }
// body items can be:
//   - "string paragraph"
//   - { list: [item, ...] }  → renders <ul>
//   - { note: "string" }     → renders <p><em>italic note</em></p>

export const LEGAL_CONTENT = {
  id: {
    privacy: {
      title: "Kebijakan Privasi",
      description:
        "Kebijakan privasi Pelangi Homestay: bagaimana kami mengumpulkan, menggunakan, dan melindungi data tamu.",
      hero: "Kami menghormati privasi Anda. Halaman ini menjelaskan bagaimana Pelangi Homestay mengumpulkan, menggunakan, dan melindungi data pribadi yang Anda berikan saat menggunakan website ini atau melakukan reservasi.",
      sections: [
        {
          h: "1. Pengumpulan Data",
          body: [
            "Kami mengumpulkan data pribadi yang Anda berikan secara sukarela melalui form kontak, form reservasi (melalui Booking Engine resmi), interaksi WhatsApp, dan email. Data juga dapat dikumpulkan secara otomatis melalui cookies dan log server standar (alamat IP, jenis browser, halaman yang dikunjungi).",
          ],
        },
        {
          h: "2. Data yang Dikumpulkan",
          body: [
            {
              list: [
                "Nama lengkap",
                "Alamat email",
                "Nomor WhatsApp / telepon",
                "Tanggal check-in dan check-out",
                "Jumlah tamu (dewasa & anak)",
                "Kartu identitas saat check-in (dilihat, tidak disimpan digital)",
                "Data transaksi (dikelola oleh Payment Gateway resmi)",
              ],
            },
          ],
        },
        {
          h: "3. Cara Penggunaan Data",
          body: [
            "Data yang kami kumpulkan digunakan untuk:",
            {
              list: [
                "Memproses reservasi dan pembayaran",
                "Menghubungi tamu terkait status reservasi, konfirmasi, dan perubahan",
                "Melayani pertanyaan dan permintaan khusus",
                "Meningkatkan pengalaman menginap dan pelayanan",
                "Mengirimkan penawaran promo (hanya jika tamu memberikan persetujuan)",
                "Memenuhi kewajiban hukum yang berlaku di Indonesia",
              ],
            },
          ],
        },
        {
          h: "4. Cookies",
          body: [
            "Website kami menggunakan cookies untuk mempertahankan preferensi tampilan, melakukan analitik pengunjung, dan meningkatkan performa. Anda dapat menonaktifkan cookies melalui pengaturan browser. Menonaktifkan cookies tidak akan menghentikan reservasi, namun beberapa fitur website mungkin tidak berfungsi optimal.",
          ],
        },
        {
          h: "5. Berbagi Data dengan Pihak Ketiga",
          body: [
            "Kami tidak menjual atau menyewakan data pribadi Anda. Data hanya dibagikan kepada pihak ketiga tepercaya untuk kepentingan operasional, misalnya:",
            {
              list: [
                "Booking Engine resmi kami untuk memproses reservasi",
                "Payment Gateway resmi untuk memproses pembayaran (Tripay, Midtrans, atau penyedia serupa)",
                "Otoritas pemerintah bila diwajibkan oleh hukum",
              ],
            },
          ],
        },
        {
          h: "6. Keamanan Data",
          body: [
            "Website kami memakai koneksi HTTPS terenkripsi. Data internal disimpan dengan akses terbatas hanya untuk tim yang berwenang. Kami tidak menyimpan detail kartu kredit — pembayaran diproses langsung oleh Payment Gateway.",
          ],
        },
        {
          h: "7. Hak Pengguna",
          body: [
            "Anda berhak untuk:",
            {
              list: [
                "Meminta salinan data pribadi yang kami simpan",
                "Meminta koreksi data yang tidak akurat",
                "Meminta penghapusan data (sepanjang tidak melanggar kewajiban hukum)",
                "Menarik persetujuan penggunaan data untuk keperluan pemasaran",
              ],
            },
          ],
        },
        {
          h: "8. Perubahan Kebijakan",
          body: [
            "Kebijakan ini dapat diperbarui sewaktu-waktu. Perubahan akan dipublikasikan di halaman ini dengan tanggal pembaruan terbaru.",
          ],
        },
        { h: "9. Kontak", body: [{ contact: true }] },
      ],
      showLastUpdated: true,
    },
    terms: {
      title: "Syarat & Ketentuan",
      description:
        "Syarat dan ketentuan reservasi serta menginap di Pelangi Homestay, Bedugul, Bali.",
      hero: "Dengan melakukan reservasi di Pelangi Homestay, Anda dianggap telah membaca, memahami, dan menyetujui syarat dan ketentuan berikut.",
      sections: [
        {
          h: "1. Reservasi",
          body: [
            {
              list: [
                "Reservasi resmi dilakukan melalui Booking Engine resmi kami.",
                "Reservasi dianggap sah setelah pembayaran (down payment atau lunas) berhasil dikonfirmasi oleh sistem.",
                "Tamu wajib mengisi data lengkap dan benar saat reservasi.",
                "Kode konfirmasi reservasi wajib ditunjukkan saat check-in.",
              ],
            },
          ],
        },
        {
          h: "2. Pembayaran",
          body: [
            {
              list: [
                "Pembayaran diproses melalui Payment Gateway resmi (Tripay / Midtrans / setara).",
                "Metode yang tersedia: Transfer Bank, Virtual Account, QRIS, e-Wallet, dan Kartu Kredit/Debit (bila tersedia).",
                "Semua transaksi menggunakan koneksi terenkripsi HTTPS.",
                "Bukti pembayaran akan dikirim otomatis ke email tamu.",
              ],
            },
          ],
        },
        {
          h: "3. Check-in",
          body: [
            {
              list: [
                "Waktu check-in mulai pukul 14:00 WITA.",
                "Early check-in menyesuaikan ketersediaan kamar dan tidak dijamin.",
                "Tamu wajib menunjukkan identitas resmi (KTP / Paspor).",
                "Reception buka 07:00–22:00 WITA. Check-in di luar jam operasional harus diinformasikan sebelumnya.",
              ],
            },
          ],
        },
        {
          h: "4. Check-out",
          body: [
            {
              list: [
                "Waktu check-out paling lambat pukul 12:00 WITA.",
                "Late check-out tersedia dengan biaya tambahan dan menyesuaikan ketersediaan.",
              ],
            },
          ],
        },
        {
          h: "5. Extra Bed",
          body: [
            {
              list: [
                "Extra bed tersedia dengan biaya Rp 50.000 / malam sudah termasuk sarapan tambahan.",
                "Permintaan extra bed wajib diinformasikan sebelum kedatangan.",
              ],
            },
          ],
        },
        {
          h: "6. Kebijakan Anak",
          body: [
            {
              list: [
                "Anak di bawah 6 tahun menginap gratis tanpa extra bed.",
                "Anak 6–12 tahun dikenakan biaya extra bed sesuai ketentuan.",
                "Setiap kamar maksimal 2 dewasa + 1 anak.",
              ],
            },
          ],
        },
        {
          h: "7. Force Majeure",
          body: [
            "Pelangi Homestay tidak bertanggung jawab atas ketidaknyamanan yang diakibatkan oleh keadaan kahar (bencana alam, gangguan listrik/air dari penyedia, pandemi, tindakan pemerintah, dan sebab lain di luar kendali kami). Dalam kondisi ini, kami akan berupaya memberikan solusi terbaik.",
          ],
        },
        {
          h: "8. Perubahan Harga",
          body: [
            "Harga kamar yang ditampilkan dapat berubah sewaktu-waktu tanpa pemberitahuan sebelumnya, khususnya pada musim liburan (high season). Harga yang berlaku adalah harga pada saat reservasi dikonfirmasi.",
          ],
        },
        {
          h: "9. Hak Pelanggan",
          body: [
            {
              list: [
                "Menerima kamar sesuai deskripsi yang tercantum di website.",
                "Menerima pelayanan yang ramah dan profesional.",
                "Mengajukan komplain resmi melalui WhatsApp atau email kami.",
              ],
            },
          ],
        },
        {
          h: "10. Hak Pelangi Homestay",
          body: [
            {
              list: [
                "Menolak tamu yang terbukti melakukan kekerasan, penggunaan narkoba, atau melanggar norma hukum yang berlaku.",
                "Meminta ganti rugi atas kerusakan properti yang disebabkan oleh tamu.",
                "Memindahkan tamu ke kamar setara jika terjadi kondisi teknis mendesak.",
              ],
            },
          ],
        },
      ],
    },
    cancellation: {
      title: "Kebijakan Pembatalan",
      description:
        "Kebijakan pembatalan reservasi Pelangi Homestay: syarat, tenggat waktu, dan proses.",
      hero: "Kami memahami rencana perjalanan bisa berubah. Kebijakan pembatalan berikut berlaku untuk seluruh reservasi langsung melalui website resmi.",
      sections: [
        {
          h: "1. Tenggat Waktu Pembatalan",
          body: [
            {
              list: [
                "Pembatalan lebih dari 3 hari sebelum tanggal check-in: gratis, tanpa biaya.",
                "Pembatalan 1–3 hari sebelum tanggal check-in: dikenakan biaya sebesar 50% dari total reservasi.",
                "Pembatalan pada hari kedatangan atau no-show: dikenakan biaya sebesar 100%.",
              ],
            },
          ],
        },
        {
          h: "2. Cara Membatalkan",
          body: [
            "Pembatalan dapat dilakukan melalui salah satu kanal berikut:",
            {
              list: [
                "WhatsApp resmi kami",
                "Email resmi kami",
                "Balas email konfirmasi reservasi",
              ],
            },
            "Sertakan kode reservasi Anda saat mengajukan pembatalan.",
          ],
        },
        {
          h: "3. Reschedule (Ubah Tanggal)",
          body: [
            "Perubahan tanggal check-in dapat dilakukan gratis satu kali, minimal 3 hari sebelum tanggal check-in awal, sepanjang kamar tersedia pada tanggal baru. Selisih harga (jika ada) menjadi tanggungan tamu.",
          ],
        },
        {
          h: "4. Proses Refund",
          body: [
            "Refund akan diproses setelah pembatalan disetujui, mengikuti Kebijakan Pengembalian Dana kami.",
          ],
        },
      ],
    },
    refund: {
      title: "Kebijakan Pengembalian Dana",
      description:
        "Kebijakan pengembalian dana (refund) untuk reservasi Pelangi Homestay yang dibatalkan sesuai syarat.",
      hero: "Kebijakan berikut menjelaskan bagaimana dan kapan pengembalian dana akan diproses oleh Pelangi Homestay setelah pembatalan reservasi.",
      sections: [
        {
          h: "1. Nominal Refund",
          body: [
            "Nominal refund mengikuti Kebijakan Pembatalan:",
            {
              list: [
                "Pembatalan > 3 hari sebelum check-in: refund 100%.",
                "Pembatalan 1–3 hari sebelum check-in: refund 50%.",
                "Pembatalan pada hari check-in / no-show: tidak ada refund.",
              ],
            },
          ],
        },
        {
          h: "2. Waktu Pemrosesan",
          body: [
            "Refund diproses maksimal 7 hari kerja sejak pembatalan disetujui. Waktu penerimaan dana bergantung pada bank / Payment Gateway pengirim & penerima (biasanya 2–14 hari kerja).",
          ],
        },
        {
          h: "3. Metode Pengembalian",
          body: [
            "Refund dikembalikan ke metode pembayaran asal (bank / e-wallet / kartu kredit). Kami tidak melakukan refund lintas metode kecuali disepakati bersama.",
          ],
        },
        {
          h: "4. Potongan Biaya Payment Gateway",
          body: [
            "Biaya administrasi dari Payment Gateway (jika ada) menjadi tanggungan tamu dan tidak dikembalikan.",
          ],
        },
        {
          h: "5. Bukti Refund",
          body: [
            "Bukti pengembalian dana akan dikirim ke email tamu setelah proses selesai.",
          ],
        },
      ],
    },
    houseRules: {
      title: "Peraturan Rumah",
      description:
        "Peraturan menginap di Pelangi Homestay agar semua tamu nyaman dan aman.",
      hero: "Beberapa aturan sederhana untuk memastikan pengalaman menginap yang aman, nyaman, dan menyenangkan bagi semua tamu.",
      sections: [
        {
          h: "1. Jam Malam & Ketenangan",
          body: [
            {
              list: [
                "Jam tenang berlaku mulai pukul 22:00 hingga 07:00 WITA.",
                "Mohon menjaga volume suara di kamar dan area bersama.",
              ],
            },
          ],
        },
        {
          h: "2. Merokok",
          body: [
            {
              list: [
                "Dilarang keras merokok di dalam kamar.",
                "Merokok diperbolehkan di area outdoor yang ditentukan.",
                "Pelanggaran akan dikenakan biaya cleaning fee Rp 500.000.",
              ],
            },
          ],
        },
        {
          h: "3. Hewan Peliharaan",
          body: [
            "Pelangi Homestay tidak menerima hewan peliharaan (kecuali service animal dengan pemberitahuan sebelumnya).",
          ],
        },
        {
          h: "4. Tamu Tambahan",
          body: [
            "Tamu yang menginap harus terdaftar saat check-in. Tamu tambahan yang tidak terdaftar tidak diperbolehkan menginap.",
          ],
        },
        {
          h: "5. Kerusakan Properti",
          body: [
            "Tamu bertanggung jawab atas kerusakan yang disebabkan selama masa menginap. Biaya ganti rugi akan disesuaikan dengan tingkat kerusakan.",
          ],
        },
        {
          h: "6. Barang Berharga",
          body: [
            "Pelangi Homestay tidak bertanggung jawab atas kehilangan barang berharga. Kami menyarankan menyimpan barang berharga di tempat yang aman.",
          ],
        },
        {
          h: "7. Anak-anak",
          body: [
            "Anak-anak wajib berada dalam pengawasan orang tua sepanjang waktu, terutama di area kolam kecil, taman, dan tangga.",
          ],
        },
        {
          h: "8. Larangan",
          body: [
            {
              list: [
                "Dilarang membawa & menggunakan narkoba dalam bentuk apa pun.",
                "Dilarang membawa senjata tajam atau senjata api.",
                "Dilarang menggunakan kamar untuk aktivitas ilegal.",
              ],
            },
          ],
        },
      ],
    },
    payment: {
      title: "Informasi Pembayaran",
      description:
        "Metode pembayaran, keamanan transaksi, dan Payment Gateway resmi Pelangi Homestay.",
      hero: "Kami menerima pembayaran melalui kanal resmi menggunakan Payment Gateway terpercaya dengan koneksi terenkripsi.",
      sections: [
        {
          h: "1. Metode Pembayaran",
          body: [
            "Metode pembayaran yang tersedia melalui Payment Gateway resmi kami:",
            {
              list: [
                "Transfer Bank (BCA, Mandiri, BNI, BRI, dll.)",
                "Virtual Account seluruh bank utama",
                "QRIS (semua e-wallet & mobile banking)",
                "e-Wallet: OVO, DANA, ShopeePay, LinkAja, GoPay",
                "Kartu Kredit / Debit: Visa, Mastercard, JCB",
                "Convenience Store: Alfamart, Indomaret",
              ],
            },
          ],
        },
        {
          h: "2. Payment Gateway Resmi",
          body: [
            "Kami menggunakan Payment Gateway resmi berlisensi (Tripay / Midtrans / setara) yang telah terdaftar dan diawasi oleh otoritas terkait di Indonesia.",
          ],
        },
        {
          h: "3. Keamanan Transaksi",
          body: [
            {
              list: [
                "Semua transaksi melalui koneksi HTTPS terenkripsi.",
                "Kami tidak menyimpan detail kartu kredit atau debit Anda.",
                "Payment Gateway mengikuti standar keamanan PCI DSS.",
                "Data transaksi hanya diakses oleh tim finance yang berwenang.",
              ],
            },
          ],
        },
        {
          h: "4. Konfirmasi Pembayaran",
          body: [
            "Konfirmasi pembayaran akan dikirimkan otomatis ke email Anda setelah transaksi berhasil. Simpan bukti pembayaran ini untuk ditunjukkan saat check-in.",
          ],
        },
        {
          h: "5. Kendala Pembayaran",
          body: [
            "Jika Anda mengalami kendala saat pembayaran (transaksi ditolak, pending, atau berhasil tapi konfirmasi belum diterima), silakan hubungi kami melalui WhatsApp atau email resmi dengan menyertakan:",
            {
              list: [
                "Kode reservasi",
                "Tanggal & waktu transaksi",
                "Screenshot bukti transaksi (jika ada)",
              ],
            },
          ],
        },
        {
          h: "6. Mata Uang & Pajak",
          body: [
            "Semua harga ditampilkan dalam Rupiah (IDR) dan sudah termasuk pajak & service charge yang berlaku, kecuali disebutkan lain.",
          ],
        },
      ],
    },
  },

  en: {
    privacy: {
      title: "Privacy Policy",
      description:
        "Pelangi Homestay privacy policy: how we collect, use, and protect guest data.",
      hero: "We respect your privacy. This page explains how Pelangi Homestay collects, uses, and protects the personal data you share when using this website or making a reservation.",
      sections: [
        {
          h: "1. Data Collection",
          body: [
            "We collect personal data you provide voluntarily through the contact form, reservation form (via the official Booking Engine), WhatsApp, and email. Data may also be collected automatically through cookies and standard server logs (IP address, browser type, pages visited).",
          ],
        },
        {
          h: "2. Data We Collect",
          body: [
            {
              list: [
                "Full name",
                "Email address",
                "WhatsApp / phone number",
                "Check-in and check-out dates",
                "Number of guests (adults & children)",
                "Identity card at check-in (viewed only, not stored digitally)",
                "Transaction data (handled by the official Payment Gateway)",
              ],
            },
          ],
        },
        {
          h: "3. How We Use Your Data",
          body: [
            "The data we collect is used to:",
            {
              list: [
                "Process reservations and payments",
                "Contact guests about reservation status, confirmation, and changes",
                "Respond to questions and special requests",
                "Improve the guest experience and service",
                "Send promotional offers (only with your consent)",
                "Comply with legal obligations in Indonesia",
              ],
            },
          ],
        },
        {
          h: "4. Cookies",
          body: [
            "Our website uses cookies to remember display preferences, run visitor analytics, and improve performance. You can disable cookies in your browser settings. Disabling cookies won't stop reservations, but some website features may not work optimally.",
          ],
        },
        {
          h: "5. Sharing With Third Parties",
          body: [
            "We do not sell or rent your personal data. Data is shared only with trusted third parties for operations, such as:",
            {
              list: [
                "Our official Booking Engine to process reservations",
                "The official Payment Gateway (Tripay, Midtrans, or similar) to process payments",
                "Government authorities where required by law",
              ],
            },
          ],
        },
        {
          h: "6. Data Security",
          body: [
            "Our website uses HTTPS encryption. Internal data is stored with limited access for authorized staff only. We do not store credit card details — payments are processed directly by the Payment Gateway.",
          ],
        },
        {
          h: "7. Your Rights",
          body: [
            "You have the right to:",
            {
              list: [
                "Request a copy of the personal data we hold",
                "Request correction of inaccurate data",
                "Request deletion of data (where not restricted by law)",
                "Withdraw consent for marketing use",
              ],
            },
          ],
        },
        {
          h: "8. Policy Changes",
          body: [
            "This policy may be updated from time to time. Changes will be published on this page with the latest update date.",
          ],
        },
        { h: "9. Contact", body: [{ contact: true }] },
      ],
      showLastUpdated: true,
    },
    terms: {
      title: "Terms & Conditions",
      description:
        "Terms and conditions for booking and staying at Pelangi Homestay, Bedugul, Bali.",
      hero: "By making a reservation at Pelangi Homestay, you are considered to have read, understood, and agreed to the following terms and conditions.",
      sections: [
        {
          h: "1. Reservation",
          body: [
            {
              list: [
                "Official reservations are made through our Booking Engine.",
                "A reservation is confirmed once payment (deposit or full) is successfully verified by the system.",
                "Guests must provide complete and accurate details when booking.",
                "The reservation confirmation code must be shown at check-in.",
              ],
            },
          ],
        },
        {
          h: "2. Payment",
          body: [
            {
              list: [
                "Payments are processed via our official Payment Gateway (Tripay / Midtrans / equivalent).",
                "Available methods: Bank Transfer, Virtual Account, QRIS, e-Wallet, and Credit/Debit Card (where available).",
                "All transactions use encrypted HTTPS connections.",
                "Proof of payment is sent automatically to the guest's email.",
              ],
            },
          ],
        },
        {
          h: "3. Check-in",
          body: [
            {
              list: [
                "Check-in from 14:00 WITA.",
                "Early check-in is subject to room availability and not guaranteed.",
                "Guests must present a valid ID (ID card / Passport).",
                "Reception is open 07:00–22:00 WITA. Check-in outside these hours must be arranged in advance.",
              ],
            },
          ],
        },
        {
          h: "4. Check-out",
          body: [
            {
              list: [
                "Check-out by 12:00 WITA at the latest.",
                "Late check-out is available for an extra fee and subject to availability.",
              ],
            },
          ],
        },
        {
          h: "5. Extra Bed",
          body: [
            {
              list: [
                "Extra bed is available at Rp 50,000 / night including additional breakfast.",
                "Extra bed requests must be communicated before arrival.",
              ],
            },
          ],
        },
        {
          h: "6. Children Policy",
          body: [
            {
              list: [
                "Children under 6 stay free without an extra bed.",
                "Children 6–12 years incur an extra bed fee as per policy.",
                "Maximum occupancy per room: 2 adults + 1 child.",
              ],
            },
          ],
        },
        {
          h: "7. Force Majeure",
          body: [
            "Pelangi Homestay is not liable for inconvenience caused by force majeure (natural disasters, external electricity/water disruptions, pandemics, government actions, and other causes beyond our control). In such cases we will do our best to provide a fair solution.",
          ],
        },
        {
          h: "8. Price Changes",
          body: [
            "Displayed room rates may change at any time without prior notice, particularly during high season. The applicable rate is the one at the moment your reservation is confirmed.",
          ],
        },
        {
          h: "9. Guest Rights",
          body: [
            {
              list: [
                "Receive a room matching the description on our website.",
                "Receive friendly and professional service.",
                "Submit official complaints via our WhatsApp or email.",
              ],
            },
          ],
        },
        {
          h: "10. Pelangi Homestay's Rights",
          body: [
            {
              list: [
                "Refuse guests found engaging in violence, drug use, or breaking applicable laws.",
                "Request compensation for property damage caused by guests.",
                "Relocate guests to an equivalent room in urgent technical situations.",
              ],
            },
          ],
        },
      ],
    },
    cancellation: {
      title: "Cancellation Policy",
      description:
        "Pelangi Homestay cancellation policy: terms, deadlines, and process.",
      hero: "We know travel plans can change. The following cancellation policy applies to all direct reservations made through our official website.",
      sections: [
        {
          h: "1. Cancellation Deadlines",
          body: [
            {
              list: [
                "Cancellations more than 3 days before check-in: free of charge.",
                "Cancellations 1–3 days before check-in: 50% of the total reservation is charged.",
                "Same-day cancellation or no-show: 100% is charged.",
              ],
            },
          ],
        },
        {
          h: "2. How to Cancel",
          body: [
            "Cancellations can be made through one of these channels:",
            {
              list: [
                "Our official WhatsApp",
                "Our official email",
                "Reply to the reservation confirmation email",
              ],
            },
            "Please include your reservation code when requesting a cancellation.",
          ],
        },
        {
          h: "3. Reschedule (Change of Dates)",
          body: [
            "Check-in date changes can be made free of charge once, at least 3 days before the original check-in, subject to availability on the new date. Any rate difference is the guest's responsibility.",
          ],
        },
        {
          h: "4. Refund Process",
          body: [
            "Refunds are processed once a cancellation is approved, following our Refund Policy.",
          ],
        },
      ],
    },
    refund: {
      title: "Refund Policy",
      description:
        "Refund policy for Pelangi Homestay reservations cancelled under our terms.",
      hero: "The following policy explains how and when refunds are processed by Pelangi Homestay after a reservation is cancelled.",
      sections: [
        {
          h: "1. Refund Amount",
          body: [
            "Refund amounts follow our Cancellation Policy:",
            {
              list: [
                "Cancellation > 3 days before check-in: 100% refund.",
                "Cancellation 1–3 days before check-in: 50% refund.",
                "Same-day cancellation / no-show: no refund.",
              ],
            },
          ],
        },
        {
          h: "2. Processing Time",
          body: [
            "Refunds are processed within a maximum of 7 working days after approval. The time to receive funds depends on the sending and receiving bank / Payment Gateway (typically 2–14 working days).",
          ],
        },
        {
          h: "3. Refund Method",
          body: [
            "Refunds are returned to the original payment method (bank / e-wallet / credit card). We do not refund cross-method unless mutually agreed.",
          ],
        },
        {
          h: "4. Payment Gateway Fees",
          body: [
            "Payment Gateway administrative fees (if any) are the guest's responsibility and are non-refundable.",
          ],
        },
        {
          h: "5. Refund Proof",
          body: [
            "Proof of refund will be sent to the guest's email once processing is complete.",
          ],
        },
      ],
    },
    houseRules: {
      title: "House Rules",
      description:
        "House rules at Pelangi Homestay so every guest feels safe and comfortable.",
      hero: "A few simple rules to make sure every guest enjoys a safe, comfortable, and pleasant stay.",
      sections: [
        {
          h: "1. Quiet Hours",
          body: [
            {
              list: [
                "Quiet hours are from 22:00 to 07:00 WITA.",
                "Please keep noise low in rooms and shared areas.",
              ],
            },
          ],
        },
        {
          h: "2. Smoking",
          body: [
            {
              list: [
                "Smoking is strictly prohibited inside rooms.",
                "Smoking is allowed in designated outdoor areas.",
                "Violations incur a Rp 500,000 cleaning fee.",
              ],
            },
          ],
        },
        {
          h: "3. Pets",
          body: [
            "Pelangi Homestay does not accept pets (except service animals with prior notice).",
          ],
        },
        {
          h: "4. Additional Guests",
          body: [
            "All overnight guests must be registered at check-in. Unregistered additional guests are not permitted to stay.",
          ],
        },
        {
          h: "5. Property Damage",
          body: [
            "Guests are responsible for any damage caused during their stay. Compensation will be based on the extent of the damage.",
          ],
        },
        {
          h: "6. Valuables",
          body: [
            "Pelangi Homestay is not liable for loss of valuables. We recommend keeping valuables in a secure place.",
          ],
        },
        {
          h: "7. Children",
          body: [
            "Children must be supervised at all times, especially around the small pool, garden, and stairs.",
          ],
        },
        {
          h: "8. Prohibited",
          body: [
            {
              list: [
                "Bringing or using drugs in any form is prohibited.",
                "Bringing sharp weapons or firearms is prohibited.",
                "Using rooms for illegal activities is prohibited.",
              ],
            },
          ],
        },
      ],
    },
    payment: {
      title: "Payment Information",
      description:
        "Payment methods, transaction security, and the official Pelangi Homestay Payment Gateway.",
      hero: "We accept payments through official channels using a trusted Payment Gateway with an encrypted connection.",
      sections: [
        {
          h: "1. Payment Methods",
          body: [
            "Payment methods available through our official Payment Gateway:",
            {
              list: [
                "Bank Transfer (BCA, Mandiri, BNI, BRI, etc.)",
                "Virtual Accounts for all major banks",
                "QRIS (all e-wallets & mobile banking)",
                "e-Wallet: OVO, DANA, ShopeePay, LinkAja, GoPay",
                "Credit / Debit Card: Visa, Mastercard, JCB",
                "Convenience Store: Alfamart, Indomaret",
              ],
            },
          ],
        },
        {
          h: "2. Official Payment Gateway",
          body: [
            "We use licensed official Payment Gateways (Tripay / Midtrans / equivalent) registered and supervised by the relevant authorities in Indonesia.",
          ],
        },
        {
          h: "3. Transaction Security",
          body: [
            {
              list: [
                "All transactions use encrypted HTTPS connections.",
                "We do not store your credit or debit card details.",
                "Our Payment Gateway follows PCI DSS security standards.",
                "Transaction data is only accessed by our authorized finance team.",
              ],
            },
          ],
        },
        {
          h: "4. Payment Confirmation",
          body: [
            "Payment confirmation is sent automatically to your email once the transaction succeeds. Please keep it to show at check-in.",
          ],
        },
        {
          h: "5. Payment Issues",
          body: [
            "If you experience issues during payment (rejected, pending, or successful but no confirmation received), please contact us via WhatsApp or our official email, including:",
            {
              list: [
                "Reservation code",
                "Date & time of transaction",
                "Screenshot of the transaction receipt (if any)",
              ],
            },
          ],
        },
        {
          h: "6. Currency & Tax",
          body: [
            "All prices are shown in Indonesian Rupiah (IDR) and include applicable tax & service charges unless otherwise stated.",
          ],
        },
      ],
    },
  },
};
