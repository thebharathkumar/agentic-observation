import { useEffect, useMemo, useState } from 'react'
import type { Span } from '../types/trace'

type Props = {
  spans: Span[]
}

export function TraceTimeline({ spans }: Props) {
  const [cursor, setCursor] = useState(0)
  const [playing, setPlaying] = useState(false)

  const current = spans[cursor]
  const total = spans.length

  useEffect(() => {
    if (!playing) return
    const timer = setInterval(() => {
      setCursor((c) => {
        if (c >= total - 1) {
          setPlaying(false)
          return c
        }
        return c + 1
      })
    }, 350)
    return () => clearInterval(timer)
  }, [playing, total])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === ' ') {
        e.preventDefault()
        setPlaying((v) => !v)
      }
      if (e.key === 'ArrowRight') setCursor((c) => Math.min(c + 1, total - 1))
      if (e.key === 'ArrowLeft') setCursor((c) => Math.max(c - 1, 0))
      if (e.key.toLowerCase() === 'j') setCursor((c) => Math.max(c - 10, 0))
      if (e.key.toLowerCase() === 'k') setCursor((c) => Math.min(c + 10, total - 1))
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [total])

  const parsedState = useMemo(() => {
    if (!current) return null
    return {
      input: current.input_json,
      output: current.output_json,
      error: current.exception_json,
    }
  }, [current])

  return (
    <section className="rounded-xl border border-slate-800 p-4">
      <div className="mb-3 flex items-center gap-2">
        <button onClick={() => setCursor(0)} className="rounded bg-slate-800 px-2 py-1 text-xs">rewind</button>
        <button onClick={() => setCursor((c) => Math.max(c - 1, 0))} className="rounded bg-slate-800 px-2 py-1 text-xs">step back</button>
        <button onClick={() => setPlaying((v) => !v)} className="rounded bg-cyan-700 px-2 py-1 text-xs">{playing ? 'pause' : 'play'}</button>
        <button onClick={() => setCursor((c) => Math.min(c + 1, total - 1))} className="rounded bg-slate-800 px-2 py-1 text-xs">step forward</button>
        <span className="ml-auto text-xs text-slate-400">{cursor + 1}/{total}</span>
      </div>

      <input
        type="range"
        min={0}
        max={Math.max(total - 1, 0)}
        value={cursor}
        onChange={(e) => setCursor(Number(e.target.value))}
        className="w-full"
      />

      <div className="mt-3 grid gap-3 md:grid-cols-3">
        {spans.map((span, i) => (
          <button
            key={span.id}
            onClick={() => setCursor(i)}
            className={`h-2 rounded ${i === cursor ? 'bg-cyan-400' : 'bg-slate-700'}`}
            aria-label={`span-${i}`}
          />
        ))}
      </div>

      {current && (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <div className="rounded bg-slate-900 p-3 text-xs">
            <h3 className="mb-2 font-semibold">Current Span</h3>
            <p>{current.name}</p>
            <p className="text-slate-400">{current.status}</p>
          </div>
          <pre className="overflow-auto rounded bg-slate-900 p-3 text-xs">{parsedState?.input}</pre>
          <pre className="overflow-auto rounded bg-slate-900 p-3 text-xs">{parsedState?.error ?? parsedState?.output}</pre>
        </div>
      )}
    </section>
  )
}
