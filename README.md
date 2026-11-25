# Applied AI Engineering

**Building, deploying and operating AI systems in production: LLM applications, RAG, agents and ML.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_API-8E75B2?logo=googlegemini&logoColor=white)

I'm **Marco López Prieto** (Madrid): Computer Engineering graduate (CUNEF) and MSc student in Business Analytics & Data Science (IE). This repository follows a week-by-week plan (November 2026 – September 2027) to build the engineering skills behind production AI systems, targeting **AI Engineer**, **Forward Deployed Engineer**, **ML Engineer** and **Software Engineer** roles.

The approach is hands-on: every week ends with working, tested code committed to this repository.

---

## Projects

| # | Project | What it shows | Status |
|:---:|---|---|:---:|
| 01 | [**CLI AI Assistant**](projects/01-cli-ai-assistant) | LLM APIs, tool calling, streaming, tests | In progress |
| 02 | **DocuChat** | RAG over PDFs with cited answers, evals, observability, AWS deployment, React + TypeScript frontend | Planned (Dec 2026 – Mar 2027) |
| 03 | **Support Agent** | LangGraph agent over a mock CRM: memory, human approval, MCP server, webhooks and queues, guardrails, agent evals | Planned (Apr – Jun 2027) |
| 04 | **ML in Production** | Model tracked with MLflow, served with FastAPI in Docker, with drift monitoring | Planned (Mar – Apr 2027) |

Each project README covers the problem, architecture, decisions and trade-offs, metrics (quality, cost, latency), what failed and how to run it.

---

## Progress

| Week | Topic | Status |
|:---:|---|:---:|
| 1 | Asynchronous Python (`asyncio`) and data validation with Pydantic | Done |
| 2 | REST API design with FastAPI | Done |
| 3 | Advanced Git and testing with Pytest | Done |
| 4 | LLM fundamentals: tokens, prompting and API usage | Done |
| 5 | Prompt engineering and structured outputs: [Code Analyzer](practice/semana5/code_analyzer.py) with Pydantic validation and retry | Done |
| 6–7 | Tool calling and Project 01: CLI AI Assistant | Next |
| 9–11 | Docker, pgvector, embeddings and DocuChat v0 | Planned |

Weekly exercises and code are described in the [practice log](practice/README.md). Algorithm practice is tracked in [`practice/algoritmos`](practice/algoritmos/README.md): **2 problems solved** (NeetCode 150).

_Last updated: end of week 5 (29 Nov 2026)._

---

## Roadmap

| Phase | Weeks | Period | Outcome |
|---|---|---|---|
| **1. Foundations** | 1–8 | Oct – Dec 2026 | Async Python, FastAPI, testing, LLMs, prompting, tool calling · **CLI AI Assistant** |
| **2. Winter sprint** | 9–11 | Dec 2026 – Jan 2027 | Docker, pgvector, embeddings · **DocuChat v0** |
| **3. RAG to production** | 12–23 | Jan – Apr 2027 | Evals, Langfuse, AWS, CI/CD, React + TypeScript · **DocuChat** with real users · **ML in Production** |
| **4. Agents** | 24–36 | Apr – Jul 2027 | LangGraph, memory, MCP, integrations, guardrails, agent evals · **Support Agent** |
| **5. Polish** | 37–48 | Jul – Sep 2027 | System design, interviews, project polish |

The full week-by-week plan, with what to do and how, is in [`resources/applied-ai-engineering-roadmap.md`](resources/applied-ai-engineering-roadmap.md) (Spanish). The original 48-week plan, [`resources/ai-engineer-roadmap-48weeks.md`](resources/ai-engineer-roadmap-48weeks.md), is kept as technical reference material.

---

## Repository structure

```
applied-ai-engineering/
├── practice/      Weekly exercises (see practice/README.md) and algorithm practice
├── projects/      Main projects and infrastructure (docker-compose)
└── resources/     Week-by-week roadmap, weekly log and technical reference
```

---

## Contact

- GitHub: [@MarcoLopezP10](https://github.com/MarcoLopezP10)

Feedback and suggestions on the code are always welcome.
