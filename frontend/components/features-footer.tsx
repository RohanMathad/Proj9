'use client';

import { motion } from 'motion/react';
import { Bot, Zap, ShieldCheck, BrainCircuit, Globe, Terminal, ChartNetwork } from 'lucide-react'; // Added ChartNetwork

const FEATURES = [
  { icon: Bot, text: "Powered by Gemini 2.5 Flash" },
  { icon: Zap, text: "Real-time Voice Analysis" },
  { icon: BrainCircuit, text: "Adaptive Questioning" },
  { icon: ChartNetwork, text: "Custom ML Grading Engine" },
  { icon: Globe, text: "Multi-Company Simulation" },
  
  // YOUR NAME HIGHLIGHT
  { icon: Terminal, text: "Developed by Rohan Mathad © 2026" },
];

export function FeaturesFooter() {
  return (
    <footer className="fixed bottom-0 left-0 z-50 w-full overflow-hidden border-t border-white/10 bg-black/80 backdrop-blur-md">
      
      {/* Top Glow Line */}
      <div className="absolute top-0 left-0 h-[1px] w-full bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-50"></div>

      <div className="flex w-full items-center justify-center py-3"> 
        
        {/* ANIMATED MARQUEE */}
        <div className="relative flex w-full overflow-hidden whitespace-nowrap">
          <motion.div 
            className="flex gap-16 px-4"
            animate={{ x: ["0%", "-50%"] }}
            transition={{ 
              repeat: Infinity, 
              ease: "linear", 
              duration: 30, 
            }}
          >
            {[...FEATURES, ...FEATURES].map((feature, i) => (
              <div 
                key={i} 
                className={`flex items-center gap-2 text-xs font-medium transition-colors md:text-sm ${
                  feature.text.includes("Rohan") 
                    ? "text-indigo-400 font-bold" 
                    : "text-white/60 hover:text-white"
                }`}
              >
                <feature.icon className="h-4 w-4" />
                <span>{feature.text}</span>
              </div>
            ))}
          </motion.div>
          
          {/* Fade Edges */}
          <div className="pointer-events-none absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-black to-transparent"></div>
          <div className="pointer-events-none absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-black to-transparent"></div>
        </div>

      </div>
    </footer>
  );
}