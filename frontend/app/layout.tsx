import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Dispatch — Order Agent",
  description: "Shipper console for the freight dispatching Order Agent",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
