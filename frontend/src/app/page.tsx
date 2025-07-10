"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import Button from "./components/Button";
import { useAuth } from "../contexts/AuthContext";

export default function Home() {
  const { user, loading, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-[80vh]">
      <motion.div
        className="glass p-12 mt-16 flex flex-col items-center"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        <h1 className="text-5xl font-bold mb-2 text-black">Welcome to VeridianAI</h1>
        <p className="text-lg text-gray-700 mb-8 max-w-xl text-center">
          Personalized AI Newsletters Tailored for You.
        </p>
        {loading ? (
          <div className="h-12" />
        ) : user ? (
          <Link href="/settings">
            <Button variant="primary">Open Settings</Button>
          </Link>
        ) : (
          <div className="flex gap-4">
            <Link href="/signup">
              <Button variant="primary">Sign Up</Button>
            </Link>
            <Link href="/login">
              <Button variant="secondary">Login</Button>
            </Link>
          </div>
        )}
      </motion.div>
    </main>
  );
}
