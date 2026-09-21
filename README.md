# Camera Store

Monolithic camera e-commerce platform with a Spring Boot backend, React frontend, and a dedicated Python recommendation component.

## Structure

- `backend/`: Spring Boot API, JPA entities, and Flyway migrations
- `frontend/`: React + Vite UI
- `ai/`: recommendation training, inference, models, and experiments
- `docs/`: project source documentation, diagrams, report, and presentation materials
- `.ai/skills/`: reusable coding and review instructions for AI assistants

## Local stack

- PostgreSQL for the main database
- Redis for recommendation caching
- Docker Compose for local infrastructure

## Start here

New team members should follow [docs/setup.md](docs/setup.md) before implementing features.
The project uses a modular monolith: one Spring Boot backend, one React SPA, PostgreSQL,
Redis, and Python files for recommendation experiments. Docker containers are runtime
tooling, not microservices.


