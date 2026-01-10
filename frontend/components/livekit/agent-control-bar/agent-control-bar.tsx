'use client';

import { type HTMLAttributes, useCallback, useState } from 'react';
import { Track } from 'livekit-client';
import {
  useChat,
  useRemoteParticipants,
  useTrackVolume,
} from '@livekit/components-react';
import { ChatTextIcon, PhoneDisconnectIcon } from '@phosphor-icons/react/dist/ssr';
import { useSession } from '@/components/app/session-provider';
import { TrackToggle } from '@/components/livekit/agent-control-bar/track-toggle';
import { Button } from '@/components/livekit/button';
import { Toggle } from '@/components/livekit/toggle';
import { cn } from '@/lib/utils';
import { ChatInput } from './chat-input';
import { UseInputControlsProps, useInputControls } from './hooks/use-input-controls';
import { usePublishPermissions } from './hooks/use-publish-permissions';
import { TrackSelector } from './track-selector';

export interface ControlBarControls {
  leave?: boolean;
  camera?: boolean;
  microphone?: boolean;
  screenShare?: boolean;
  chat?: boolean;
}

export interface AgentControlBarProps extends UseInputControlsProps {
  controls?: ControlBarControls;
  onDisconnect?: () => void;
  onChatOpenChange?: (open: boolean) => void;
  onDeviceError?: (error: { source: Track.Source; error: Error }) => void;
}

/**
 * A control bar specifically designed for voice assistant interfaces
 */
export function AgentControlBar({
  controls,
  saveUserChoices = true,
  className,
  onDisconnect,
  onDeviceError,
  onChatOpenChange,
  ...props
}: AgentControlBarProps & HTMLAttributes<HTMLDivElement>) {
  const { send } = useChat();
  const participants = useRemoteParticipants();
  const [chatOpen, setChatOpen] = useState(false);
  const publishPermissions = usePublishPermissions();
  const { isSessionActive, endSession } = useSession();

  const {
    micTrackRef,
    cameraToggle,
    microphoneToggle,
    screenShareToggle,
    handleAudioDeviceChange,
    handleVideoDeviceChange,
    handleMicrophoneDeviceSelectError,
    handleCameraDeviceSelectError,
  } = useInputControls({ onDeviceError, saveUserChoices });

  // 🔊 READ-ONLY mic volume (0 → ~1)
  const micVolume = useTrackVolume(micTrackRef);
  const micGlow = Math.min(1, micVolume * 2.5);

  const handleSendMessage = async (message: string) => {
    await send(message);
  };

  const handleToggleTranscript = useCallback(
    (open: boolean) => {
      setChatOpen(open);
      onChatOpenChange?.(open);
    },
    [onChatOpenChange, setChatOpen]
  );

  const handleDisconnect = useCallback(async () => {
    endSession();
    onDisconnect?.();
  }, [endSession, onDisconnect]);

  const visibleControls = {
    leave: controls?.leave ?? true,
    microphone: controls?.microphone ?? publishPermissions.microphone,
    screenShare: controls?.screenShare ?? publishPermissions.screenShare,
    camera: controls?.camera ?? publishPermissions.camera,
    chat: controls?.chat ?? publishPermissions.data,
  };

  const isAgentAvailable = participants.some((p) => p.isAgent);

  return (
    <div
      aria-label="Voice assistant controls"
      className={cn(
        `
        relative flex flex-col gap-3
        rounded-3xl border border-white/10
        bg-gradient-to-br from-white/[0.08] to-white/[0.02]
        backdrop-blur-xl
        p-4
        shadow-[0_8px_40px_-10px_rgba(0,0,0,0.6)]
        `,
        className
      )}
      {...props}
    >
      {/* subtle ambient glow */}
      <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-r from-cyan-400/10 via-transparent to-violet-500/10" />

      {/* Chat Input */}
      {visibleControls.chat && (
        <ChatInput
          chatOpen={chatOpen}
          isAgentAvailable={isAgentAvailable}
          onSend={handleSendMessage}
        />
      )}

      <div className="relative flex items-center gap-2">
        {/* LEFT CONTROLS */}
        <div className="flex grow items-center gap-2">
          {/* 🎤 MIC WITH AUDIO-SYNCED GLOW */}
          {visibleControls.microphone && (
            <div
              className="relative flex items-center justify-center rounded-full"
              style={{
                boxShadow: microphoneToggle.enabled
                  ? `0 0 ${18 + micGlow * 26}px rgba(34,211,238,${
                      0.25 + micGlow * 0.45
                    })`
                  : 'none',
                transition: 'box-shadow 120ms ease-out',
              }}
            >
              <TrackSelector
                kind="audioinput"
                aria-label="Toggle microphone"
                source={Track.Source.Microphone}
                pressed={microphoneToggle.enabled}
                disabled={microphoneToggle.pending}
                audioTrackRef={micTrackRef}
                onPressedChange={microphoneToggle.toggle}
                onMediaDeviceError={handleMicrophoneDeviceSelectError}
                onActiveDeviceChange={handleAudioDeviceChange}
              />
            </div>
          )}

          {visibleControls.camera && (
            <TrackSelector
              kind="videoinput"
              aria-label="Toggle camera"
              source={Track.Source.Camera}
              pressed={cameraToggle.enabled}
              pending={cameraToggle.pending}
              disabled={cameraToggle.pending}
              onPressedChange={cameraToggle.toggle}
              onMediaDeviceError={handleCameraDeviceSelectError}
              onActiveDeviceChange={handleVideoDeviceChange}
            />
          )}

          {visibleControls.screenShare && (
            <TrackToggle
              size="icon"
              variant="secondary"
              aria-label="Toggle screen share"
              source={Track.Source.ScreenShare}
              pressed={screenShareToggle.enabled}
              disabled={screenShareToggle.pending}
              onPressedChange={screenShareToggle.toggle}
            />
          )}

          <Toggle
            size="icon"
            variant="secondary"
            aria-label="Toggle transcript"
            pressed={chatOpen}
            onPressedChange={handleToggleTranscript}
            className="data-[state=on]:bg-cyan-500/20 data-[state=on]:text-cyan-300"
          >
            <ChatTextIcon weight="bold" />
          </Toggle>
        </div>

        {/* RIGHT – END CALL */}
        {visibleControls.leave && (
          <Button
            variant="destructive"
            onClick={handleDisconnect}
            disabled={!isSessionActive}
            className="
              ml-1
              rounded-full
              px-4
              font-mono
              tracking-wide
              transition-all
              hover:scale-[1.04]
              hover:shadow-[0_0_24px_rgba(239,68,68,0.45)]
            "
          >
            <PhoneDisconnectIcon weight="bold" />
            <span className="hidden md:inline">END CALL</span>
            <span className="inline md:hidden">END</span>
          </Button>
        )}
      </div>
    </div>
  );
}
