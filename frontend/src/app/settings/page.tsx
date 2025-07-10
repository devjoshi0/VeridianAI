"use client";

import { motion } from "framer-motion";
import TopicSelectionDashboard from "./TopicSelectionDashboard";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";

export default function SettingsPage() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-200 via-white to-blue-200">
        <div className="backdrop-blur-2xl bg-white/60 dark:bg-black/40 rounded-3xl shadow-2xl ring-1 ring-white/40 dark:ring-white/10 border border-white/30 dark:border-white/10 px-8 py-14 w-full max-w-xl flex flex-col items-center glass-panel relative">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-center mb-2 text-black dark:text-white">Access Denied</h1>
          <p className="text-center text-gray-700 dark:text-gray-200 mb-8 max-w-md text-lg">You must be logged in to view your settings.</p>
          <Link href="/login">
            <span className="text-blue-600 underline">Go to Login</span>
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="min-h-screen flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="glass rounded-3xl shadow-2xl border border-white/30 px-8 py-14 w-full max-w-xl flex flex-col items-center relative"
      >
        <Link href="/" className="absolute left-4 top-4 text-2xl text-blue-500 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors" aria-label="Back to home">
          ←
        </Link>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-center mb-2 text-black">
          Settings
        </h1>
        <p className="text-center text-black mb-8 max-w-md text-lg">
          Tailor your AI newsletter topics and preferences here.
        </p>
        <TopicSelectionDashboard />
      </motion.div>
    </div>
  );
} 