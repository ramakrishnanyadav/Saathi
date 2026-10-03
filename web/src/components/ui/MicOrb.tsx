import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';

interface Props {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function MicOrb({ onTranscript, disabled }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [volume, setVolume] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const animFrameRef = useRef<number>();

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      // Audio analysis for reactive rings
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        setVolume(avg / 128); // 0 to 1 scale
        animFrameRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        stream.getTracks().forEach((t) => t.stop());
        audioCtx.close();

        if (audioChunksRef.current.length > 0) {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const fd = new FormData();
          fd.append('audio', blob, 'voice.webm');
          fd.append('author_id', 'm-1');
          try {
            const res = await fetch('/api/v1/voice/ingest', {
              method: 'POST',
              headers: { 'X-House-Id': 'h-demo', 'X-Member-Id': 'm-1' },
              body: fd,
            });
            if (res.ok) {
              const data = await res.json();
              if (data.transcript) onTranscript(data.transcript);
            }
          } catch { /* Handled gracefully */ }
        }
        setIsRecording(false);
        setVolume(0);
      };

      mr.start();
      setIsRecording(true);
    } catch {
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  return (
    <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      {/* Audio-reactive pulsing ring */}
      {isRecording && (
        <motion.div
          animate={{ scale: 1 + volume * 0.6, opacity: 0.3 + volume * 0.5 }}
          transition={{ duration: 0.1 }}
          style={{
            position: 'absolute',
            inset: -12,
            borderRadius: '50%',
            background: 'radial-gradient(circle, var(--ember-glow) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Mic orb button */}
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        aria-label={isRecording ? 'Stop voice recording' : 'Start voice recording'}
        style={{
          width: 52,
          height: 52,
          borderRadius: '50%',
          border: '1.5px solid var(--glass-edge)',
          background: isRecording
            ? 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)'
            : 'linear-gradient(135deg, var(--diya) 0%, var(--brass) 100%)',
          color: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          boxShadow: isRecording ? 'var(--shadow-ember)' : 'var(--shadow-diya)',
          transition: 'all 200ms ease',
        }}
      >
        {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
      </button>
    </div>
  );
}
