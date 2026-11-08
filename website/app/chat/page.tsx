"use client";

import ReactMarkdown from "react-markdown";
import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Send, RotateCcw, AlertCircle } from "lucide-react";

interface Source {
  tag: string;
  document: string;
  page: number;
  reference: string;
  url: string | null;
}

interface Message {
  id: string;
  sender: "user" | "advisor";
  text: string;
  timestamp: string;
  sources?: Source[];
}

// 1. Dedicated greetings for each language option
const WELCOME_MESSAGES = {
  auto: "Hi! I’m ReCover. I’m here to help you understand microinsurance and explore options that may suit your business.\n\nYou can talk to me in the language you’re most comfortable with English, Kiswahili, or Sheng.",
  Kiswahili: "Habari! Mimi ni ReCover. Niko hapa kukusaidia kuelewa bima ndogondogo (microinsurance) na kuangalia mipango inayofaa biashara yako.\n\nUnaweza kuzungumza nami kwa Kiswahili au Sheng.",
  English: "Hello! I'm ReCover. I'm here to help you understand microinsurance and explore coverage options that work best for your business.\n\nFeel free to ask me anything in plain English."
};


const API_BASE_URL = (
  process.env.NEXT_PUBLIC_RECOVER_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const SESSION_STORAGE_KEY = "recover_session_id";

function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);

  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }

  return sessionId;
}

