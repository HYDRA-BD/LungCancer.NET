import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "LungCancer.NET — Clinical Pre-Screening",
  description:
    "AI-assisted lung cancer risk pre-screening for rural and underserved populations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-full flex flex-col bg-background text-foreground relative selection:bg-primary/20"
        suppressHydrationWarning
      >
        {/* Global Fixed Blurred Background Logo */}
        <div
          aria-hidden="true"
          className="fixed inset-0 -z-10 pointer-events-none opacity-[0.08] dark:opacity-[0.14] dark:brightness-200"
          style={{
            backgroundImage: "url(/logo.png)",
            backgroundSize: "contain",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
            filter: "blur(60px)",
          }}
        />

        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
