'use client';

import { useRef, useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useRoomContext } from '@livekit/components-react';
import { useSession } from '@/components/app/session-provider';
import { SessionView } from '@/components/app/session-view';
import { WelcomeView } from '@/components/app/welcome-view';
import { Loader2, Mail, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.5, ease: 'linear' },
};

export function ViewController() {
  const room = useRoomContext();
  const isSessionActiveRef = useRef(false);
  const { appConfig, isSessionActive, startSession } = useSession();

  // --- POST-INTERVIEW LOGIC ---
  const [showProcessing, setShowProcessing] = useState(false);
  const wasActive = useRef(false);

  useEffect(() => {
    // Detect when the session ENDS (Active -> Inactive)
    if (wasActive.current && !isSessionActive) {
      setShowProcessing(true);
      
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#3b82f6', '#10b981', '#6366f1']
      });

      const timer = setTimeout(() => {
        setShowProcessing(false);
      }, 6000);

      return () => clearTimeout(timer);
    }
    wasActive.current = isSessionActive;
  }, [isSessionActive]);
  
  isSessionActiveRef.current = isSessionActive;

  const handleAnimationComplete = () => {
    if (!isSessionActiveRef.current && room.state !== 'disconnected') {
      room.disconnect();
    }
  };

  return (
    <AnimatePresence mode="wait">
      
      {/* 1. SESSION VIEW (THE INTERVIEW) */}
      {isSessionActive && (
        <motion.div 
            key="session" 
            className="h-full w-full"
            {...VIEW_MOTION_PROPS}
            // ⚠️ FIXED: Handle animation completion here on the wrapper!
            onAnimationComplete={(definition) => {
                // Only disconnect when the 'exit' (hidden) animation finishes
                if (definition === 'hidden') {
                    handleAnimationComplete();
                }
            }}
        >
          <SessionView
            appConfig={appConfig}
            // Removed onAnimationComplete from here to fix the React warning
          />
        </motion.div>
      )}

      {/* 2. PROCESSING CARD (THE LOADING SCREEN) */}
      {!isSessionActive && showProcessing && (
        <motion.div
          key="processing"
          className="flex h-full w-full flex-col items-center justify-center p-4"
          {...VIEW_MOTION_PROPS}
        >
          <ProcessingCard />
        </motion.div>
      )}

      {/* 3. WELCOME VIEW (THE CARDS) */}
      {!isSessionActive && !showProcessing && (
        <motion.div 
            key="welcome" 
            className="h-full w-full"
            {...VIEW_MOTION_PROPS}
        >
          <WelcomeView
            startButtonText={appConfig.startButtonText}
            onStartCall={startSession}
          />
        </motion.div>
      )}

    </AnimatePresence>
  );
}

// --- THE PROCESSING CARD COMPONENT ---
function ProcessingCard() {
  return (
    <div className="relative w-full max-w-md overflow-hidden rounded-3xl border border-white/20 bg-black/60 p-10 text-center shadow-[0_0_50px_rgba(59,130,246,0.3)] backdrop-blur-xl">
      <div className="absolute -top-20 -left-20 h-40 w-40 rounded-full bg-blue-500/30 blur-[60px] animate-pulse"></div>
      <div className="absolute -bottom-20 -right-20 h-40 w-40 rounded-full bg-purple-500/30 blur-[60px] animate-pulse"></div>

      <div className="relative z-10 flex flex-col items-center gap-6">
        <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-tr from-blue-500/20 to-purple-500/20 ring-1 ring-white/20">
           <Loader2 className="h-10 w-10 animate-spin text-blue-400" />
           <div className="absolute inset-0 animate-ping rounded-full ring-1 ring-blue-500/30"></div>
        </div>

        <div className="space-y-1">
          <h2 className="text-3xl font-bold tracking-tight text-white">Analysis in Progress</h2>
          <p className="text-sm text-blue-200/60">Do not close this window</p>
        </div>
        
        <div className="w-full space-y-4 rounded-xl bg-white/5 p-4 text-left ring-1 ring-white/10">
          <StepItem text="Encrypting voice data..." delay="0s" color="text-blue-400" />
          <StepItem text="Calculating AI Confidence Score..." delay="1.5s" color="text-purple-400" />
          <StepItem text="Generating Performance Report..." delay="3s" color="text-green-400" />
        </div>

        <div 
          className="flex items-center gap-2 rounded-full bg-green-500/20 px-5 py-2 text-sm font-medium text-green-300 ring-1 ring-green-500/50"
          style={{ animation: 'fadeIn 0.5s ease-out forwards 4.5s', opacity: 0 }}
        >
          <Mail className="h-4 w-4" />
          <span>Report sent to Inbox!</span>
        </div>
      </div>
      <style jsx>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </div>
  );
}

function StepItem({ text, delay, color }: { text: string; delay: string; color: string }) {
  return (
    <div 
      className="flex items-center gap-3 text-sm font-medium text-white/80"
      style={{ animation: `fadeIn 0.5s ease-out forwards ${delay}`, opacity: 0 }}
    >
      <CheckCircle2 className={`h-5 w-5 ${color}`} />
      <span>{text}</span>
    </div>
  );
}