# Greensoft Leadgen — Design Specification

- **Fecha**: 2026-04-25
- **Estado**: Pendiente de revisión por el usuario
- **Autor**: Sesión de brainstorming con Claude Code
- **Repo destino**: `greensofttech-usa-mx/greensoft-leadgen` (privado, por crear)
- **Dashboard URL**: `https://leads.greensofts.org`

---

## 1. Contexto y objetivo

Greensoft Technologies es una LLC con base en Chicago que ofrece dos servicios:

1. **Tech Recruitment** — colocación de ingenieros senior (QA, DevOps, Backend, Cloud, Data) en empresas US con talento nearshore desde México y Latinoamérica.
2. **QA Consulting** — testing manual y automatizado, integración CI/CD.

**Propuestas de valor**: 40–60% reducción de costo, mismo huso horario, hiring en 14 días, estructura legal en US (Chicago LLC).

**Clientes actuales**: Walmart, Coca-Cola FEMSA, Santander, Nike (entre otros).

**Objetivo del sistema**: automatizar la generación de leads B2B calientes — empresas US que están publicando vacantes IT/QA y son candidatas a comprar los servicios de Greensoft (recruitment o consulting).

**Hipótesis subyacente**: una empresa con 5+ vacantes IT abiertas hace 3+ semanas → está luchando para cubrir su pipeline → es prospecto caliente para nearshore staffing.

## 2. Out of scope (Fase 1)

- Mercado Latam (OCC, Computrabajo) → Fase 2
- Discovery automático de empresas nuevas → Fase 3
- Status compartido entre socios → Fase 2
- Tiered discovery (Adzuna/JSearch) → Fase 3
- Envío automático de correos → no en roadmap
- Integración con CRM (HubSpot, Pipedrive) → Fase 4
- Email tracking, follow-ups automáticos → Fase 4
- LinkedIn scraping → fuera de scope (riesgos legales/técnicos)

## 3. Arquitectura general

5 capas, ejecución coordinada por un cron diario en GitHub Actions:

```
                   ┌──────────────────────────────────┐
                   │  GitHub Actions — cron diario    │
                   │  07:00 CT                        │
                   └──────────────┬───────────────────┘
                                  │
       ┌──────────────────────────┼─────────────────────────┐
       ▼                          ▼                         ▼
┌──────────────┐         ┌──────────────────┐      ┌─────────────────┐
│ 1. SCRAPE    │ ──────▶ │ 2. FILTER        │ ───▶ │ 3. SCORE +      │
│              │         │   (Haiku 4.5)    │      │   MESSAGE       │
│ Greenhouse   │         │                  │      │   (Sonnet 4.6)  │
│ Lever        │         │ ¿Es lead real?   │      │                 │
│ OCC* Comp.*  │         │ Extrae fields    │      │ Score 0-100 +   │
│  *Fase 2     │         │                  │      │ outreach msg    │
└──────────────┘         └──────────────────┘      └────────┬────────┘
                                                            │
                                                            ▼
                                              ┌──────────────────────────┐
                                              │ 4. STORAGE (private repo)│
                                              │   data/leads.json        │
                                              └────────────┬─────────────┘
                                                           │
                                                           ▼
                                              ┌──────────────────────────┐
                                              │ 5. DASHBOARD (CF Pages)  │
                                              │   leads.greensofts.org   │
                                              │   • Cloudflare Access    │
                                              └──────────────────────────┘
```

**Decisiones arquitectónicas:**

- **Embudo IA en 2 pasos** (Haiku 4.5 → Sonnet 4.6): reduce ~70% del costo vs todo-Sonnet
- **Storage = JSON en repo privado**: sin DB, versionado git gratis, suficiente para volumen <5k leads activos
- **Cron único diario 07:00 CT**: leads listos antes de horario laboral del equipo
- **Idempotencia** vía `data/seen.json` con IDs estables `{ats}:{slug}:{job_id}`

## 4. Stack técnico

### Backend
- Python 3.11
- `httpx` (async HTTP) para fetch paralelo de ATS
- `anthropic` SDK oficial con prompt caching habilitado
- `pydantic` v2 para schemas y validación
- `pytest` para tests

### Frontend
- HTML + Vanilla JS + Alpine.js
- Tailwind CSS (CDN o pre-compilado)
- Sin framework SPA

### Hosting & Auth
- GitHub Actions: cron + scraper + IA + commit
- Cloudflare Pages: dashboard estático, deploy desde repo privado, **gratis**
- Cloudflare Access (Zero Trust): auth, gratis hasta 50 users
- Cloudflare DNS: ya configurado, dominio registrado en Cloudflare

