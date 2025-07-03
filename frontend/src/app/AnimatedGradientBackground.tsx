"use client";

import { motion } from "framer-motion";

export default function AnimatedGradientBackground() {
  return (
    <div className="fixed inset-0 -z-10 w-full h-full overflow-hidden">
      {/* Pink blob */}
      <motion.div
        className="absolute top-[-10%] left-[-10%] w-[60vw] h-[60vw] bg-pink-300 rounded-full blur-3xl opacity-60"
        animate={{
          x: [0, 40, -40, 0],
          y: [0, 30, -30, 0],
          scale: [1, 1.1, 0.9, 1],
        }}
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {/* Blue blob */}
      <motion.div
        className="absolute bottom-[-10%] right-[-10%] w-[60vw] h-[60vw] bg-blue-300 rounded-full blur-3xl opacity-60"
        animate={{
          x: [0, -40, 40, 0],
          y: [0, -30, 30, 0],
          scale: [1, 0.9, 1.1, 1],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {/* Center white/pink/blue blend for extra glassy look */}
      <motion.div
        className="absolute top-1/2 left-1/2 w-[80vw] h-[80vw] -translate-x-1/2 -translate-y-1/2 bg-gradient-to-br from-pink-200 via-white to-blue-200 rounded-full blur-2xl opacity-40"
        animate={{
          scale: [1, 1.05, 0.95, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </div>
  );
} 