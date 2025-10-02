# Project Context: Document Search & Retrieval System

**Last Updated:** October 2, 2025
**Project Status:** Technical Design Complete - Ready for Development

---

## Project Overview

### Mission
Build an AI-powered document search and retrieval system to help the internal sales department quickly find information about custom-built machines from scattered PDF documentation.

### Problem Being Solved
- **Current State:** Sales agents spend 30 minutes to 4 hours searching through PDF documents to answer customer requests about maintenance, operations, and spare parts
- **Target State:** Agents find accurate information in <3 minutes using AI-powered semantic search
- **Impact:** 90% time reduction = significant cost savings and improved customer satisfaction

### Project Approach
**Phase 1 (Current):** Document Storage & Search System (PDF Only)
- Ingest and parse PDF documents
- Convert to markdown and generate summaries
- Store with metadata and vector embeddings
- Enable semantic search and retrieval
- **Note:** Phase 1 focuses exclusively on PDF documents to accelerate delivery

**Phase 2 (Future):** Automated Request Understanding & Response Generation

**Phase 3 (Future):** Learning & Continuous Improvement

---

## Current Capabilities

### Existing Codebase
Located at: `/workspaces/doc-parser/`

**What We Have:**
- ✅ Python-based PDF parsing using **LandingAI ADE SDK**
- ✅ Model: `dpt-2-latest` for document parsing
- ✅ Successfully converts complex PDFs to clean markdown
- ✅ Preserves structure: tables, headings, lists, images, logos
- ✅ Working example in `playground.ipynb` with a 20-page URS document
- ✅ Virtual environment setup with dependencies

**Technology Stack:**
- Python 3.12
- LandingAI ADE SDK (`landingai-ade`)
- python-dotenv for environment management
- Jupyter notebooks for experimentation

**Sample Output:**
- Input: 20-page PDF "User Requirement Specification for Horizontal Cartoner"
- Output: Structured markdown with table IDs, anchor tags, image descriptions, flowcharts

### What We Need to Build

**Document Processing Pipeline:**
- Scale up existing PDF parser for production use
- Add document summarization (LLM-based)
- Extract metadata and entities (machine models, part numbers)

**Storage Layer:**
- Database for document metadata and references
- File storage for original PDF documents
- Elasticsearch for indexed content and full-text search

**Search & Retrieval:**
- Elasticsearch indexing (BM25 algorithm)
- Full-text search with fuzzy matching
- API endpoints for search and retrieval
- Highlighting and snippet extraction

**User Interface:**
- Search interface for sales agents
- Admin interface for document management

**Future Enhancements (Post-Phase 1):**
- Support for Word and Excel documents
- ELSER semantic search (hybrid with BM25)

---

## Product Planning Status

### Recent Updates (October 2, 2025)

**Elasticsearch Documentation Review:**
- Reviewed official Elasticsearch documentation and pricing
- **Key Finding:** Elasticsearch Basic tier is **completely FREE** for self-managed deployments
- **Updated TDD (v1.1)** with:
  - Accurate licensing information (Basic tier includes BM25, fuzzy matching, highlighting, security)
  - Comprehensive security configuration (API keys, RBAC, TLS/SSL)
  - Detailed infrastructure setup guide (single node → cluster scaling)
  - Complete cost analysis ($0 Elasticsearch license, ~$75/month MVP total)
  - Enhanced search implementation (fuzzy matching rules, boosting strategies, custom analyzers)
  - ELSER upgrade path (requires Platinum+ license at $125/month/node)
- **Background materials added:**
  - `/workspaces/doc-parser/background-material/elasticsearch.pdf` (GitHub README)
  - `/workspaces/doc-parser/background-material/elasticsearch-pricing.pdf` (Licensing tiers)

### Documents Created

1. **Product Requirements Document (PRD)**
   - Location: [tasks/prd-document-search-system.md](../tasks/prd-document-search-system.md)
   - Status: ✅ Complete (Draft v1.3 - PDF-only, Elasticsearch)
   - Contents:
     - Executive summary with problem statement and vision
     - 13 detailed user stories with acceptance criteria (PDF-focused)
     - Technical requirements (APIs, Elasticsearch indexing, architecture)
     - Elasticsearch BM25 search strategy (reuses existing patterns)
     - Success metrics (90% time reduction, >90% search accuracy)
     - Feature prioritization (MoSCoW)
     - Risks, dependencies, future phases

