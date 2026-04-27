type Cell = { task: string; run: string; status: 'pass' | 'fail' }

const demo: Cell[] = Array.from({ length: 50 }).map((_, i) => ({
  task: `task-${Math.floor(i / 5)}`,
  run: `run-${i % 5}`,
  status: i % 7 === 0 ? 'fail' : 'pass',
}))

export function EvalHeatmap() {
  return (
    <section className="rounded-xl border border-slate-800 p-4">
      <h2 className="mb-3 text-sm font-semibold">Eval Heatmap (pass/fail)</h2>
      <div className="grid grid-cols-10 gap-1">
        {demo.map((cell) => (
          <button
            key={`${cell.task}-${cell.run}`}
            title={`${cell.task} ${cell.run} ${cell.status}`}
            className={`h-4 w-4 rounded-sm ${cell.status === 'pass' ? 'bg-emerald-500' : 'bg-red-500'}`}
          />
        ))}
      </div>
    </section>
  )
}
