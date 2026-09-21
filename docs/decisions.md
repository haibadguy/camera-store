# Architecture Decisions

## Decision 001: Use a modular monolith
**Status:** Accepted

**Reason:**
- The project scope is suitable for a single backend application.
- It is easier to develop, debug, and deploy than a distributed system.
- The team can keep the architecture simple while still separating business concerns.

**Tradeoffs:**
- The system cannot scale independently by module.
- Cross-module coupling must be managed carefully.

## Decision 002: Use Spring Boot packages as business boundaries
**Status:** Accepted

**Reason:**
- Spring Boot packages make the codebase easier to organize.
- Each module can own its own controller, service, and domain logic.
- This aligns well with the modular monolith approach.

## Decision 003: Keep recommendation logic isolated
**Status:** Accepted

**Reason:**
- Recommendation is a specialized feature with different processing needs.
- It is easier to evolve later if it has a dedicated boundary.
- The initial version can start with content-based filtering.

## Decision 004: Run recommendation training offline first
**Status:** Accepted

**Reason:**
- The project needs a reliable demo and repeatable evaluation more than realtime model training.
- Batch artifacts keep Python out of the request path and avoid introducing a second API service.
- Spring Boot remains the single runtime API for the frontend.

**Rules:**
- Python owns dataset preparation, training, batch inference and offline metrics.
- Spring Boot owns recommendation endpoints, authorization, filtering and presentation metadata.
- Every published artifact must have a model version and training timestamp.
- Realtime or hybrid algorithms are future extensions, not Phase 1 dependencies.

## Decision 005: Redis as cache layer for AI recommendations
**Status:** Accepted

**Reason:**
- The cosine similarity matrix and personalized recommendation responses are compute-heavy and should not query PostgreSQL repeatedly.
- Redis provides ultra-fast lookup (TTL: 1 hour) for `recommendations:similar:{productId}` and `recommendations:personalized:{userId}`.
- If Redis is down, Spring Boot falls back gracefully to in-memory cache or direct DB queries without breaking the user experience.