2. **Technical Design Document (TDD)**
   - Location: [docs/technical_design_document.md](./technical_design_document.md)
   - Status: ✅ Complete (v1.1 - Enhanced with Elasticsearch best practices)
   - Contents:
     - Complete system architecture and component diagrams
     - Technology stack with detailed justifications
     - **Elasticsearch 8.11+** with Basic tier (FREE) licensing
     - Data models (Elasticsearch index schemas, database tables)
     - API design (6 REST endpoints with full specs)
     - Document processing pipeline implementation
     - **Enhanced search implementation:** BM25 with fuzzy matching, boosting, custom analyzers
     - **Comprehensive security:** API keys, RBAC, TLS/SSL (Basic tier features)
     - **Detailed infrastructure setup:** Single node → cluster scaling guide
     - **Complete cost analysis:** $0 Elasticsearch + $0.0037/doc summarization = ~$75/month MVP
     - Performance optimization techniques
     - Code organization and project structure
     - Testing strategy (unit, integration, E2E)
     - 8-week development roadmap (4 phases)
     - Risk mitigation strategies
     - **Future enhancements:** ELSER semantic search (requires Platinum+ upgrade)

3. **Elasticsearch Reference Implementation**
   - Location: [docs/elasticsearch_reference.md](./elasticsearch_reference.md)
   - Status: ✅ Complete
   - Purpose: Reusable code patterns from existing Elasticsearch implementation
   - Contents: Index creation, search queries, summarization with Claude

4. **Context Session Document (This Document)**
   - Location: [docs/context_session.md](./context_session.md)
   - Status: ✅ Complete
   - Purpose: Quick reference for all team members and agents

5. **Project Instructions**
   - Location: [CLAUDE.md](../CLAUDE.md)
   - Status: ✅ Existing (updated with project overview)

---

## Key Decisions Made

### Technology Decisions

**✅ Document Parsing**
- **PDF:** LandingAI ADE SDK (`dpt-2-latest` model) - already validated
- **Rationale:** Focus exclusively on PDF parsing for Phase 1 to accelerate delivery
- **Future:** Word and Excel support deferred to future phases

**✅ Output Format**
- **Decision:** Markdown as normalized format
- **Rationale:** Human-readable, preserves structure, easy to process with LLMs

**✅ Elasticsearch Deployment**
- **Decision:** Self-hosted Elasticsearch cluster (Basic tier - FREE)
- **Version:** Elasticsearch 8.11+ (latest stable)
- **Licensing:** Basic tier is completely free for self-managed deployments
- **Options:**
  1. Self-hosted single node (MVP) ← Start here
  2. Self-hosted cluster (production scale - 3+ nodes)
  3. Elastic Cloud (managed service - if needed later)
- **Rationale:**
  - Leverage existing Elasticsearch experience
  - Basic tier includes all required features (BM25, fuzzy matching, highlighting, aggregations, security)
  - No license costs ($0/month)
  - Can upgrade to Platinum ($125/month/node) for ELSER if semantic search is needed
- **Next Step:** Deploy single-node Elasticsearch 8.11+ for development

**✅ LLM Provider for Summarization**
- **Decision:** Start with **Claude Haiku 3** for development and testing
- **Pricing:** $0.25 input / $1.25 output per MTok
- **Rationale:**
  - Most cost-effective option (68% cheaper than Haiku 3.5)
  - Fast response times (low latency)
  - Good quality for technical document summaries
  - 200K token context window (handles long documents)
  - Perfect for MVP and testing phase
- **Upgrade Path:** Can easily upgrade to Claude Haiku 3.5 if quality needs improvement
  - Same API, just change model parameter
  - Decision based on real-world summary quality evaluation
- **Cost Optimization:**
  - Cache generated summaries in database to avoid re-generation
  - Monitor summary quality with real documents
- **Use Case:** Generate 150-300 word summaries of parsed PDF documents
- **Next Step:** Implement summarization with Claude Haiku 3 (`claude-3-haiku-20240307`)

