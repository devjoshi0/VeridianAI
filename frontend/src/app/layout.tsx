import "./globals.css";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import LightDarkToggle from "./LightDarkToggle";
import { ThemeProvider } from "next-themes";
import Header from "./components/Header";
import ConditionalBackground from "./components/ConditionalBackground";
import { AuthProvider } from "../contexts/AuthContext";

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
});
const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "VeridianAI Newsletter",
  description: "Personalized AI Newsletters for You.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ConditionalBackground />
        <div className="min-h-screen flex flex-col relative">
          <AuthProvider>
            <Header />
            {children}
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
