import type { Metadata } from "next";
import { Radio } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";
import { APP_NAME, APP_TAGLINE } from "@/lib/brand";
import "./globals.css";

export const metadata: Metadata = {
  title: `${APP_NAME} — Front Desk`,
  description: APP_TAGLINE,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex h-screen flex-col">
          <header className="flex shrink-0 items-center justify-between border-b border-border px-5 py-3">
            <div className="flex items-baseline gap-3">
              <BrandMark />
              <span className="hidden text-sm text-muted-foreground sm:inline">Front desk review queue</span>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary-soft px-2.5 py-1 text-xs font-medium text-primary-deep">
              <Radio className="size-3.5" aria-hidden />
              Demo · seeded data
            </span>
          </header>
          <main className="min-h-0 flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
