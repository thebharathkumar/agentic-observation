import { PromptDiff } from './components/PromptDiff'
import { TraceTimeline } from './components/TraceTimeline'
import { EvalHeatmap } from './components/EvalHeatmap'
import type { Trace } from './types/trace'

const demoTrace: Trace = {
  id: 'demo-trace',
  name: 'customer-support-agent',
  status: 'ok',
  spans: Array.from({ length: 20 }).map((_, i) => ({
    id: `span-${i}`,
    name: `step-${i + 1}`,
    status: i === 13 ? 'error' : 'ok',
    started_at: `2026-04-27T00:00:${String(i).padStart(2, '0')}Z`,
    ended_at: `2026-04-27T00:00:${String(i + 1).padStart(2, '0')}Z`,
    input_json: JSON.stringify({ thought: `decide action ${i + 1}`, tool: i % 2 ? 'search_docs' : 'calculator' }, null, 2),
    output_json: JSON.stringify({ response: `result for step ${i + 1}` }, null, 2),
    exception_json: i === 13 ? JSON.stringify({ error: 'tool timeout' }, null, 2) : null,
  })),
}

export default function App() {
  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-bold">trace-replay</h1>
        <p className="text-sm text-slate-400">Scrub through agent traces like video and diff prompts across runs.</p>
      </header>
      <TraceTimeline spans={demoTrace.spans} />
      <PromptDiff
        left={'system: You are helpful.\nuser: summarize contract\nassistant: ...'}
        right={'system: You are a concise legal assistant.\nuser: summarize contract\nassistant: ...'}
      />
      <EvalHeatmap />
    </main>
  )
}
