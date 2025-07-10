"use client";

import Link from "next/link";
import Button from "./Button";
import { useAuth } from "../../contexts/AuthContext";
import Image from "next/image";

export default function Header() {
  const { user, loading, logout } = useAuth();

  return (
    <header className="glass flex items-center justify-between px-8 py-4 mt-4 mx-auto max-w-5xl gap-8">
      <Link href="/" className="flex items-center gap-3 text-2xl font-bold">
        <Image src="/logo.png" alt="VeridianAI Logo" width={40} height={40} priority />
        <span className="text-black">Veridian</span>
        <span className="text-purple-600">AI</span>
      </Link>
      <nav className="flex items-center gap-3">
        {loading ? null : user ? (
          <form action="/logout" method="post" onSubmit={async (e) => { e.preventDefault(); await logout(); }}>
            <Button variant="secondary" type="submit">Logout</Button>
          </form>
        ) : (
          <Link href="/login">
            <Button variant="secondary">Login</Button>
          </Link>
        )}
      </nav>
    </header>
  );
} 