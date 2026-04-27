import { diff_match_patch, DIFF_DELETE, DIFF_EQUAL, DIFF_INSERT } from 'diff-match-patch'
import { useMemo } from 'react'

type Props = {
  left: string
  right: string
}

export function PromptDiff({ left, right }: Props) {
  const segments = useMemo(() => {
    const dmp = new diff_match_patch()
    const diffs = dmp.diff_main(left, right)
    dmp.diff_cleanupSemantic(diffs)
    return diffs
  }, [left, right])

  const changed = segments.filter(([op]) => op !== DIFF_EQUAL).length

  return (
    <section className="rounded-xl border border-slate-800 p-4">
      <h2 className="mb-2 text-sm font-semibold">What changed between these runs</h2>
      <p className="mb-3 text-xs text-slate-400">{changed === 0 ? 'No prompt changes' : `${changed} changed token block(s)`}</p>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="max-h-72 overflow-auto rounded bg-slate-900 p-3 text-xs">
          {segments.map(([op, text], i) => (
            <span
              key={`l-${i}`}
              className={op === DIFF_DELETE ? 'bg-red-500/30' : op === DIFF_EQUAL ? '' : 'opacity-30'}
            >
              {op === DIFF_INSERT ? '' : text}
            </span>
          ))}
        </div>
        <div className="max-h-72 overflow-auto rounded bg-slate-900 p-3 text-xs">
          {segments.map(([op, text], i) => (
            <span
              key={`r-${i}`}
              className={op === DIFF_INSERT ? 'bg-emerald-500/30' : op === DIFF_EQUAL ? '' : 'opacity-30'}
            >
              {op === DIFF_DELETE ? '' : text}
            </span>
          ))}
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-500">Semantic coloring: red=removed, green=added, neutral=unchanged.</p>
    </section>
  )
}
