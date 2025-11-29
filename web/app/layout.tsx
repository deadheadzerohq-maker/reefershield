import "./globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "ReeferShield",
  description: "Autonomous reefer monitoring and tamper-proof certificates"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900 text-slate-100">
        {children}
      </body>
    </html>
  );
}
