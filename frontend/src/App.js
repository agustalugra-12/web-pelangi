import { useEffect, lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ContentProvider } from "@/context/ContentContext";
import { LanguageProvider } from "@/context/LanguageContext";
import SiteLayout from "@/components/site/SiteLayout";
import ProtectedRoute from "@/components/site/ProtectedRoute";

// Toaster (sonner) dijadikan lazy (2026-08-01, ditemukan lewat analisis bundle nyata -
// source-map-explorer: sonner = 35KB/~9.6KB gzip, 6-8% dari main bundle) - sebelumnya
// dimuat EAGER di setiap halaman termasuk landing page, padahal toast() TIDAK PERNAH
// dipanggil dari Home/halaman publik lain (cuma Contact.jsx & /admin, keduanya SUDAH
// lazy). Toaster cuma perlu siap SEBELUM tamu benar-benar submit form, jadi aman ditunda
// tanpa terasa - mengurangi JS yang wajib dieksekusi di render pertama Home.
const Toaster = lazy(() =>
  import("sonner").then((m) => ({ default: m.Toaster }))
);

// Home is kept as a static import: it's the most common landing page,
// so loading it eagerly avoids a Suspense flash for the majority of visits.
import Home from "@/pages/Home";

const Rooms = lazy(() => import("@/pages/Rooms"));
const Facilities = lazy(() => import("@/pages/Facilities"));
const Gallery = lazy(() => import("@/pages/Gallery"));
const ExploreBedugul = lazy(() => import("@/pages/ExploreBedugul"));
const Restaurant = lazy(() => import("@/pages/Restaurant"));
const About = lazy(() => import("@/pages/About"));
const Contact = lazy(() => import("@/pages/Contact"));
const FAQ = lazy(() => import("@/pages/FAQ"));
const Blog = lazy(() => import("@/pages/Blog"));
const BlogDetail = lazy(() => import("@/pages/BlogDetail"));
const PrivacyPolicy = lazy(() => import("@/pages/PrivacyPolicy"));
const TermsAndConditions = lazy(() => import("@/pages/TermsAndConditions"));
const CancellationPolicy = lazy(() => import("@/pages/CancellationPolicy"));
const RefundPolicy = lazy(() => import("@/pages/RefundPolicy"));
const HouseRules = lazy(() => import("@/pages/HouseRules"));
const PaymentInformation = lazy(() => import("@/pages/PaymentInformation"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const AdminLogin = lazy(() => import("@/pages/admin/Login"));
const AdminLayout = lazy(() => import("@/pages/admin/AdminLayout"));
const CmsBlog = lazy(() => import("@/pages/admin/CmsBlog"));
const PostEditor = lazy(() => import("@/pages/admin/PostEditor"));
const CmsList = lazy(() => import("@/pages/admin/CmsList"));
const CmsSettings = lazy(() => import("@/pages/admin/CmsSettings"));
const CmsMedia = lazy(() => import("@/pages/admin/CmsMedia"));

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

// Shared between client (App, wrapped in BrowserRouter below) and the Node SSR entry
// (frontend/ssr/render.jsx, wrapped in StaticRouter instead) - kept as a named export
// so StaticRouter/react-router core never needs to be imported here, keeping it out of
// the CLIENT bundle entirely (it's only ever used server-side).
export function AppRoutes() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={null}>
        <Toaster
          richColors
          position="top-center"
          toastOptions={{ style: { fontFamily: "DM Sans, sans-serif" } }}
        />
      </Suspense>
      <Suspense fallback={null}>
      <Routes>
        {/* Site */}
        <Route element={<SiteLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/rooms" element={<Rooms />} />
          <Route path="/facilities" element={<Facilities />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/explore-bedugul" element={<ExploreBedugul />} />
          <Route path="/restaurant" element={<Restaurant />} />
          <Route path="/about" element={<About />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/:slug" element={<BlogDetail />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/terms-and-conditions" element={<TermsAndConditions />} />
          <Route path="/cancellation-policy" element={<CancellationPolicy />} />
          <Route path="/refund-policy" element={<RefundPolicy />} />
          <Route path="/house-rules" element={<HouseRules />} />
          <Route path="/payment-information" element={<PaymentInformation />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Admin */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/admin" element={<CmsBlog />} />
          <Route path="/admin/dashboard" element={<CmsBlog />} />
          <Route path="/admin/blog" element={<CmsBlog />} />
          <Route path="/admin/posts/new" element={<PostEditor />} />
          <Route path="/admin/posts/:id" element={<PostEditor />} />
          <Route path="/admin/rooms" element={<CmsList section="rooms" />} />
          <Route path="/admin/menu" element={<CmsList section="menu" />} />
          <Route path="/admin/gallery" element={<CmsList section="gallery" />} />
          <Route path="/admin/attractions" element={<CmsList section="attractions" />} />
          <Route path="/admin/faqs" element={<CmsList section="faqs" />} />
          <Route path="/admin/testimonials" element={<CmsList section="testimonials" />} />
          <Route path="/admin/settings" element={<CmsSettings />} />
          <Route path="/admin/media" element={<CmsMedia />} />
        </Route>
      </Routes>
      </Suspense>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <ContentProvider>
        <LanguageProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </LanguageProvider>
      </ContentProvider>
    </AuthProvider>
  );
}

export default App;
