import "./globals.css";
import type { Metadata } from "next";
import Header from "./components/Header";
import ConditionalBackground from "./components/ConditionalBackground";
import { AuthProvider } from "../contexts/AuthContext";

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