### Servicios externos
- Anthropic API: Haiku 4.5 (filter) + Sonnet 4.6 (score + message)
- ATS públicos:
  - Greenhouse: `boards.greenhouse.io/{slug}`
  - Lever: `jobs.lever.co/{slug}`

## 5. Modelo de datos

### `data/leads.json`

Array de objetos `Lead`:

```json
{
  "lead_id": "greenhouse:airtable:5612345",
  "company": {
    "name": "Airtable",
    "ats_provider": "greenhouse",
    "ats_slug": "airtable",
    "homepage": "https://airtable.com",
    "linkedin": "https://linkedin.com/company/airtable",
    "country": "US",
    "size_estimate": "500-1000",
    "industry": "SaaS",
    "first_seen": "2026-04-25"
  },
  "active_jobs": [
    {
      "id": "5612345",
      "title": "Senior QA Automation Engineer",
      "url": "https://...",
      "location": "Remote - US",
      "remote_friendly": true,
      "posted_date": "2026-04-12",
      "days_open": 13,
      "tech_stack": ["Cypress", "TypeScript", "AWS"]
    }
  ],
  "qa_jobs_count": 2,
  "all_it_jobs_count": 8,
  "lead_score": 84,
  "score_breakdown": {
    "qa_relevance": 22,
    "company_size": 18,
    "urgency": 14,
    "nearshore_fit": 18,
    "deal_size": 12
  },
  "score_rationale": "SaaS mid-market (500-1000) con 2 QA y 6 IT abiertos +13 días. Stack moderno. JD menciona 'distributed' → nearshore-friendly.",
  "outreach_message": {
    "subject": "Helping Airtable close 8 senior IT roles in 14 days",
    "body": "Hi [name],\n\nNoticed Airtable's QA Automation role has been open 3+ weeks...",
    "channel": "email"
  },
  "status": "new",
  "first_seen": "2026-04-25",
  "last_updated": "2026-04-25T07:14:32Z"
}
```

### `data/seen.json`
Mapa `lead_id → last_seen_iso8601` para idempotencia.

### `data/feedback.json` (Fase 2)
Mapa `lead_id → { status, marked_by_user, note, timestamp }`.

### `seed/companies.json`
Lista inicial de ~200 empresas US:

```json
[
  { "name": "Airtable", "ats_provider": "greenhouse", "ats_slug": "airtable" }
]
```

## 6. Capa IA — scoring y generación de mensaje

### 6.1 Filtro (Claude Haiku 4.5)

Para cada vacante nueva, devuelve estructura:
- `is_lead_candidate: bool` — ¿IT/QA real, US-based?
- `extracted: { role, seniority, location, remote_friendly, urgency_signal }`

Si `is_lead_candidate=false`, descarta sin pasar al siguiente paso. **Esto recorta ~70% del input al modelo caro.**

### 6.2 Scoring + mensaje (Claude Sonnet 4.6)

Para empresas con ≥1 vacante candidata, agregadas a nivel empresa:

- `lead_score: int (0-100)`
- `score_breakdown`: 5 componentes (ver pesos abajo)
- `score_rationale: str`
- `outreach_message: { subject, body }`

### 6.3 Pesos de scoring

| Señal | Puntos | Lógica |
|---|---|---|
| **QA relevance** | /25 | ¿Vacantes QA? ¿Senior? Stack matches Greensoft (Selenium, Cypress, Playwright, k6) |
| **Company size** | /20 | Sweet spot 200–2,000 empleados (mid-market). <50 startup → no le importa nearshore. >5,000 enterprise → ciclo venta 6+ meses |
| **Urgency** | /20 | Vacantes >21 días = lucha por llenar. >45 días = muy alto. <7 días = no desesperados |
| **Nearshore fit** | /20 | Keywords JD: "remote", "distributed", "global", "Latin America". Bonus si ya tienen empleados Latam |
| **Deal size** | /15 | Total IT roles abiertos. 1-2 transactional. 5-10 good. 10+ potencial multi-rol |
| **Total** | **100** | **Threshold "caliente" = 70** |

### 6.4 Reglas del mensaje (system prompt)

**Forma:**
- ≤110 palabras totales
- Subject ≤8 palabras, específico, mencionando rol/beneficio
- Apertura: 1 oración con observación específica del prospecto (NO "I hope this email finds you well")
- Social proof: mencionar Walmart / Coca-Cola FEMSA / Nike
- Value prop: 40–60% cost reduction, zero timezone gap, 14-day hiring
- CTA: una sola pregunta cerrada al final

