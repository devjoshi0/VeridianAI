"use client";

import { useEffect, useState } from "react";
import { collection, getDocs, doc, getDoc, updateDoc } from "firebase/firestore";
import { firestore } from "../../../lib/firebase";
import { useAuth } from "../../contexts/AuthContext";
import { motion } from "framer-motion";

interface Topic {
  id: string;
  name: string;
  description?: string;
}

export default function TopicSelectionDashboard() {
  const { user } = useAuth();
  const [availableTopics, setAvailableTopics] = useState<Topic[]>([]);
  const [userSelectedTopics, setUserSelectedTopics] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const topics = ['general', 'science', 'sports', 'tech', 'entertainment'];

  useEffect(() => {
    if (!user) return;
    setIsLoading(true);

    // Fetch master topics
    const fetchTopics = async () => {
      // const topicsSnap = await getDocs(collection(firestore, "topics"));
      // const topics: Topic[] = [];
      // topicsSnap.forEach(doc => {
      //   topics.push({ id: doc.id, ...doc.data() } as Topic);
      // });
      setAvailableTopics(topics.map(topic => ({ id: topic, name: topic })));

      // Fetch user preferences
      const userDoc = await getDoc(doc(firestore, "users", user.uid));
      if (userDoc.exists()) {
        const data = userDoc.data();
        if (Array.isArray(data.topics)) {
          setUserSelectedTopics(new Set(data.topics));
        }
      }
      setIsLoading(false);
    };

    fetchTopics();
  }, [user]);

  const handleCheckboxChange = (topicName: string) => {
    setUserSelectedTopics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(topicName)) {
        newSet.delete(topicName);
      } else {
        newSet.add(topicName);
      }
      return newSet;
    });
  };

  const handleSavePreferences = async () => {
    if (!user) return;
    setSaving(true);
    setFeedback(null);
    try {
      await updateDoc(doc(firestore, "users", user.uid), {
        topics: Array.from(userSelectedTopics),
      });
      setFeedback("Preferences saved!");
    } catch (err) {
      setFeedback("Failed to save preferences.");
    }
    setSaving(false);
    setTimeout(() => setFeedback(null), 2000);
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading topics...</div>;
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <h2 className="text-xl font-bold mb-4 text-center text-black">Select Your Topics</h2>
      <form className="flex flex-col gap-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 justify-items-center">
          {availableTopics.map(topic => {
            const selected = userSelectedTopics.has(topic.name);
            return (
              <motion.button
                key={topic.id}
                type="button"
                onClick={() => handleCheckboxChange(topic.name)}
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: 'spring', stiffness: 1, damping: 2 }}
                className={`px-5 py-3 rounded-xl font-medium text-lg transition-all duration-200 border border-white/30 backdrop-blur-xl focus:outline-none flex items-center justify-center text-center w-full h-full
                  ${selected
                    ? "liquid-gradient text-black shadow-lg"
                    : "bg-white/40 text-black shadow border border-white/30"}
                `}
                style={{
                  minWidth: '120px',
                  maxWidth: '100%',
                  WebkitBackdropFilter: 'blur(12px) saturate(180%)',
                  backdropFilter: 'blur(12px) saturate(180%)',
                  whiteSpace: 'pre-line',
                }}
              >
                <span className="capitalize w-full flex items-center justify-center text-center">{topic.name}</span>
                {topic.description && (
                  <span className="ml-2 text-xs text-black/60">{topic.description}</span>
                )}
              </motion.button>
            );
          })}
        </div>
        <button
          type="button"
          onClick={handleSavePreferences}
          disabled={saving}
          className="mt-4 px-6 py-2 rounded-lg bg-blue-500/80 hover:bg-blue-600 text-white font-semibold shadow-lg transition-colors duration-200 text-base backdrop-blur-xl border border-white/30"
        >
          {saving ? "Saving..." : "Save"}
        </button>
        {feedback && (
          <div className="text-center text-sm mt-2 text-green-600">{feedback}</div>
        )}
      </form>
    </div>
  );
}