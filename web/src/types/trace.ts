export type Span = {
  id: string
  name: string
  status: string
  started_at: string
  ended_at: string
  input_json: string
  output_json?: string | null
  exception_json?: string | null
}

export type Trace = {
  id: string
  name: string
  status: string
  spans: Span[]
}
