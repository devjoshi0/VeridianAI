"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LightDarkToggle() {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";

  return (
    <button
      aria-label="Toggle light/dark mode"
      className="fixed z-50 top-4 right-4 bg-white/60 dark:bg-black/40 backdrop-blur-xl border border-white/30 dark:border-white/10 shadow-lg rounded-full p-2 flex items-center justify-center transition-colors hover:bg-white/80 dark:hover:bg-black/60"
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isDark ? (
          <motion.span
            key="sun"
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 90, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-yellow-400 text-2xl"
          >
            {/* Sun icon */}
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m0 13.5V21m8.25-9H21M3 12H4.75m15.364 6.364l-1.591-1.591M6.227 6.227l-1.591-1.591m0 13.728l1.591-1.591m13.728-13.728l-1.591 1.591M12 7.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 0 1 12 7.5Z" />
            </svg>
          </motion.span>
        ) : (
          <motion.span
            key="moon"
            initial={{ rotate: 90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: -90, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-blue-500 text-2xl"
          >
            {/* Moon icon */}
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 15.5A9 9 0 0 1 8.5 2.25c0 .621.063 1.23.184 1.818a.75.75 0 0 1-.97.87A7.501 7.501 0 1 0 19.06 16.286a.75.75 0 0 1 .87-.97c.588.121 1.197.184 1.82.184Z" />
            </svg>
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
} 