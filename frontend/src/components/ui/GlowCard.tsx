import { ReactNode } from 'react';

interface GlowCardProps {
  children: ReactNode;
  className?: string;
  glow?: boolean;
}

export default function GlowCard({ children, className = '', glow = true }: GlowCardProps) {
  const baseStyles = 'bg-bg-card border border-border-subtle rounded-xl transition-all duration-300';
  const glowStyles = glow ? 'hover:border-border-accent hover:shadow-glow-cyan' : '';

  return (
    <div className={`${baseStyles} ${glowStyles} ${className}`}>
      {children}
    </div>
  );
}
