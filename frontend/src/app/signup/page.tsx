"use client";

import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { motion } from "framer-motion";
import Link from "next/link";

export default function SignupPage() {
  const { register, error, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!email || !password || !confirmPassword) {
      setFormError("Please fill in all fields.");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }
    await register(email, password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-200 via-white to-blue-200">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="backdrop-blur-lg bg-white/40 rounded-xl shadow-xl p-8 w-full max-w-md border border-white/30"
      >
        <h2 className="text-2xl font-bold mb-2 text-center">Create an account</h2>
        <p className="mb-6 text-center text-gray-600">Enter your details to get started.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="name@example.com"
            className="w-full px-4 py-2 rounded bg-pink-100/60 border border-pink-200 focus:outline-none focus:ring-2 focus:ring-pink-300 text-black placeholder-gray-400"
            value={email}
            onChange={e => setEmail(e.target.value)}
            autoComplete="email"
          />
          <input
            type="password"
            placeholder="Password"
            className="w-full px-4 py-2 rounded bg-pink-100/60 border border-pink-200 focus:outline-none focus:ring-2 focus:ring-pink-300 text-black placeholder-gray-400"
            value={password}
            onChange={e => setPassword(e.target.value)}
            autoComplete="new-password"
          />
          <input
            type="password"
            placeholder="Confirm Password"
            className="w-full px-4 py-2 rounded bg-pink-100/60 border border-pink-200 focus:outline-none focus:ring-2 focus:ring-pink-300 text-black placeholder-gray-400"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
          />
          {(formError || error) && (
            <div className="text-red-500 text-sm text-center">{formError || error}</div>
          )}
          <button
            type="submit"
            className="w-full py-2 rounded bg-pink-400 hover:bg-pink-500 text-white font-semibold transition-colors duration-200 disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>
        <p className="mt-4 text-center text-gray-600 text-sm">
          Already have an account?{' '}
          <Link href="/login" className="text-pink-500 hover:underline">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
} 