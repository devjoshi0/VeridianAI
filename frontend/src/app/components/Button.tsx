"use client";

import { motion } from "framer-motion";
import React, { ReactNode, MouseEventHandler } from "react";

type ButtonProps = {
  children: ReactNode;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  variant?: "primary" | "secondary";
  [key: string]: any;
};

export default function Button({ children, onClick, variant = "primary", ...props }: ButtonProps) {
  const base =
    "px-6 py-2 rounded-xl font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-purple-400";
  const variants: { [key in "primary" | "secondary"]: string } = {
    primary: "bg-purple-600 text-white shadow-lg hover:bg-purple-700",
    secondary: "bg-white bg-opacity-60 text-purple-700 border border-purple-200 hover:bg-opacity-80",
  };
  return (
    <motion.button
      whileHover={{ scale: 1.04, y: -2 }}
      whileTap={{ scale: 0.98 }}
      className={`${base} ${variants[variant]}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.button>
  );
} 