function renderAnswerWithCitations(
  text: string,
  sources: Source[] = []
) {
  const sourceMap = new Map(
    sources.map((source) => [source.tag, source])
  );

  const parts = text.split(/(\\[S\\d+\\])/g);

  return parts.map((part, index) => {
    const source = sourceMap.get(part);

    if (!source || !source.url) {
      return <React.Fragment key={index}>{part}</React.Fragment>;
    }

    const citationUrl = new URL(source.url, API_BASE_URL).toString();

    return (
      <a
        key={index}
        href={citationUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[#1F7A50] font-semibold underline hover:text-[#145C3A]"
        title={`${source.document}, page ${source.page}`}
      >
        {part}
      </a>
    );
  });
}

export default function ChatPage() {
  const [languagePref, setLanguagePref] = useState<"auto" | "Kiswahili" | "English">("auto");
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "advisor",
      text: WELCOME_MESSAGES.auto,
      timestamp: "Just now",
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // 2. Tapping the button directly updates the initial greeting
  const handleLanguageChange = (newLang: "auto" | "Kiswahili" | "English") => {
    if (languagePref === newLang) return;
    setLanguagePref(newLang);

    setMessages((prev) => {
      // If user hasn't sent any messages yet, replace the initial welcome text
      if (prev.length === 1 && prev[0].id === "initial-welcome") {
        return [
          {
            ...prev[0],
            text: WELCOME_MESSAGES[newLang],
          },
        ];
      }
      
      // If a conversation is already underway, update the welcome message at the top
      return prev.map((msg) =>
        msg.id === "initial-welcome"
          ? { ...msg, text: WELCOME_MESSAGES[newLang] }
          : msg
      );
    });
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const trimmed = inputText.trim();

    if (!trimmed || isLoading) return;

    setErrorMessage(null);

    const now = new Date();

    const timeString = now.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: trimmed,
      timestamp: timeString,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      const sessionId = getSessionId();

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmed,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          errorData.detail || "Unable to reach the advisor service."
        );
      }

      const data = await res.json();

      const rawText = data.answer || data.reply || "I couldn't generate a response.";
      const cleanText = rawText
        .replace(/\[S\d+(?:,\s*S\d+)*\]/gi, "")
        .replace(/\s{2,}/g, " ")
        .replace(/\s+([.,!?:])/g, "$1")
        .trim();

      const advisorMessage: Message = {
        id: `advisor-${Date.now()}`,
        sender: "advisor",
        text: cleanText,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        sources: data.sources || [],
      };

      setMessages((prev) => [...prev, advisorMessage]);

    } catch (err: any) {
      console.error(err);

      setErrorMessage(
        err.message || "Could not reach the ReCover backend."
      );

    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleResetConversation = async () => {
    const oldSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

    if (oldSessionId) {
      try {
        await fetch(
          `${API_BASE_URL}/reset/${encodeURIComponent(oldSessionId)}`,
          { method: "POST" }
        );
      } catch (error) {
        console.error("Could not reset backend session:", error);
      }
    }

    localStorage.setItem(
      SESSION_STORAGE_KEY,
      crypto.randomUUID()
    );

    setMessages([
      {
        id: "initial-welcome",
        sender: "advisor",
        text: WELCOME_MESSAGES[languagePref],
        timestamp: "Just now",
      },
    ]);

    setErrorMessage(null);
  };

  return (
    <div className="flex h-screen flex-col bg-[#FAF8F5] text-[#1E1E1E] font-sans antialiased">
      {/* 1. Header */}
      <header className="border-b border-[#EAE3D5] bg-[#FBF9F4] px-4 py-3 shrink-0">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-1.5 -ml-1.5 rounded-full text-[#5C5547] hover:bg-[#EFE7DA] transition"
              aria-label="Back to home"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif font-bold text-base text-[#1F4E38]">
                  ReCover
                </span>
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-600" title="Online" />
              </div>
              <p className="text-[11px] text-[#7C7362] leading-tight">
                Microinsurance Advisor
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <div 
              role="group"
              aria-label="Select conversation language"
              className="flex items-center border border-[#DDD5C5] bg-[#EFE8DC] rounded-full p-1 text-xs font-semibold text-[#564E41] shadow-2xs select-none"
            >
              <button
                type="button"
                onClick={() => handleLanguageChange("auto")}
                className={`min-h-[34px] px-3.5 rounded-full transition-all duration-150 active:scale-95 cursor-pointer touch-manipulation ${
                  languagePref === "auto"
                    ? "bg-white text-[#1F4E38] shadow-xs font-bold"
                    : "text-[#6E6554] hover:text-[#1F4E38]"
                }`}
                title="Automatic detection"
              >
                Auto
              </button>

              <button
                type="button"
                onClick={() => handleLanguageChange("Kiswahili")}
                className={`min-h-[34px] px-3.5 rounded-full transition-all duration-150 active:scale-95 cursor-pointer touch-manipulation ${
                  languagePref === "Kiswahili"
                    ? "bg-white text-[#1F4E38] shadow-xs font-bold"
                    : "text-[#6E6554] hover:text-[#1F4E38]"
                }`}
              >
                SW
              </button>

              <button
                type="button"
                onClick={() => handleLanguageChange("English")}
                className={`min-h-[34px] px-3.5 rounded-full transition-all duration-150 active:scale-95 cursor-pointer touch-manipulation ${
                  languagePref === "English"
                    ? "bg-white text-[#1F4E38] shadow-xs font-bold"
                    : "text-[#6E6554] hover:text-[#1F4E38]"
                }`}
              >
                EN
              </button>
            </div>

            <button
              type="button"
              onClick={handleResetConversation}
              className="p-2 rounded-full text-[#7C7362] hover:bg-[#EFE7DA] transition"
              title="Restart conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* 2. Message Feed */}
      <main className="flex-1 overflow-y-auto px-4 py-5 overscroll-contain">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.map((msg) => {
            const isUser = msg.sender === "user";
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[78%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed shadow-2xs whitespace-pre-wrap ${
                    isUser
                      ? "bg-[#1F4E38] text-white rounded-br-xs"
                      : "bg-white text-[#212121] border border-[#E7DFD1] rounded-bl-xs"
                  }`}
                >
                  <ReactMarkdown>
                    {msg.text}
                  </ReactMarkdown>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-[#EAE3D5]">
                      <p className="text-xs font-semibold text-[#6B6254] mb-1">
                        Sources
                      </p>

                      <div className="flex flex-col gap-1">
                        {msg.sources.map((source, index) => (
                          source.url ? (
                            <a
                              key={`${source.tag}-${index}`}
                              href={new URL(source.url, API_BASE_URL).toString()}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-[#1F7A50] underline hover:text-[#145C3A]"
                            >
                              {source.tag} {source.document}, page {source.page}
                            </a>
                          ) : (
                            <span
                              key={`${source.tag}-${index}`}
                              className="text-xs text-[#6B6254]"
                            >
                              {source.tag} {source.document}, page {source.page}
                            </span>
                          )
                        ))}
                      </div>
                    </div>
                  )}
                  <span
                    className={`block text-[10px] mt-1.5 text-right ${
                      isUser ? "text-emerald-200/70" : "text-[#8F8675]"
                    }`}
                  >
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex items-center gap-1.5 bg-white border border-[#E7DFD1] text-[#7C7362] px-4 py-3 rounded-2xl rounded-bl-xs w-16 shadow-2xs">
              <span className="w-1.5 h-1.5 bg-[#8F8675] rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-[#8F8675] rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-[#8F8675] rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          )}

          {/* Error Notice */}
          {errorMessage && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
              <AlertCircle className="w-4 h-4 text-amber-700 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* 3. Input Console */}
      <footer className="border-t border-[#EAE3D5] bg-[#FBF9F4] p-3 shrink-0">
        <div className="max-w-2xl mx-auto">
          <form onSubmit={handleSendMessage} className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={
                languagePref === "Kiswahili"
                  ? "Uliza swali au eleza biashara yako..."
                  : "Ask a question or describe your business..."
              }
              className="flex-1 rounded-full border border-[#D8CFBF] bg-white px-4 py-2.5 text-sm text-[#1E1E1E] placeholder-[#8F8675] focus:outline-none focus:ring-2 focus:ring-[#1F4E38] focus:border-transparent transition"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="rounded-full bg-[#1F4E38] p-2.5 text-white transition hover:bg-[#163828] disabled:opacity-30 disabled:cursor-not-allowed shadow-xs shrink-0"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
}