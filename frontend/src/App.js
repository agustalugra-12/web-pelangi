import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ContentProvider } from "@/context/ContentContext";
import SiteLayout from "@/components/site/SiteLayout";
import ProtectedRoute from "@/components/site/ProtectedRoute";

import Home from "@/pages/Home";
import Rooms from "@/pages/Rooms";
import Facilities from "@/pages/Facilities";
import Gallery from "@/pages/Gallery";
import ExploreBedugul from "@/pages/ExploreBedugul";
import Restaurant from "@/pages/Restaurant";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import FAQ from "@/pages/FAQ";
import Blog from "@/pages/Blog";
import BlogDetail from "@/pages/BlogDetail";

import AdminLogin from "@/pages/admin/Login";
import AdminLayout from "@/pages/admin/AdminLayout";
import CmsBlog from "@/pages/admin/CmsBlog";
import PostEditor from "@/pages/admin/PostEditor";
import CmsList from "@/pages/admin/CmsList";
import CmsSettings from "@/pages/admin/CmsSettings";
import CmsMedia from "@/pages/admin/CmsMedia";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

function App() {
  return (
    <AuthProvider>
      <ContentProvider>
        <BrowserRouter>
          <ScrollToTop />
          <Toaster
            richColors
            position="top-center"
            toastOptions={{ style: { fontFamily: "DM Sans, sans-serif" } }}
          />
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
        </BrowserRouter>
      </ContentProvider>
    </AuthProvider>
  );
}

export default App;
