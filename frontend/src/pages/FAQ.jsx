import SectionHeading from "@/components/site/SectionHeading";
import { faqs } from "@/data/content";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function FAQ() {
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-4xl mx-auto px-5 md:px-8">
        <SectionHeading eyebrow="FAQ" title="Pertanyaan" italicWord="umum" subtitle="Semoga jawaban di bawah ini membantu perencanaan liburan Anda." />
        <Accordion type="single" collapsible className="mt-10">
          {faqs.map((f, i) => (
            <AccordionItem key={i} value={`item-${i}`} className="border-ink/10" data-testid={`faq-item-${i}`}>
              <AccordionTrigger className="text-left text-teal-deep hover:text-mustard-deep font-display text-lg">
                {f.q}
              </AccordionTrigger>
              <AccordionContent className="text-teal-deep/80 leading-relaxed">
                {f.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>
    </div>
  );
}
