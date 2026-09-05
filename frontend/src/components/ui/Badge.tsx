import { cn } from '../../lib/utils'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'auto-commit' | 'review' | 'new-activity' | 'neutral' | 'default'
  dot?: boolean
}

export function Badge({ className, variant = 'default', dot, children, ...props }: BadgeProps) {
  const variants = {
    'auto-commit': 'bg-status-auto-commit/15 text-status-auto-commit border border-status-auto-commit/30',
    review: 'bg-status-review/15 text-status-review border border-status-review/30',
    'new-activity': 'bg-status-new-activity/15 text-status-new-activity border border-status-new-activity/30',
    neutral: 'bg-white/10 text-textMuted border border-border',
    default: 'bg-white/10 text-textMuted border border-border',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-pill text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full',
            variant === 'auto-commit' && 'bg-status-auto-commit',
            variant === 'review' && 'bg-status-review',
            variant === 'new-activity' && 'bg-status-new-activity',
            variant === 'neutral' && 'bg-textMuted',
            variant === 'default' && 'bg-textMuted'
          )}
        />
      )}
      {children}
    </span>
  )
}