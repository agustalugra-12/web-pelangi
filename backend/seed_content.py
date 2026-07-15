"""Default seed content for Pelangi Homestay CMS.
   Mirrors frontend/src/data/content.js so pages have data on first boot.
"""

DEFAULT_ROOMS = [
    {
        "id": "standard",
        "slug": "standard",
        "name": "Standard Room",
        "capacity": "2 Dewasa + 1 Anak",
        "size": "3 × 3 m",
        "priceFrom": "IDR 175.000",
        "image": "/assets/std-5.webp",
        "gallery": [
            "/assets/std-5.webp", "/assets/std-4.webp",
            "/assets/std-3.webp", "/assets/std-2.webp", "/assets/std-1.webp",
        ],
        "facilities": ["Double Bed", "Air Panas", "Smart TV", "WiFi", "Teras Pribadi", "Breakfast"],
        "description": "Kamar hangat dan efisien untuk berdua, dengan teras pribadi, kamar mandi bersih, dan sarapan hangat sudah termasuk.",
    },
    {
        "id": "cottage",
        "slug": "cottage",
        "name": "Cottage",
        "capacity": "2 Dewasa + 1 Anak",
        "size": "5 × 3,5 m",
        "priceFrom": "IDR 225.000",
        "image": "/assets/cot-2.webp",
        "gallery": [
            "/assets/cot-2.webp", "/assets/cot-4.webp",
            "/assets/cot-3.webp", "/assets/cot-1.webp", "/assets/cot-5.webp",
        ],
        "facilities": ["Double Bed", "Air Panas", "Smart TV", "WiFi", "Teras Pribadi", "Breakfast"],
        "description": "Fasilitas identik dengan Standard Room, namun jauh lebih lapang — 5 × 3,5 m dengan teras luas untuk keluarga kecil atau honeymoon yang butuh ruang bernapas lebih.",
    },
]

DEFAULT_MENU = [
    {"id": "m1", "name": "Nasi Goreng", "desc": "Nasi goreng khas rumahan, gurih dengan telur mata sapi dan kerupuk.", "price": "IDR 30k"},
    {"id": "m2", "name": "Mie Instan", "desc": "Mie instan panas yang tidak pernah salah, sempurna untuk pagi berkabut.", "price": "IDR 15k"},
    {"id": "m3", "name": "Sosis Bakar", "desc": "Sosis panggang saus khas, disajikan dengan saus sambal & mayo.", "price": "IDR 20k"},
    {"id": "m4", "name": "Kentang Goreng", "desc": "Kentang goreng crispy dengan bumbu keju atau sambal manis.", "price": "IDR 20k"},
    {"id": "m5", "name": "Kopi Hitam", "desc": "Kopi hitam single origin dari perkebunan sekitar Bedugul.", "price": "IDR 10k"},
]

DEFAULT_GALLERY = [
    {"id": "g1", "category": "Standard Room", "src": "/assets/std-5.webp"},
    {"id": "g2", "category": "Standard Room", "src": "/assets/std-4.webp"},
    {"id": "g3", "category": "Standard Room", "src": "/assets/std-3.webp"},
    {"id": "g4", "category": "Standard Room", "src": "/assets/std-2.webp"},
    {"id": "g5", "category": "Cottage", "src": "/assets/cot-2.webp"},
    {"id": "g6", "category": "Cottage", "src": "/assets/cot-4.webp"},
    {"id": "g7", "category": "Cottage", "src": "/assets/cot-3.webp"},
    {"id": "g8", "category": "Cottage", "src": "/assets/cot-1.webp"},
    {"id": "g9", "category": "Bathroom", "src": "/assets/std-1.webp"},
    {"id": "g10", "category": "Bathroom", "src": "/assets/cot-5.webp"},
    {"id": "g11", "category": "Restaurant", "src": "/assets/restaurant.jpg"},
    {"id": "g12", "category": "Garden", "src": "/assets/garden.jpg"},
    {"id": "g13", "category": "Lobby", "src": "/assets/signage.jpg"},
    {"id": "g14", "category": "Lobby", "src": "/assets/facade.jpg"},
    {"id": "g15", "category": "View", "src": "/assets/ulun-danu.webp"},
    {"id": "g16", "category": "View", "src": "/assets/danau-beratan.webp"},
    {"id": "g17", "category": "View", "src": "/assets/handara-gate.webp"},
]

DEFAULT_ATTRACTIONS = [
    {"id": "a1", "title": "Pura Ulun Danu Beratan", "distance": "5 menit", "image": "/assets/ulun-danu.webp", "desc": "Ikon Bedugul — pura di atas danau yang tampak melayang saat air pasang."},
    {"id": "a2", "title": "Kebun Raya Bali", "distance": "8 menit", "image": "/assets/kebun-raya.webp", "desc": "Kebun raya luas dengan ribuan koleksi tanaman tropis dataran tinggi."},
    {"id": "a3", "title": "Danau Beratan", "distance": "5 menit", "image": "/assets/danau-beratan.webp", "desc": "Berperahu, memancing, atau sekadar menikmati sunrise berkabut."},
    {"id": "a4", "title": "Pasar Candikuning", "distance": "6 menit", "image": "/assets/pasar-candikuning.webp", "desc": "Strawberry segar, sayur mayur, dan oleh-oleh khas dataran tinggi."},
    {"id": "a5", "title": "Handara Gate", "distance": "12 menit", "image": "/assets/handara-gate.webp", "desc": "Gerbang ikonik untuk foto klasik ala Bali dataran tinggi."},
]

