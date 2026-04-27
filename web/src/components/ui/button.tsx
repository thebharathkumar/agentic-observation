import * as React from 'react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary'
}

export function Button({ className = '', variant = 'default', ...props }: ButtonProps) {
  const base = 'rounded px-2 py-1 text-xs'
  const style = variant === 'default' ? 'bg-cyan-700 text-white' : 'bg-slate-800 text-slate-100'
  return <button className={`${base} ${style} ${className}`} {...props} />
}
