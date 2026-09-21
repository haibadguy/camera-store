# AGENTS.md

## Role
Báº¡n lĂ  AI assistant cho Camera Store - má»™t dá»± Ă¡n Ä‘á»“ Ă¡n thÆ°Æ¡ng máº¡i Ä‘iá»‡n tá»­ vá» mĂ¡y áº£nh. Sá»­ dá»¥ng modular monolith vá»›i Spring Boot, JPA/Hibernate + Flyway, PostgreSQL vĂ  React.

## Commands
- Backend dev: `cd backend && mvn spring-boot:run`
- Frontend dev: `cd frontend && npm run dev`
- Migration: Flyway runs automatically on Spring Boot startup; inspect with `cd backend && mvn flyway:info`
- Backend build: `cd backend && mvn clean package`
- Frontend build: `cd frontend && npm run build`

## Source of Truth
Khi thĂ´ng tin mĂ¢u thuáº«n, Æ°u tiĂªn theo thá»© tá»± sau:
1. `docs/constitution.md` â€“ nguyĂªn táº¯c khĂ´ng thay Ä‘á»•i
2. `docs/decisions.md` â€“ quyáº¿t Ä‘á»‹nh kiáº¿n trĂºc Ä‘Ă£ Ä‘Æ°á»£c cháº¥p nháº­n
3. `docs/architecture.md` â€“ kiáº¿n trĂºc tá»•ng thá»ƒ vĂ  business context
4. `docs/coding-style.md` â€“ quy táº¯c code cá»¥ thá»ƒ
5. `docs/workflow.md` â€“ quy trĂ¬nh lĂ m viá»‡c
6. `docs/checklist.md` â€“ tiáº¿n Ä‘á»™ task

## Scope
Dá»± Ă¡n nĂ y lĂ  Ä‘á»“ Ă¡n há»c táº­p. Æ¯u tiĂªn giáº£i phĂ¡p Ä‘Æ¡n giáº£n, dá»… báº£o trĂ¬.
KhĂ´ng giá»›i thiá»‡u cĂ¡c máº«u kiáº¿n trĂºc doanh nghiá»‡p (CQRS, Event Sourcing, DDD Ä‘áº§y Ä‘á»§, Hexagonal, Repository pattern chá»“ng cháº¥t) trá»« khi Ä‘Æ°á»£c yĂªu cáº§u rĂµ rĂ ng.
TrĂ¡nh táº¡o abstraction khĂ´ng cáº§n thiáº¿t.

## AI skills
- Implement feature: load `.ai/skills/implement-feature/SKILL.md`
- Review code / fix bug: load `.ai/skills/review-code/SKILL.md`

## Workflow
Thá»±c hiá»‡n theo workflow vĂ  phase gates trong `docs/workflow.md`.

## API Reference
Náº¿u dá»± Ă¡n dĂ¹ng Swagger/OpenAPI, coi Swagger lĂ  nguá»“n sá»± tháº­t duy nháº¥t cho API. KhĂ´ng cáº§n duy trĂ¬ file markdown riĂªng cho API contracts.

