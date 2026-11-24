import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "DocIntel | Document Intelligence", description: "AI-powered document processing and invoice verification" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
