// Deep Scan Workflow — project-architect (ultracode)
//
// Fan-out de scanner-agents (um por área funcional) em paralelo. Cada agente:
//   1. Segue agents/scanner.md e grava o relatório completo em <output_dir>/<area>.md (artefato)
//   2. Retorna um inventário ESTRUTURADO (schema validado) usado para síntese
//
// O agente principal (project-architect) lê o retorno estruturado + os .md e faz o
// diagnóstico. Este workflow NÃO interpreta nem propõe correções — só coleta fatos.
//
// Invocação (a partir da seção Deep Scan do SKILL.md):
//   Workflow({ scriptPath: "<skill_dir>/scripts/deep-scan.workflow.js",
//              args: { skill_dir, project_root, areas: [{ name, path }], output_dir? } })

export const meta = {
  name: 'project-architect-deep-scan',
  description: 'Deep Scan spec-driven: fan-out de scanner-agents (um por área funcional) em paralelo, output estruturado + .md por área.',
  phases: [{ title: 'Scan', detail: 'um scanner-agent por área funcional, em paralelo' }],
}

// Schema espelha as categorias de extração do agents/scanner.md.
// Os arrays são um índice conciso (top items, com file:line); o detalhe verbatim
// (schemas, contratos, types) vive no .md de cada área.
const SCANNER_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['area', 'summary', 'file_count', 'md_path'],
  properties: {
    area: { type: 'string', description: 'nome da área/diretório (igual ao solicitado)' },
    summary: { type: 'string', description: 'visão factual de 2-5 frases do que esta área faz' },
    file_count: { type: 'number', description: 'número de arquivos de fonte relevantes lidos' },
    total_lines: { type: 'number', description: 'aprox. linhas de código lidas (0 se desconhecido)' },
    stack: { type: 'array', items: { type: 'string' }, description: 'runtime, frameworks, libs com versão; serviços externos consumidos' },
    api_contracts: { type: 'array', items: { type: 'string' }, description: 'por endpoint/handler: "METHOD PATH — auth — validação: sim/não/parcial"' },
    data_stores: { type: 'array', items: { type: 'string' }, description: 'tabelas DB / key patterns KV / filas com shapes (conciso; verbatim no .md)' },
    auth_model: { type: 'array', items: { type: 'string' }, description: 'mecanismo de auth/authz por entry point' },
    business_rules: { type: 'array', items: { type: 'string' }, description: 'lógica condicional, thresholds, defaults — citar file:line' },
    error_handling: { type: 'array', items: { type: 'string' }, description: 'shape de erro, retries, timeouts, fallbacks, falhas silenciosas' },
    scheduled_jobs: { type: 'array', items: { type: 'string' }, description: 'cron/scheduled: schedule + o que faz' },
    shared_types: { type: 'array', items: { type: 'string' }, description: 'nomes+localização de tipos/interfaces compartilhados (verbatim no .md)' },
    tests: { type: 'array', items: { type: 'string' }, description: 'o que é testado, como rodar, e gaps (o que NÃO tem teste)' },
    connections: { type: 'array', items: { type: 'string' }, description: 'imports de fora da área, exports consumidos por outros, deps implícitas' },
    problems: { type: 'array', items: { type: 'string' }, description: 'código morto, imports quebrados, TODO/FIXME, inconsistências — file:line' },
    security_findings: { type: 'array', items: { type: 'string' }, description: 'só fatos, "O.x categoria — file:line — fato" (sem severidade)' },
    md_path: { type: 'string', description: 'caminho absoluto do .md completo gravado para esta área' },
  },
}

if (!args || !Array.isArray(args.areas) || args.areas.length === 0) {
  throw new Error('deep-scan.workflow: args.areas precisa ser um array não-vazio de { name, path }')
}
const skillDir = args.skill_dir || '.'
const root = args.project_root || '.'
const outDir = args.output_dir || '/tmp/project-scan'
const areas = args.areas

phase('Scan')
log(`Deep Scan: ${areas.length} área(s) → ${outDir}/[area].md (estruturado + artefato)`)

const results = await parallel(areas.map((a) => () =>
  agent(
    `You are a spec-driven codebase scanner for the project-architect skill.

Read the scanner instructions at ${skillDir}/agents/scanner.md and FOLLOW THEM EXACTLY to scan this area:
  - directory:    ${a.path}
  - project_root: ${root}
  - area name:    ${a.name}

Produce TWO outputs — both are REQUIRED:

1) ARTIFACT — first run \`mkdir -p ${outDir}\`, then write your FULL markdown report to:
     ${outDir}/${a.name}.md
   Include every extraction category (A–O) from scanner.md. Copy contracts, schemas and
   shared types VERBATIM. Do not skip files. Note what does NOT exist (no validation, no
   tests, no retries) — gaps are findings.

2) STRUCTURED — return the summary object per the provided schema. Set "area" to "${a.name}"
   and "md_path" to "${outDir}/${a.name}.md". The structured arrays are a concise index
   (top items, cite file:line); the FULL detail must live in the .md artifact.

Report FACTS only — do not assign severity or propose fixes. Diagnosis is the main agent's job.`,
    { label: `scan:${a.name}`, phase: 'Scan', schema: SCANNER_SCHEMA }
  )
))

const ok = results.filter(Boolean)
const dropped = areas.filter((_, i) => !results[i]).map((a) => a.name)
if (dropped.length) log(`⚠️ ${dropped.length} área(s) falharam e foram puladas: ${dropped.join(', ')} — reexecute o scan para elas`)
log(`${ok.length}/${areas.length} áreas escaneadas, ${ok.reduce((n, r) => n + (r.file_count || 0), 0)} arquivos lidos`)

// Retorno: dados estruturados por área + ponteiros para os .md. O agente principal
// sintetiza e diagnostica a partir daqui (lendo os .md para o detalhe verbatim).
return {
  output_dir: outDir,
  areas_scanned: ok.length,
  areas_requested: areas.length,
  areas_dropped: dropped,
  total_files: ok.reduce((n, r) => n + (r.file_count || 0), 0),
  md_paths: ok.map((r) => r.md_path),
  areas: ok,
}
