"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { 
  ArrowRight, 
  ArrowDown, 
  Check, 
  HelpCircle,
  Package,
  Flame,
  Wallet,
  Clock
} from "lucide-react";

interface MitumbaFocus {
  id: string;
  title: string;
  summary: string;
  reality: string;
  howRecoverHelps: string;
}

interface JargonPair {
  term: string;
  formalText: string;
  plainText: string;
  example: string;
}

interface TeamMember {
  name: string;
  role: string;
  initials: string;
  image?: string;
}

// 1. Mitumba-centred focus areas (Initial Target Audience)
const MITUMBA_AREAS: MitumbaFocus[] = [
  {
    id: "stock",
    title: "Stock & Bales (Marobota)",
    summary: "Your inventory represents months of upfront working capital.",
    reality: "Buying a bale means committing cash upfront before any garment is sorted, priced, or sold.",
    howRecoverHelps: "ReCover helps you discover options designed to protect inventory value if fire or unexpected damage occurs."
  },
  {
    id: "stall",
    title: "Market Stall Vulnerability",
    summary: "Open-air stalls face distinct physical risks.",
    reality: "Stalls in crowded markets share wiring and open alleys, making individual precautions harder to control.",
    howRecoverHelps: "We explain what typical stall-protection policies actually cover—and clearly point out what they exclude."
  },
  {
    id: "cashflow",
    title: "Daily & Weekly Inflows",
    summary: "Income fluctuates with foot traffic and market days.",
    reality: "A slow week shouldn't mean losing your protection because of rigid monthly billing cycles.",
    howRecoverHelps: "We guide you toward micro-options that offer flexible micro-installments aligned with your cash flow."
  }
];

// 2. Real terminology demystified
const JARGON_ITEMS: JargonPair[] = [
  {
    term: "Premium",
    formalText: "“The periodic consideration payable by the policyholder to maintain active indemnification cover.”",
    plainText: "Pesa unayolipa mara kwa mara (kila siku, wiki, au mwezi) ili bima yako iendelee kufanya kazi.",
    example: "The small regular payment you make via M-Pesa to keep your stock protected."
  },
  {
    term: "Coverage",
    formalText: "“The scope of liability and enumerated peril protections provided under the agreed schedule.”",
    plainText: "Mambo maalum ambayo bima inakubali kulipia yakitokea.",
    example: "The exact risks included in your policy—like fire or burglary—and the limit on how much will be paid."
  },
  {
    term: "Claim",
    formalText: "“A formal assertion of indemnification submitted subsequent to an insured event.”",
    plainText: "Maombi rasmi ya kulipwa fidia baada ya uharibifu au hasara iliyokatiwa bima kutokea.",
    example: "Notifying the insurer that an accident happened so they can verify the loss and send compensation."
  },
  {
    term: "Exclusion",
    formalText: "“Specific circumstances, hazards, or property conditions not indemnified under this contract.”",
    plainText: "Vitu au hali ambazo bima haitalipa hata zikitokea.",
    example: "Clear boundaries you must know in advance—such as unattended goods left outside overnight."
  }
];

// 3. Simple, uncluttered team data
const TEAM_MEMBERS: TeamMember[] = [
  {
    name: "Michelle Tulah",
    role: "Software Engineer",
    initials: "MT",
    image: "/team/michelle.jpg" 
  },
  {
    name: "Nancy Wangare",
    role: "Data Scientist",
    initials: "NW",
    image: "/team/nancy.jpg"
  },
  {
    name: "David Guchu",
    role: "Data Scientist",
    initials: "DG",
    image: "/team/david.jpg"
  }
];

