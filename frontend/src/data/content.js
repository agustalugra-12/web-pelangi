// Central static content for the marketing website.
// Photos use tinted SVG placeholders so the user can replace with real photography later.

export const SITE = {
  brand: "Pelangi Homestay",
  tagline: "Rumah hangat di jantung Bedugul",
  address: "Bedugul, Baturiti, Tabanan, Bali 82191",
  whatsapp: "6285119459269",
  whatsappDisplay: "0851-1945-9269",
  email: "pelangihomestay9@gmail.com",
  hours: "Reception 07:00 – 22:00 WITA",
  bookingUrl: "https://pelangihomestay.com/book",
  mapEmbed:
    "https://www.google.com/maps?q=Bedugul,%20Bali&t=&z=13&ie=UTF8&iwloc=&output=embed",
};

// Small utility to make a colored SVG data URL (used as placeholder photo)
// Abstract layered "landscape" placeholder. Text is intentionally omitted so
// the image can be cropped into blobs/circles without weird word fragments.
const svgPhoto = (_label, bg = "#0F4C5C", fg = "#F1C57C") => {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 400'>
    <defs>
      <linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>
        <stop offset='0' stop-color='${bg}'/>
        <stop offset='1' stop-color='#083D38'/>
      </linearGradient>
      <linearGradient id='sun' x1='0' y1='0' x2='0' y2='1'>
        <stop offset='0' stop-color='${fg}' stop-opacity='0.95'/>
        <stop offset='1' stop-color='${fg}' stop-opacity='0.4'/>
      </linearGradient>
    </defs>
    <rect width='600' height='400' fill='url(#sky)'/>
    <circle cx='430' cy='150' r='72' fill='url(#sun)' opacity='0.85'/>
    <g fill='${fg}' opacity='0.18'>
      <circle cx='90' cy='340' r='120'/>
      <circle cx='230' cy='320' r='150'/>
      <circle cx='420' cy='340' r='140'/>
      <circle cx='560' cy='320' r='95'/>
    </g>
    <g fill='#0B2E2A' opacity='0.55'>
      <path d='M0 400 L0 300 L80 250 L150 290 L210 240 L280 280 L340 235 L410 275 L470 245 L540 285 L600 260 L600 400 Z'/>
    </g>
    <g fill='#0B2E2A' opacity='0.35'>
      <path d='M0 400 L0 340 L60 310 L130 335 L190 305 L260 335 L320 300 L390 335 L450 310 L520 340 L600 315 L600 400 Z'/>
    </g>
  </svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

// Shared facility set — Standard & Cottage carry the exact same amenities.
// The only difference between them is room size (18 m² vs 34 m²).
const COMMON_FACILITIES = [
  "Double Bed",
  "Air Panas",
  "Smart TV",
  "WiFi",
  "Teras Pribadi",
  "Breakfast",
];

export const rooms = [
  {
    slug: "standard",
    name: "Standard Room",
    capacity: "2 Tamu",
    size: "18 m²",
    priceFrom: "IDR 175.000",
    image: "/assets/std-5.webp",
    gallery: [
      "/assets/std-5.webp",
      "/assets/std-4.webp",
      "/assets/std-3.webp",
      "/assets/std-2.webp",
      "/assets/std-1.webp",
    ],
    facilities: COMMON_FACILITIES,
    description:
      "Kamar hangat dan efisien untuk berdua, dengan teras pribadi, kamar mandi bersih, dan sarapan hangat sudah termasuk.",
  },
  {
    slug: "cottage",
    name: "Cottage",
    capacity: "2 – 4 Tamu",
    size: "34 m²",
    priceFrom: "IDR 225.000",
    image: "/assets/cot-2.webp",
    gallery: [
      "/assets/cot-2.webp",
      "/assets/cot-4.webp",
      "/assets/cot-3.webp",
      "/assets/cot-1.webp",
      "/assets/cot-5.webp",
    ],
    facilities: COMMON_FACILITIES,
    description:
      "Fasilitas identik dengan Standard Room, namun jauh lebih lapang — 34 m² dengan teras luas untuk keluarga kecil atau honeymoon yang butuh ruang bernapas lebih.",
  },
];

export const facilities = [
  { icon: "fa-wifi", title: "WiFi Cepat", desc: "Fiber optic di seluruh area." },
  { icon: "fa-mug-hot", title: "Air Panas 24 Jam", desc: "Selalu siap untuk pagi yang dingin." },
  { icon: "fa-tv", title: "Smart TV", desc: "Netflix & YouTube di setiap kamar." },
  { icon: "fa-utensils", title: "Breakfast Lokal", desc: "Menu hangat khas Bedugul." },
  { icon: "fa-tree", title: "Taman & Kebun", desc: "Sudut hijau untuk pagi tenang." },
  { icon: "fa-mountain", title: "View Pegunungan", desc: "Kabut pagi tepat di depan mata." },
  { icon: "fa-car", title: "Parkir Luas", desc: "Aman untuk mobil & motor." },
  { icon: "fa-headset", title: "Reception Ramah", desc: "Tim lokal siap membantu 07:00–22:00." },
];

export const galleryCategories = [
  "Semua",
  "Standard Room",
  "Cottage",
  "Bathroom",
  "Restaurant",
  "Garden",
  "View",
  "Lobby",
];

export const galleryItems = [
  { category: "Standard Room", src: "/assets/std-5.webp" },
  { category: "Standard Room", src: "/assets/std-4.webp" },
  { category: "Standard Room", src: "/assets/std-3.webp" },
  { category: "Standard Room", src: "/assets/std-2.webp" },
  { category: "Cottage", src: "/assets/cot-2.webp" },
  { category: "Cottage", src: "/assets/cot-4.webp" },
  { category: "Cottage", src: "/assets/cot-3.webp" },
  { category: "Cottage", src: "/assets/cot-1.webp" },
  { category: "Bathroom", src: "/assets/std-1.webp" },
  { category: "Bathroom", src: "/assets/cot-5.webp" },
  { category: "Restaurant", src: "/assets/restaurant.jpg" },
  { category: "Garden", src: "/assets/garden.jpg" },
  { category: "Lobby", src: "/assets/signage.jpg" },
  { category: "Lobby", src: "/assets/facade.jpg" },
  { category: "View", src: svgPhoto("Mountain View", "#12564F", "#E9C46A") },
];

// Icon mapping for facility pills (Font Awesome classnames)
export const facilityIcons = {
  "WiFi": "fa-wifi",
  "Air Panas": "fa-mug-hot",
  "Smart TV": "fa-tv",
  "Breakfast": "fa-utensils",
  "Double Bed": "fa-bed",
  "Queen Bed": "fa-bed",
  "King Bed": "fa-bed",
  "Extra Bed": "fa-bed-pulse",
  "Teras Pribadi": "fa-chair",
  "Balkon Kecil": "fa-chair",
  "Balkon Luas": "fa-chair",
  "View Taman": "fa-tree",
  "View Pegunungan": "fa-mountain",
};

// Helper: get first gallery item in a category, with safe fallback
export const galleryByCategory = (category) =>
  galleryItems.find((g) => g.category === category) || galleryItems[0];

export const attractions = [
  {
    title: "Pura Ulun Danu Beratan",
    distance: "5 menit",
    image: svgPhoto("Pura Ulun Danu", "#0F4C5C", "#F1C57C"),
    desc: "Ikon Bedugul — pura di atas danau yang tampak melayang saat air pasang.",
  },
  {
    title: "Kebun Raya Bali",
    distance: "8 menit",
    image: svgPhoto("Kebun Raya", "#3F7F49", "#F1C57C"),
    desc: "Kebun raya luas dengan ribuan koleksi tanaman tropis dataran tinggi.",
  },
  {
    title: "Danau Beratan",
    distance: "5 menit",
    image: svgPhoto("Danau Beratan", "#1F6A6E", "#F7F3EA"),
    desc: "Berperahu, memancing, atau sekadar menikmati sunrise berkabut.",
  },
  {
    title: "Pasar Candikuning",
    distance: "6 menit",
    image: svgPhoto("Pasar Candikuning", "#C6852E", "#0B2E2A"),
    desc: "Strawberry segar, sayur mayur, dan oleh-oleh khas dataran tinggi.",
  },
  {
    title: "Hidden Gems Munduk",
    distance: "35 menit",
    image: svgPhoto("Munduk", "#0B3A47", "#E9C46A"),
    desc: "Air terjun, perkebunan kopi, dan jalur trekking untuk pecinta alam.",
  },
  {
    title: "Handara Gate",
    distance: "12 menit",
    image: svgPhoto("Handara Gate", "#0F4C5C", "#F1C57C"),
    desc: "Gerbang ikonik untuk foto klasik ala Bali dataran tinggi.",
  },
];

export const testimonials = [
  {
    name: "Rina & Aldo",
    origin: "Jakarta",
    text: "Kamarnya wangi, kasurnya empuk, dan sarapannya bikin susah move on. Bakal balik lagi tahun depan!",
  },
  {
    name: "Sarah",
    origin: "Melbourne, AU",
    text: "The most peaceful morning I've had in months. The staff went above and beyond for us.",
  },
  {
    name: "Keluarga Wibowo",
    origin: "Surabaya",
    text: "Cottage-nya luas, anak-anak betah main di taman. Lokasinya sangat strategis ke Kebun Raya.",
  },
  {
    name: "Bagas",
    origin: "Bandung",
    text: "Value for money-nya juara. Sunset di balkon, kopi hangat — nggak butuh liburan yang mahal.",
  },
];

export const faqs = [
  { q: "Jam berapa Check-in dan Check-out?", a: "Check-in mulai pukul 14:00 WITA, Check-out paling lambat 12:00 WITA. Early check-in menyesuaikan ketersediaan kamar." },
  { q: "Apakah breakfast sudah termasuk?", a: "Ya, semua tipe Superior dan Cottage sudah termasuk breakfast lokal untuk 2 orang. Standard Room bisa menambahkan breakfast dengan biaya kecil." },
  { q: "Apakah anak-anak diperbolehkan?", a: "Tentu. Anak di bawah 6 tahun gratis (tanpa extra bed). Extra bed tersedia untuk anak 6–12 tahun dengan biaya tambahan." },
  { q: "Berapa biaya Extra Bed?", a: "Rp 50.000 per malam sudah termasuk sarapan tambahan." },
  { q: "Bagaimana kebijakan pembatalan?", a: "Pembatalan gratis hingga 3 hari sebelum tanggal check-in. Setelah itu berlaku ketentuan booking engine terkait." },
  { q: "Metode pembayaran apa saja?", a: "Semua kartu kredit utama, transfer bank Indonesia, QRIS, dan pembayaran on-site (tunai)." },
  { q: "Apakah tersedia parkir?", a: "Ya, parkir mobil dan motor tersedia gratis untuk tamu." },
];

export const restaurant = {
  intro:
    "Ruang makan hangat dengan panorama taman dan pegunungan. Menu kami memuliakan bahan lokal Bedugul — strawberry segar, kopi Munduk, dan sayur mayur dari kebun tetangga.",
  hours: "07:00 – 21:00 WITA",
  menu: [
    { name: "Nasi Campur Pelangi", desc: "Nasi hangat, ayam bakar, sate lilit, sayur khas, sambal matah.", price: "IDR 65k" },
    { name: "Bubur Injin Kelapa", desc: "Bubur beras hitam gula aren dengan santan segar.", price: "IDR 28k" },
    { name: "Strawberry Pancake", desc: "Pancake tebal, strawberry Candikuning, madu lokal.", price: "IDR 45k" },
    { name: "Kopi Susu Munduk", desc: "Kopi Munduk single origin, susu segar dataran tinggi.", price: "IDR 25k" },
  ],
};
