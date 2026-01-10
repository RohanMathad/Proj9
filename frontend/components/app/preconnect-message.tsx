'use client';

import { AnimatePresence, motion } from 'motion/react';
import { type ReceivedChatMessage } from '@livekit/components-react';
import { ShimmerText } from '@/components/livekit/shimmer-text';
import { cn } from '@/lib/utils';

const MotionMessage = motion.create('p');

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface PreConnectMessageProps {
  messages?: ReceivedChatMessage[];
  className?: string;
}

export function PreConnectMessage({ className, messages = [] }: PreConnectMessageProps) {
  return (
    <AnimatePresence>
      {messages.length === 0 && (
        <MotionMessage
          {...VIEW_MOTION_PROPS}
          aria-hidden={messages.length > 0}
          className={cn(
            'pointer-events-none text-center text-white/80',
            className
          )}
        >
          <ShimmerText className="text-sm font-medium tracking-wide">
            AI interviewer is ready — start speaking when prompted
          </ShimmerText>
        </MotionMessage>
      )}
    </AnimatePresence>
  );
}