**✅ Search Technology**
- **Decision:** **Elasticsearch** with BM25 full-text search
- **Rationale:**
  - Reuses existing Elasticsearch implementation patterns
  - No GPU requirements (simpler infrastructure)
  - Excellent for exact matching (part numbers, model names)
  - Proven technology with established best practices
  - Fuzzy matching for typo tolerance
  - Fast indexing and search performance
- **Future Enhancement:** Add ELSER for semantic search if needed
- **Next Step:** Set up Elasticsearch cluster (single node for MVP)

### Scope Decisions

**✅ Phase 1 Scope**
- **In Scope:**
  - PDF document upload, parsing, storage
  - Summarization (optional for MVP)
  - Elasticsearch indexing and BM25 search
  - Full-text search with fuzzy matching
  - Basic admin interface
- **Out of Scope:**
  - Word and Excel document support (deferred to future phases)
  - Semantic/vector search (deferred; ELSER in future)
  - Automated request understanding
  - Automated response generation
  - CRM/email integration
  - Multi-language support

**✅ MVP Features (Must Have)**
- PDF document upload (100MB max)
- PDF parsing with LandingAI (`dpt-2-latest`)
- Elasticsearch indexing with BM25 search
- Full-text search with fuzzy matching and highlighting
- Document retrieval with full content
- Basic admin panel

**✅ Nice-to-Have Features (Should Have)**
- Document summarization
- Search filters (category, date, machine model)
- Specific answer extraction (RAG)
- Document versioning
- Custom Elasticsearch analyzers for technical terms

---

## Open Questions

### Product Questions

**Q1: Who are the pilot users?**
- **Status:** ⏳ Awaiting response from sales manager
- **Action:** Identify 5 experienced + 2 beginner sales agents for pilot
- **Owner:** Product Manager / Sales Manager

**Q2: What are the document categories?**
- **Status:** ⏳ Needs input from documentation team
- **Action:** Map existing PDF documents to categories (maintenance, operations, spare parts, other)
- **Owner:** Documentation Manager

**Q3: How many PDF documents exist today?**
- **Status:** ⏳ Unknown
- **Action:** Inventory current PDF documentation (count, total size)
- **Owner:** Documentation Manager

**Q4: What are the most common machine models?**
- **Status:** ⏳ Needs input from sales/engineering
- **Action:** List top 20 machine models for entity extraction
- **Owner:** Sales Manager / Engineering

### Technical Questions

**Q5: Where will documents be stored?**
- **Status:** ⏳ Infrastructure decision needed
- **Options:** AWS S3, Azure Blob Storage, local file server
- **Action:** Architect to recommend based on existing infrastructure
- **Owner:** Technical Architect / DevOps

**Q6: What is the expected scale?**
- **Status:** ⏳ Estimate needed
- **Action:** Estimate total documents (current + 3-year growth), concurrent users
- **Owner:** Product Manager + Sales Manager

**Q7: What authentication system should be used?**
- **Status:** ⏳ Integration decision needed
- **Options:** SSO (SAML/OAuth), LDAP, custom auth
- **Action:** Check existing company auth systems
- **Owner:** IT / Security

**Q8: What are the deployment requirements?**
- **Status:** ⏳ Infrastructure decision needed
- **Options:** Cloud (AWS/Azure/GCP), on-premise, hybrid
- **Action:** Align with company infrastructure policies
- **Owner:** DevOps / IT

**Q9: What Elasticsearch deployment is preferred?**
- **Status:** ⏳ Infrastructure decision
- **Action:** Decide on Elasticsearch deployment approach
- **Options:**
  - Self-hosted single node (MVP, simplest)
  - Self-hosted cluster (production scale)
  - Elastic Cloud managed service (easiest operations)
- **Owner:** DevOps / IT

---

## Next Steps

### Immediate Actions (This Week)

**1. Stakeholder Review & Validation**
- [ ] Share PRD and TDD with sales department for feedback
- [ ] Review with sales manager to validate user stories and metrics
- [ ] Identify pilot users (5 sales agents)
- [ ] Owner: Product Manager

