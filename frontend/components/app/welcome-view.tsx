'use client';

import { Loader2, Code2, Globe, Cpu } from 'lucide-react';
import { FeaturesFooter } from '@/components/features-footer'; // <--- 1. IMPORT IT

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: (company: string) => void;
}

export function WelcomeView({ startButtonText, onStartCall }: WelcomeViewProps) {
  
  const handleCardClick = (company: string) => {
    console.log(`Clicked: ${company}`);
    onStartCall(company);
  };

  return (
    <div className="relative flex h-svh w-full items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-black overflow-hidden">
      
      {/* Background Glow */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.15),transparent_60%)]" />

      <div className="relative z-10 flex flex-col items-center gap-8 p-4 text-center">
        
        {/* Header Text */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-white md:text-5xl drop-shadow-lg">
            AI Interview System
          </h1>
          <p className="text-lg text-indigo-200/80">
            Select a role to customize your interview experience.
          </p>
        </div>

        {/* THE CARDS GRID */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          
          {/* GOOGLE CARD */}
          <CompanyCard 
            name="Google" 
            icon={<Globe className="h-10 w-10 text-red-400 group-hover:scale-110 transition-transform" />} 
            desc="Algorithms & Scalability"
            color="border-red-500/20 hover:border-red-500 hover:bg-red-500/10 hover:shadow-[0_0_30px_rgba(239,68,68,0.3)]"
            onClick={() => handleCardClick("GOOGLE")}
          />

          {/* META CARD */}
          <CompanyCard 
            name="Meta" 
            icon={<Code2 className="h-10 w-10 text-blue-400 group-hover:scale-110 transition-transform" />} 
            desc="System Design & Speed"
            color="border-blue-500/20 hover:border-blue-500 hover:bg-blue-500/10 hover:shadow-[0_0_30px_rgba(59,130,246,0.3)]"
            onClick={() => handleCardClick("META")}
          />

          {/* STARTUP CARD */}
          <CompanyCard 
            name="Startup" 
            icon={<Cpu className="h-10 w-10 text-green-400 group-hover:scale-110 transition-transform" />} 
            desc="Full Stack & Java"
            color="border-green-500/20 hover:border-green-500 hover:bg-green-500/10 hover:shadow-[0_0_30px_rgba(34,197,94,0.3)]"
            onClick={() => handleCardClick("STARTUP")}
          />

        </div>
      </div>

      {/* 2. ADD FOOTER HERE - IT WILL ONLY SHOW ON THIS SCREEN */}
      <FeaturesFooter />

    </div>
  );
}

// --- HELPER COMPONENT ---
function CompanyCard({ name, icon, desc, color, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={`group relative flex h-64 w-60 flex-col items-center justify-center gap-5 rounded-3xl border bg-black/40 p-6 backdrop-blur-xl transition-all duration-300 hover:-translate-y-2 cursor-pointer z-50 ${color}`}
    >
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white/5 ring-1 ring-white/10 group-hover:bg-white/10">
        {icon}
      </div>
      <div>
        <h3 className="text-2xl font-bold text-white">{name}</h3>
        <p className="mt-2 text-sm text-white/60">{desc}</p>
      </div>
    </button>
  );
}