DEFAULT_FAQS = [
    {"id": "f1", "q": "Jam berapa Check-in dan Check-out?", "a": "Check-in mulai pukul 14:00 WITA, Check-out paling lambat 12:00 WITA. Early check-in menyesuaikan ketersediaan kamar."},
    {"id": "f2", "q": "Apakah breakfast sudah termasuk?", "a": "Ya, breakfast lokal untuk 2 orang sudah termasuk untuk semua tipe kamar."},
    {"id": "f3", "q": "Apakah anak-anak diperbolehkan?", "a": "Tentu. Anak di bawah 6 tahun gratis (tanpa extra bed). Extra bed tersedia untuk anak 6–12 tahun dengan biaya tambahan."},
    {"id": "f4", "q": "Berapa biaya Extra Bed?", "a": "Rp 50.000 per malam sudah termasuk sarapan tambahan."},
    {"id": "f5", "q": "Bagaimana kebijakan pembatalan?", "a": "Pembatalan gratis hingga 3 hari sebelum tanggal check-in. Setelah itu berlaku ketentuan booking engine terkait."},
    {"id": "f6", "q": "Metode pembayaran apa saja?", "a": "Semua kartu kredit utama, transfer bank Indonesia, QRIS, dan pembayaran on-site (tunai)."},
    {"id": "f7", "q": "Apakah tersedia parkir?", "a": "Ya, parkir mobil dan motor tersedia gratis untuk tamu."},
]

DEFAULT_TESTIMONIALS = [
    {"id": "t1", "name": "Rina & Aldo", "origin": "Jakarta", "text": "Kamarnya wangi, kasurnya empuk, dan sarapannya bikin susah move on. Bakal balik lagi tahun depan!"},
    {"id": "t2", "name": "Sarah", "origin": "Melbourne, AU", "text": "The most peaceful morning I've had in months. The staff went above and beyond for us."},
    {"id": "t3", "name": "Keluarga Wibowo", "origin": "Surabaya", "text": "Cottage-nya luas, anak-anak betah main di taman. Lokasinya sangat strategis ke Kebun Raya."},
    {"id": "t4", "name": "Bagas", "origin": "Bandung", "text": "Value for money-nya juara. Sunset di balkon, kopi hangat — nggak butuh liburan yang mahal."},
]

DEFAULT_SITE = {
    "brand": "Pelangi Homestay",
    "tagline": "Rumah hangat di jantung Bedugul",
    "address": "Bedugul, Baturiti, Tabanan, Bali 82191",
    "whatsappDisplay": "0851-1945-9269",
    "whatsapp": "6285119459269",
    "email": "pelangihomestay9@gmail.com",
    "hours": "Reception 07:00 – 22:00 WITA",
    "bookingUrl": "https://pelangihomestay.com/book",
    "mapEmbed": "https://www.google.com/maps?q=Bedugul,%20Bali&t=&z=13&ie=UTF8&iwloc=&output=embed",
    "restaurantIntro": "Ruang makan hangat dengan panorama taman dan pegunungan. Menu sederhana yang cocok untuk sarapan, camilan sore, atau teman ngobrol di malam sejuk Bedugul.",
    "restaurantHours": "07:00 – 21:00 WITA",
    "heroEyebrow": "Discover",
    "heroTitle": "Bedugul",
    "heroSubtitle": "Tenang. Hangat.",
    "heroBody": "Rumah kedua Anda di dataran tinggi Bali. Kabut pagi, kopi lokal, dan pelayanan tulus dari keluarga Pelangi.",
    "promoTitle": "Menginap 10 malam, gratis 1 malam.",
    "promoBody": "Berlaku untuk pemesanan langsung melalui website resmi. Berlaku akumulatif — kumpulkan malam Anda.",
    "promoEyebrow": "Special offer",
    "seoTitle": "Pelangi Homestay — Bedugul, Bali",
    "seoDescription": "Pelangi Homestay Bedugul — penginapan hangat dengan pemandangan pegunungan, sarapan lokal, dan akses mudah ke Kebun Raya Bali serta Pura Ulun Danu Beratan.",
}

SEED_CONTENT = {
    "rooms": DEFAULT_ROOMS,
    "menu": DEFAULT_MENU,
    "gallery": DEFAULT_GALLERY,
    "attractions": DEFAULT_ATTRACTIONS,
    "faqs": DEFAULT_FAQS,
    "testimonials": DEFAULT_TESTIMONIALS,
    "site": DEFAULT_SITE,
}
