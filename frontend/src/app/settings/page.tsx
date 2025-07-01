"use client";

import { motion } from "framer-motion";

export default function SettingsPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-200 via-white to-blue-200">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="backdrop-blur-lg bg-white/40 rounded-2xl shadow-2xl px-8 py-14 w-full max-w-xl flex flex-col items-center border border-white/30"
      >
        <h1 className="text-3xl sm:text-4xl font-extrabold text-center mb-2">
          Settings
        </h1>
        <p className="text-center text-gray-700 mb-8 max-w-md text-lg">
          Tailor your AI newsletter topics and preferences here.
        </p>
        {/* Settings form/components will go here */}
      </motion.div>
    </div>
  );
} 