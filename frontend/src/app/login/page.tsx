"use client";

import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { login, error, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!email || !password) {
      setFormError("Please fill in all fields.");
      return;
    }
    await login(email, password);
    if (!error) {
      router.push("/settings");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-200 via-white to-blue-200">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="backdrop-blur-lg bg-white/40 rounded-xl shadow-xl p-8 w-full max-w-md border border-white/30"
      >
        <h2 className="text-2xl font-bold mb-2 text-center">Welcome back</h2>
        <p className="mb-6 text-center text-gray-600">Enter your credentials to access your account</p>
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
            autoComplete="current-password"
          />
          {(formError || error) && (
            <div className="text-red-500 text-sm text-center">{formError || error}</div>
          )}
          <button
            type="submit"
            className="w-full py-2 rounded bg-pink-400 hover:bg-pink-500 text-white font-semibold transition-colors duration-200 disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <p className="mt-4 text-center text-gray-600 text-sm">
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="text-pink-500 hover:underline">Sign up</Link>
        </p>
      </motion.div>
    </div>
  );
} 