**Frases prohibidas:** revolutionize, leverage synergies, game-changing, in today's fast-paced world, synergize, cutting-edge, world-class, best-in-class, paradigm shift.

**Tono:** americano ejecutivo, directo, sin diminutivos.

**Idioma:** inglés (V1). Español para Latam (Fase 2).

### 6.5 Prompt caching

System prompt + few-shot examples (estáticos) → cached por Anthropic SDK. Reduce costo ~70% en ráfagas.

### 6.6 Determinismo

`temperature=0` para scoring (necesitamos reproducibilidad). `temperature=0.3` para generación de mensajes (algo de variación natural sin perder consistencia).

## 7. Dashboard

UI single-page, mobile-friendly, lee `leads.json` directamente.

```
┌────────────────────────────────────────────────────────────────────┐
│  Greensoft Leads          🔄 Last update: 7:00 AM CT  [User ▾]     │
├────────────────────────────────────────────────────────────────────┤
│  [Country ▾]  [Score > 70]  [Status: New]  [Industry ▾]            │
│  Sort: Score ↓                                       198 leads     │
├────────────────────────────────────────────────────────────────────┤
│  Score │ Company       │ Country │ QA  │ All IT │ Status            │
│   84   │ Airtable      │ 🇺🇸 US   │  2  │   8   │ ● New             │
│   78   │ Notion        │ 🇺🇸 US   │  1  │  12   │ ◐ Contacted       │
└────────────────────────────────────────────────────────────────────┘

   Click row → expansión con score breakdown, jobs, mensaje generado,
   botones de status (Contacted/Replied/Client/Dead).
```

### 7.1 Filtros y sort
- **Filtros**: country, score min, status, industry, has-QA-role
- **Sort**: score (desc default), days-open, company name, first-seen
- **Búsqueda**: por nombre de empresa (substring)

### 7.2 Status tracking — Fase 1

`localStorage` del navegador. Per-user, **NO compartido entre socios**.

**Limitación honesta**: cada socio ve su propio estado. Para coordinar manejamos un Google Sheet exportado manualmente.

### 7.3 Status tracking — Fase 2

Cloudflare Worker + KV store (gratis hasta 100k requests/día) → estado compartido en tiempo real.

### 7.4 Performance
- Tabla virtualizada en frontend → sin lag con 5,000+ leads
- `leads.json` cacheado por CF CDN, ETag para revalidación rápida

## 8. Autenticación

Cloudflare Access (Zero Trust):
- App self-hosted en `leads.greensofts.org`
- Identity Provider: One-time PIN (magic link al email)
- Policy: **allowlist explícita de emails Gmail** (cuentas personales de los socios)
  - `josefabianorozcolazaro@gmail.com`
  - [+ socios — agregados manualmente conforme se sumen]
- Sesión: 24h
- MFA: opcional (activable post-deploy)

**Setup**: 5 min en Cloudflare Zero Trust dashboard, cero código.

## 9. Manejo de errores y resiliencia

| Falla | Comportamiento |
|---|---|
| ATS individual caído | Skip ese provider, sigue con los demás. Log warning. |
| Claude API rate limit | Retry exponential backoff (3 intentos: 2/4/8s). Si falla, marca `needs_retry`. |
| JSON malformado | Log a `data/parse_errors.log`, continúa pipeline. |
| Git commit falla | Retry. Si falla 3 veces, abre GitHub Issue con error. |
| Cron job falla completo | GitHub manda email automático al admin del repo (default GH behavior). |

**Principio de oro**: una empresa o vacante con problema **nunca** rompe la corrida diaria entera.

## 10. Testing

### 10.1 Unit (pytest)
- Parsers de cada ATS contra fixtures JSON/HTML reales en `tests/fixtures/`
- Función de scoring contra "golden set" de 20 leads con score esperado (tolerancia ±5)
- Validación de schemas Pydantic

### 10.2 IA quality
- Set de 10 leads conocidos → score esperado en rango. `temperature=0` para reproducibilidad.
- **Linter de mensajes**: word count <110, no contiene frases prohibidas, subject <8 palabras. Mensajes que no pasan se marcan `needs_review`, no se exponen al equipo.

### 10.3 End-to-end smoke
- Semanal: pipeline completo contra una empresa conocida (ej: Airtable) en dry-run, sin commit, verificando shape.

### 10.4 CI
- Tests corren en GitHub Actions en cada PR
- `main` protegido: no se mergea sin tests verdes

## 11. Observabilidad

- **Daily commit message**: `"Daily leadgen YYYY-MM-DD: N companies → M postings → X hot, Y warm, Z cold | Cost: $0.62"`
- **GitHub Actions tab**: historial de runs, logs, status badges
- **Email automático** si una corrida falla (default GH behavior)
- **Webhook Slack/Discord** opcional Fase 2

