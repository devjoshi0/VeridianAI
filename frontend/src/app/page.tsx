"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-200 via-white to-blue-200">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="backdrop-blur-lg bg-white/40 rounded-2xl shadow-2xl px-8 py-14 w-full max-w-xl flex flex-col items-center border border-white/30"
      >
        <h1 className="text-4xl sm:text-5xl font-extrabold text-center mb-4">
          Welcome to <span className="text-pink-400">AuthGlass</span>
        </h1>
        <p className="text-center text-gray-700 mb-8 max-w-md">
          A beautiful, modern, and secure authentication system built with Next.js and Firebase. Featuring a stunning frosted glass UI with soft pink and blue tones.
        </p>
        <div className="flex gap-4 w-full justify-center">
          <Link href="/signup" className="px-6 py-2 rounded-lg bg-pink-400 hover:bg-pink-500 text-white font-semibold shadow transition-colors duration-200 text-base">
            Get Started
          </Link>
          <Link href="/login" className="px-6 py-2 rounded-lg bg-white/70 hover:bg-white/90 text-pink-500 font-semibold border border-pink-200 shadow transition-colors duration-200 text-base">
            Sign In
          </Link>
        </div>
      </motion.div>
      <div className="fixed top-6 left-8 text-2xl font-bold text-pink-200 select-none opacity-80">
        AuthGlass
      </div>
      <div className="fixed top-6 right-8 flex gap-2">
        <Link href="/login" className="px-4 py-1 rounded bg-white/60 text-pink-500 font-medium hover:bg-white/80 transition-colors">Login</Link>
        <Link href="/signup" className="px-4 py-1 rounded bg-pink-400 text-white font-medium hover:bg-pink-500 transition-colors">Sign Up</Link>
      </div>
    </div>
  );
}