export default function ReCoverLanding() {
  const [activeArea, setActiveArea] = useState<MitumbaFocus>(MITUMBA_AREAS[0]);
  const [activeJargon, setActiveJargon] = useState<number>(0);
  const [showPlain, setShowPlain] = useState<boolean>(true);

  return (
    <div className="min-h-screen bg-[#FBF9F4] text-[#1E1E1E] font-sans antialiased selection:bg-[#EBDBC9] selection:text-[#1F4E38]">
      
      {/* --- Top Navigation --- */}
      <header className="sticky top-0 z-40 border-b border-[#E8E2D5] bg-[#FBF9F4]/90 backdrop-blur-md px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="font-serif text-2xl font-bold tracking-tight text-[#1F4E38]">
              ReCover
            </span>
          </Link>

          <nav className="flex items-center gap-6">
            <a 
              href="#about" 
              className="hidden text-xs font-semibold uppercase tracking-wider text-[#5A5347] hover:text-[#1F4E38] transition sm:block"
            >
              How It Works
            </a>
            <a 
              href="#jargon" 
              className="hidden text-xs font-semibold uppercase tracking-wider text-[#5A5347] hover:text-[#1F4E38] transition sm:block"
            >
              Insurance Terms
            </a>
            <a 
              href="#team" 
              className="hidden text-xs font-semibold uppercase tracking-wider text-[#5A5347] hover:text-[#1F4E38] transition sm:block"
            >
              Team
            </a>
            <a
              href="#about"
              className="inline-flex items-center gap-1.5 rounded-full border border-[#D5C7B2] bg-white px-4 py-2 text-xs font-bold text-[#1F4E38] transition hover:bg-[#F3EFE6]"
            >
              <span>Explore ReCover</span>
              <ArrowDown className="h-3 w-3" />
            </a>
          </nav>
        </div>
      </header>

      {/* --- Section 1: Hero --- */}
      <section className="px-6 pt-20 pb-16 sm:pt-28 sm:pb-24">
        <div className="mx-auto max-w-3xl text-center">
          
  

          <h1 className="font-serif text-4xl sm:text-6xl font-normal leading-[1.15] text-[#1A1A1A]">
            Microinsurance, explained simply for mitumba traders.
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-[#5C564B]">
            Affordable insurance options exist, but understanding what they cover and how to access them shouldn’t be complicated. ReCover breaks down terms in plain language and helps you discover options relevant to your stock.
          </p>

          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/chat"
              className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#1F4E38] px-7 py-3.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#163828] sm:w-auto"
            >
              <span>Open Chat Advisor</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            
            <a
              href="#about"
              className="inline-flex w-full items-center justify-center rounded-full border border-[#D5C7B2] bg-white px-6 py-3.5 text-sm font-semibold text-[#3E382E] transition hover:bg-[#F3EFE6] sm:w-auto"
            >
              Learn More
            </a>
          </div>

          <p className="mt-5 text-xs text-[#8C8373]">
            Recover with ReCover.
          </p>
        </div>
      </section>

      {/* --- Section 2: The Real Problem We Address --- */}
      <section id="about" className="border-t border-[#E8E2D5] bg-[#F4EFE6] px-6 py-16 sm:py-24">
        <div className="mx-auto max-w-4xl">
          <div className="max-w-2xl">
            <span className="text-xs font-bold uppercase tracking-widest text-[#C86D32]">
              The Awareness Gap
            </span>
            <h2 className="font-serif text-2xl sm:text-3xl leading-snug text-[#1E1E1E] mt-2">
              Microinsurance exists. The challenge is knowing what applies to your business.
            </h2>
            <p className="mt-4 text-sm sm:text-base leading-relaxed text-[#564F42]">
              Microinsurance products already exist in Kenya. The barrier is that many traders have never been introduced to them, find the paperwork confusing, or are unsure whether any policy truly makes sense for a clothing stall.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-[#D8CEBA] bg-[#FDFBF7] p-5 space-y-2">
              <span className="font-mono text-xs font-bold text-[#C86D32]">01</span>
              <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">Discovery</h3>
              <p className="text-xs text-[#5C5547] leading-relaxed">
                Many traders simply don&apos;t know affordable micro-options exist. ReCover introduces what is available without pressure.
              </p>
            </div>

            <div className="rounded-2xl border border-[#D8CEBA] bg-[#FDFBF7] p-5 space-y-2">
              <span className="font-mono text-xs font-bold text-[#C86D32]">02</span>
              <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">Clarity</h3>
              <p className="text-xs text-[#5C5547] leading-relaxed">
                Terms like premiums, claims, and exclusions are explained immediately in clear language, not dense legal clauses.
              </p>
            </div>

            <div className="rounded-2xl border border-[#D8CEBA] bg-[#FDFBF7] p-5 space-y-2">
              <span className="font-mono text-xs font-bold text-[#C86D32]">03</span>
              <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">Relevance</h3>
              <p className="text-xs text-[#5C5547] leading-relaxed">
                We focus on your actual trade—helping identify options built around stock turnover and everyday realities.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* --- Section 3: Mitumba Realities Explorer --- */}
      <section className="px-6 py-16 sm:py-24 border-t border-[#E8E2D5]">
        <div className="mx-auto max-w-4xl">
          <div className="max-w-xl">
            <span className="text-xs font-bold uppercase tracking-widest text-[#1F4E38]">
              Initial Focus Area
            </span>
            <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#1A1A1A] mt-1">
              Grounded in the realities of mitumba trade.
            </h2>
            <p className="mt-2 text-sm text-[#635D51]">
              Our initial research and knowledge base are focused specifically on second-hand clothes traders.
            </p>
          </div>

          {/* Interactive Trade Pillars */}
          <div className="mt-8 flex flex-wrap gap-2 border-b border-[#E8E2D5] pb-3">
            {MITUMBA_AREAS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveArea(item)}
                className={`rounded-full px-4 py-2 text-xs font-bold transition ${
                  activeArea.id === item.id
                    ? "bg-[#1F4E38] text-white shadow-xs"
                    : "bg-[#F3EFE6] text-[#554E41] hover:bg-[#EAE4D7]"
                }`}
              >
                {item.title}
              </button>
            ))}
          </div>

          <div className="mt-6 rounded-2xl border border-[#DFD6C3] bg-white p-6 sm:p-8">
            <h3 className="font-serif text-xl font-medium text-[#1A1A1A]">
              {activeArea.summary}
            </h3>
            
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#7A7160]">The Trade Reality:</span>
                <p className="mt-1 text-xs sm:text-sm text-[#564F42] leading-relaxed">
                  {activeArea.reality}
                </p>
              </div>

              <div className="rounded-xl bg-[#F4EFE6] p-4 border border-[#E5DECة border-[#E5DCCF]">
                <span className="text-xs font-bold uppercase tracking-wider text-[#1F4E38]">How ReCover Helps:</span>
                <p className="mt-1 text-xs sm:text-sm text-[#284C38] leading-relaxed">
                  {activeArea.howRecoverHelps}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <span className="text-xs text-[#8C8373] italic">
              * Note: ReCover is built first for mitumba trade, with plans to expand verified research to other informal business types as we grow.
            </span>
          </div>
        </div>
      </section>

      {/* --- Section 4: Plain-Language Jargon Translator --- */}
      <section id="jargon" className="border-t border-[#E8E2D5] bg-[#F3EFE6] px-6 py-16 sm:py-24">
        <div className="mx-auto max-w-3xl">
          <div className="text-center max-w-lg mx-auto mb-10">
            <span className="text-xs font-bold uppercase tracking-widest text-[#C86D32]">
              Plain-Language Demonstration
            </span>
            <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#1A1A1A] mt-1">
              Insurance terms without the confusion.
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-[#615A4C]">
              Select a term to see how ReCover explains essential insurance concepts.
            </p>
          </div>

          {/* Term Selector */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
            {JARGON_ITEMS.map((item, idx) => (
              <button
                key={item.term}
                onClick={() => setActiveJargon(idx)}
                className={`rounded-xl border p-3 text-center text-xs font-bold transition ${
                  activeJargon === idx
                    ? "border-[#1F4E38] bg-white text-[#1F4E38] shadow-xs"
                    : "border-[#D8CFBC] bg-[#FDFBF7] text-[#696152] hover:bg-white"
                }`}
              >
                {item.term}
              </button>
            ))}
          </div>

          {/* Interactive Card */}
          <div className="rounded-2xl border border-[#D5C9B5] bg-white p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-[#EFE9DD] pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#736B5E]">
                Term: <strong className="text-[#1A1A1A]">{JARGON_ITEMS[activeJargon].term}</strong>
              </span>

              <button
                type="button"
                onClick={() => setShowPlain(!showPlain)}
                className="text-xs font-bold text-[#1F4E38] hover:underline"
              >
                {showPlain ? "View contract wording" : "Switch to plain explanation"}
              </button>
            </div>

            <div className="py-6">
              {showPlain ? (
                <div className="space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#1F4E38]">
                    Plain Meaning:
                  </span>
                  <p className="font-serif text-lg sm:text-xl text-[#1F4E38] leading-snug">
                    {JARGON_ITEMS[activeJargon].plainText}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                    Typical Contract Language:
                  </span>
                  <p className="font-mono text-xs text-[#4A4337] bg-[#FBF9F4] p-3 rounded-lg border border-[#E8E2D5] leading-relaxed">
                    {JARGON_ITEMS[activeJargon].formalText}
                  </p>
                </div>
              )}

              <div className="mt-5 rounded-xl bg-[#FBF9F4] p-3.5 border border-[#EAE3D4]">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#736B5E]">
                  In Practice:
                </span>
                <p className="mt-0.5 text-xs text-[#4A4337] leading-relaxed">
                  {JARGON_ITEMS[activeJargon].example}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- Section 5: Meet the Team (Simplified) --- */}
      <section id="team" className="border-t border-[#E8E2D5] bg-[#F4EFE6] px-6 py-16 sm:py-20">
        <div className="mx-auto max-w-4xl">
          <div className="text-center mb-10">
            <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#1A1A1A]">
              Meet the Team
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-2xl mx-auto">
            {TEAM_MEMBERS.map((member) => (
              <div 
                key={member.name}
                className="rounded-2xl border border-[#D8CEBA] bg-[#FDFBF7] p-5 text-center flex flex-col items-center"
              >
                {/* Photo or Monogram */}
                <div className="relative mb-3 h-20 w-20 overflow-hidden rounded-xl border border-[#D5C9B5] bg-[#EBE4D3]">
                  {member.image ? (
                    <Image
                      src={member.image}
                      alt={member.name}
                      fill
                      sizes="80px"
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center font-serif text-lg font-bold text-[#1F4E38]">
                      {member.initials}
                    </div>
                  )}
                </div>

                <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">
                  {member.name}
                </h3>
                
                <p className="text-xs text-[#736B5E] mt-0.5">
                  {member.role}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- Section 6: Final Closing --- */}
      <section className="px-6 py-20 text-center bg-[#FBF9F4] border-t border-[#E8E2D5]">
        <div className="mx-auto max-w-xl space-y-4">
          <h2 className="font-serif text-3xl sm:text-4xl font-normal text-[#1A1A1A]">
            Have questions about microinsurance?
          </h2>

          <p className="text-sm text-[#5F584B]">
            Ask questions in plain language and explore what protection looks like for your stock.
          </p>

          <div className="pt-2">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 rounded-full bg-[#1F4E38] px-7 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-[#163828]"
            >
              <span>Open Chat Advisor</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <p className="pt-6 font-serif italic text-sm text-[#1F4E38]">
            Recover with ReCover.
          </p>
        </div>
      </section>

      {/* --- Footer --- */}
      <footer className="border-t border-[#E8E2D5] bg-[#F4EFE6] px-6 py-6 text-xs text-[#7A7365]">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-[#1F4E38]">ReCover</span>
            <span>—</span>
            <span>Microinsurance discovery for informal enterprise.</span>
          </div>
          <div>
            <span>© 2026 ReCover</span>
          </div>
        </div>
      </footer>

    </div>
  );
}