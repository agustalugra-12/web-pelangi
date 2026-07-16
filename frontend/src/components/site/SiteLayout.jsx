import { Outlet } from "react-router-dom";
import Navbar from "@/components/site/Navbar";
import Footer from "@/components/site/Footer";
import WhatsAppButton from "@/components/site/WhatsAppButton";
import LodgingSchema from "@/components/site/LodgingSchema";

export default function SiteLayout() {
  return (
    <div className="min-h-screen flex flex-col grain bg-cream">
      <LodgingSchema />
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <WhatsAppButton />
    </div>
  );
}
