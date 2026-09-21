# Project Constitution

## Vai trĂ² file nĂ y
File cá»‘ Ä‘á»‹nh. ÄĂ¢y lĂ  bá»™ quy táº¯c lĂ m viá»‡c khĂ´ng nĂªn thay Ä‘á»•i trong suá»‘t dá»± Ă¡n trá»« khi cĂ³ quyáº¿t Ä‘á»‹nh kiáº¿n trĂºc lá»›n.

## 1. Architecture rules
- Prefer a modular monolith over microservices.
- Keep domains separated by Spring Boot packages/modules.
- Avoid over-engineering unless the requirement clearly needs it.

## 2. Development rules
- Build features incrementally.
- Keep code readable and consistent.
- Use JPA entities and Flyway migrations as the single source of truth for database modeling.
- Avoid introducing new services unless necessary.

## 3. Recommendation rules
- Recommendation logic should be isolated in a dedicated module.
- Start with content-based filtering.
- Keep the integration path simple: Spring Boot reads Python artifacts or calls a lightweight wrapper.
- Do not overcomplicate the first version.

## 4. Documentation rules
- Update documentation whenever major features are added.
- Keep architecture notes and implementation docs synchronized.

## 5. Quality rules
- Validate backend and frontend builds before considering work complete.
- Ensure key flows work: auth, product browsing, cart, order, recommendation.
- Keep the project ready for defense and demo.

