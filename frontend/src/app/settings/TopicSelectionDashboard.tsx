"use client";

import { useEffect, useState } from "react";
import { collection, getDocs, doc, getDoc, updateDoc } from "firebase/firestore";
import { firestore } from "../../../lib/firebase";
import { useAuth } from "../../contexts/AuthContext";

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

  useEffect(() => {
    if (!user) return;
    setIsLoading(true);

    // Fetch master topics
    const fetchTopics = async () => {
      const topicsSnap = await getDocs(collection(firestore, "topics"));
      const topics: Topic[] = [];
      topicsSnap.forEach(doc => {
        topics.push({ id: doc.id, ...doc.data() } as Topic);
      });
      setAvailableTopics(topics);

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
      <h2 className="text-xl font-bold mb-4 text-center text-black dark:text-white">Select Your Topics</h2>
      <form className="flex flex-col gap-4">
        {availableTopics.map(topic => (
          <label key={topic.id} className="flex items-center gap-2 bg-white/70 dark:bg-black/30 rounded-xl px-3 py-2 shadow ring-1 ring-white/40 dark:ring-white/10 border border-white/20 dark:border-white/10 backdrop-blur-xl">
            <input
              type="checkbox"
              checked={userSelectedTopics.has(topic.name)}
              onChange={() => handleCheckboxChange(topic.name)}
              className="accent-pink-400 w-5 h-5"
            />
            <span className="font-medium text-black dark:text-white">{topic.name}</span>
            <span className="text-xs text-gray-700 dark:text-gray-300 ml-2">{topic.description}</span>
          </label>
        ))}
        <button
          type="button"
          onClick={handleSavePreferences}
          disabled={saving}
          className="mt-4 px-6 py-2 rounded-lg bg-blue-500/80 dark:bg-blue-600/80 hover:bg-blue-600 dark:hover:bg-blue-700 text-white font-semibold shadow-lg transition-colors duration-200 text-base backdrop-blur-xl border border-white/30 dark:border-white/10"
        >
          {saving ? "Saving..." : "Save"}
        </button>
        {feedback && (
          <div className="text-center text-sm mt-2 text-green-600 dark:text-green-400">{feedback}</div>
        )}
      </form>
    </div>
  );
}