import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'cyan' | 'violet' | 'success' | 'warning' | 'error' | 'default';
  size?: 'sm' | 'md';
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-full';

  const variantStyles = {
    cyan: 'bg-accent-cyan bg-opacity-10 text-accent-cyan border border-accent-cyan border-opacity-30',
    violet: 'bg-accent-violet bg-opacity-10 text-accent-violet border border-accent-violet border-opacity-30',
    success: 'bg-success bg-opacity-10 text-success border border-success border-opacity-30',
    warning: 'bg-warning bg-opacity-10 text-warning border border-warning border-opacity-30',
    error: 'bg-error bg-opacity-10 text-error border border-error border-opacity-30',
    default: 'bg-bg-card text-text-secondary border border-border-subtle'
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm'
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}>
      {children}
    </span>
  );
}