**2. Document & Data Inventory**
- [ ] Count total documents (PDFs, Word, Excel)
- [ ] Measure total storage size
- [ ] Identify document categories
- [ ] List machine models and common entities
- [ ] Owner: Documentation Manager

**3. Technical Planning Kickoff**
- [x] Review PRD with technical architect
- [x] Make technology decisions (Elasticsearch, Claude Haiku 3)
- [x] Design system architecture (data pipeline, APIs, storage)
- [ ] Review TDD with development team
- [ ] Finalize infrastructure deployment strategy
- [ ] Owner: Technical Architect

### Near-Term Actions (Next 2-3 Weeks)

**4. Infrastructure & Environment Setup**
- [ ] Provision development, staging, production environments
- [ ] Set up databases (PostgreSQL + vector DB)
- [ ] Configure CI/CD pipeline
- [ ] Set up monitoring and logging
- [ ] Owner: DevOps Engineer

**5. Sprint Planning**
- [ ] Break down user stories into technical tasks
- [ ] Estimate effort for each task
- [ ] Define sprint structure (recommended: 2-week sprints)
- [ ] Create backlog in project management tool
- [ ] Owner: Tech Lead + Engineering Team

**6. UI/UX Design**
- [ ] Design search interface mockups
- [ ] Design admin interface mockups
- [ ] User flow diagrams
- [ ] Get feedback from pilot users
- [ ] Owner: UX Designer (or Product Manager if no designer)

**7. Data Preparation**
- [ ] Collect 50-100 sample documents for testing
- [ ] Clean and categorize sample documents
- [ ] Create test search queries
- [ ] Document current search process (time study)
- [ ] Owner: Product Manager + Sales Team

### Development Phase (Month 1-2)

**8. Build Phase 1 MVP**
- **Sprint 1:** Document upload and parsing (PDF, Word, Excel)
- **Sprint 2:** Storage, metadata extraction, embedding generation
- **Sprint 3:** Search and retrieval APIs
- **Sprint 4:** Basic UI and admin interface

**9. Testing & QA**
- Unit tests for all components
- Integration tests for document pipeline
- Performance testing (search response time)
- User acceptance testing with pilot group

### Pilot & Rollout (Month 3)

**10. Pilot Program**
- Deploy to 5 pilot users
- Collect feedback and measure metrics
- Iterate based on findings

**11. Full Rollout**
- Deploy to entire sales department
- Conduct training sessions
- Monitor metrics and provide support

---

## Success Criteria

### Phase 1 Success Metrics

**Primary:**
- ✅ 90% reduction in time to find information (30 min → <3 min)
- ✅ >90% search accuracy (relevant results in top 5)
- ✅ 80% user adoption within 3 months

**Technical:**
- ✅ Search response time <3 seconds (p95)
- ✅ Document parsing success rate >95%
- ✅ System uptime 99% during business hours

**User Satisfaction:**
- ✅ NPS score >40
- ✅ Positive feedback from pilot users

---

## Key Contacts & Stakeholders

**Product:**
- Product Manager: [To be assigned]
- Sales Manager: [To be assigned]
- Documentation Manager: [To be assigned]

**Engineering:**
- Technical Architect: [To be assigned]
- Backend Engineer: [To be assigned]
- Frontend Engineer: [To be assigned]
- DevOps Engineer: [To be assigned]

**Pilot Users:**
- [5 sales agents to be identified]

---

## References & Resources

### Documents
- [Product Requirements Document](../tasks/prd-document-search-system.md) (v1.3)
- [Technical Design Document](./technical_design_document.md) (v1.0)
- [Elasticsearch Reference Implementation](./elasticsearch_reference.md)
- [Project Overview (CLAUDE.md)](../CLAUDE.md)
- [Sample Notebook (playground.ipynb)](../playground.ipynb)

### Codebase
- Repository: `/workspaces/doc-parser/`
- Main branch: `main`
- Development environment: `.myenv/`

### External Resources
- LandingAI ADE SDK Documentation
- Elasticsearch 8.8+ Documentation
- Anthropic Claude API Documentation (Haiku 3)
- FastAPI Documentation

---

**Document End**

*This document is a living reference and should be updated as the project progresses.*
