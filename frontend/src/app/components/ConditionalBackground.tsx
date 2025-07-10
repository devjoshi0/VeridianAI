"use client";
import { usePathname } from "next/navigation";

export default function ConditionalBackground() {
  // Always show the animated gradient background on all pages
  return <div className="bg-gradient-animated"></div>;
} 