## 12. Costos estimados

| Item | Volumen mensual | Costo |
|---|---|---|
| Claude Haiku 4.5 (filter) | ~3,000 calls × 1k tokens | ~$3 |
| Claude Sonnet 4.6 (score + msg) | ~600 calls × 3k tokens | ~$10 |
| GitHub Actions runner | ~150 min | $0 (free tier) |
| Cloudflare Pages + Access + DNS | — | $0 |
| **Total** | | **~$13 USD/mes** |

## 13. Estructura del repositorio

```
greensoft-leadgen/
├── .github/workflows/
│   └── daily-leadgen.yml       # cron + scrape + IA + commit
├── scraper/
│   ├── ats/
│   │   ├── greenhouse.py
│   │   ├── lever.py
│   │   └── base.py
│   ├── ai/
│   │   ├── filter.py           # Haiku
│   │   ├── score.py            # Sonnet
│   │   ├── message.py          # Sonnet
│   │   ├── linter.py           # message validation
│   │   └── prompts/
│   │       ├── filter.txt
│   │       ├── score.txt
│   │       └── message.txt
│   ├── models.py               # Pydantic schemas
│   └── main.py                 # entrypoint
├── dashboard/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── data/                   # synced from /data en build
├── data/
│   ├── leads.json
│   ├── seen.json
│   └── feedback.json           # Fase 2
├── seed/
│   └── companies.json          # ~200 empresas US iniciales
├── tests/
│   ├── fixtures/
│   ├── test_parsers.py
│   ├── test_scoring.py
│   ├── test_message_linter.py
│   └── test_ai_quality.py
├── docs/superpowers/specs/
│   └── 2026-04-25-greensoft-leadgen-design.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## 14. Roadmap por fases

### Fase 1 — MVP funcional (semanas 1-2)
| Día | Entregable |
|---|---|
| 1-2 | Repo + skeleton + GH Actions cron + secrets |
| 2-3 | Greenhouse scraper + seed list 200 empresas |
| 4 | Lever scraper |
| 5 | Claude scoring + message generation, prompts iterados |
| 6-7 | Dashboard estático (HTML + Alpine + Tailwind) |
| 8 | Deploy CF Pages + DNS + CF Access |
| 9-10 | Tests, error handling, docs, primera corrida en producción |

### Fase 2 — Latam + status compartido (semanas 3-4)
- OCC + Computrabajo scraping
- Mensajes en español
- Cloudflare Worker + KV → status compartido entre socios
- Botones "Contacted/Replied/Client/Dead" persistentes

### Fase 3 — Inteligencia (mes 2-3)
- Discovery automático vía Adzuna/JSearch API
- Feedback loop: re-entrenar criterios de scoring con leads marcados
- Tiered AI optimization

### Fase 4 — Crecimiento (mes 4+)
- Integración con HubSpot/Notion/Pipedrive
- Email tracking
- Generación de second-touch follow-up automática

## 15. Acceptance criteria — Fase 1

Al final de la semana 2:

- [ ] `leads.greensofts.org` accesible, autenticación CF Access funcionando
- [ ] Cron corre diariamente 07:00 CT sin intervención
- [ ] Genera ≥5 leads "calientes" (score >70) por día en promedio
- [ ] Mensajes generados pasan el linter (word count, frases prohibidas, subject)
- [ ] Tests unitarios verdes en CI
- [ ] Costo real medido en Anthropic console <$20/mo
- [ ] README documenta: cómo agregar empresa al seed, cómo cambiar pesos de scoring, cómo invitar socio nuevo

## 16. Decisiones diferidas / open questions

1. **Lista seed inicial** — armaremos en día 2. Fuente: BuiltIn top US tech 2025 + YC top companies + clientes históricos sugeridos por equipo Greensoft.
2. **Pesos exactos del scoring** — comenzamos con (25/20/20/20/15). Después de 2 semanas de uso real ajustamos según qué leads convierten en clientes.
3. **Estilo visual del dashboard** — usar Tailwind con paleta y fonts del repo `greensoft-landing` para consistencia de marca.
4. **Frases prohibidas del linter** — set inicial definido en sec. 6.4. Ampliamos según outputs reales que suenen "AI-generated".
5. **Frecuencia exacta del cron** — 07:00 CT diario. Reevaluar si saturamos al equipo de ventas.

---

**Próximo paso**: invocar la skill `superpowers:writing-plans` para generar el plan de implementación detallado tarea por tarea.
