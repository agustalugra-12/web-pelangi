import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import SectionHeading from "@/components/site/SectionHeading";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function FAQ() {
  const { faqs } = useContent();
  const { t, pick } = useLang();
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-4xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("faq.eyebrow")}
          title={t("faq.title")}
          italicWord={t("faq.italic")}
          subtitle={t("faq.subtitle")}
        />
        <Accordion type="single" collapsible className="mt-10">
          {faqs.map((f, i) => (
            <AccordionItem key={f.id || i} value={`item-${i}`} className="border-ink/10" data-testid={`faq-item-${i}`}>
              <AccordionTrigger className="text-left text-teal-deep hover:text-mustard-deep font-display text-lg">
                {pick(f, "q")}
              </AccordionTrigger>
              <AccordionContent className="text-teal-deep/80 leading-relaxed">
                {pick(f, "a")}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>
    </div>
  );
}
