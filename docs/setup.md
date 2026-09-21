# Camera Store Setup Guide

TĂ i liá»‡u nĂ y dĂ nh cho cáº£ ba thĂ nh viĂªn trong nhĂ³m. Hiá»‡n táº¡i repository má»›i á»Ÿ giai Ä‘oáº¡n
Foundation: cáº¥u trĂºc, tĂ i liá»‡u, Spring Boot/React skeleton vĂ  Flyway migration Ä‘Ă£ cĂ³; cĂ¡c API
nghiá»‡p vá»¥ chÆ°a Ä‘Æ°á»£c hoĂ n thiá»‡n.

## 1. MĂ´ hĂ¬nh cháº¡y thá»‘ng nháº¥t

```text
React SPA (frontend) -> REST API -> Spring Boot modular monolith (backend)
                                      |-> JPA/Flyway -> PostgreSQL
                                      |-> Redis (cache, optional)
                                      |-> ai/recommendation (Python ML files)
```

Docker Compose chá»‰ lĂ  cĂ¡ch cháº¡y mĂ´i trÆ°á»ng. `backend` váº«n lĂ  má»™t Spring Boot application duy
nháº¥t, khĂ´ng pháº£i nhiá»u microservice. Python chá»‰ phá»¥c vá»¥ training/inference/experiment,
khĂ´ng dá»±ng Python API riĂªng á»Ÿ giai Ä‘oáº¡n Ä‘áº§u.

Khi development, dĂ¹ng cĂ¡ch nĂ y:

- Docker: PostgreSQL vĂ  Redis.
- MĂ¡y local: Java/Maven vĂ  Vite.
- Python: chá»‰ setup khi báº¯t Ä‘áº§u Phase 6 Recommendation.

## 2. CĂ´ng cá»¥ cáº§n cĂ i trĂªn Windows

CĂ i cĂ¡c cĂ´ng cá»¥ sau trĂªn mĂ¡y cá»§a má»—i thĂ nh viĂªn:

- Git: https://git-scm.com/download/win
- Node.js LTS: https://nodejs.org/
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- VS Code: https://code.visualstudio.com/
- Python 3.11 hoáº·c má»›i hÆ¡n: https://www.python.org/downloads/

Sau khi cĂ i, má»Ÿ PowerShell má»›i vĂ  kiá»ƒm tra:

```powershell
git --version
node --version
npm --version
docker --version
docker compose version
python --version
```

Náº¿u `docker compose version` cháº¡y Ä‘Æ°á»£c nhÆ°ng lá»‡nh Docker bĂ¡o khĂ´ng káº¿t ná»‘i Ä‘Æ°á»£c API,
hĂ£y má»Ÿ Docker Desktop vĂ  chá» tráº¡ng thĂ¡i Docker Engine cháº¡y xong.

## 3. Nháº­n source code báº±ng Git

### ThĂ nh viĂªn Ä‘Ă£ cĂ³ quyá»n repository

```powershell
git clone <GITHUB_REPOSITORY_URL>
cd camera-store
git status
```

KhĂ´ng gá»­i folder báº±ng USB/ZIP Ä‘á»ƒ lĂ m source chĂ­nh. Má»—i ngÆ°á»i clone má»™t báº£n riĂªng vĂ 
Ä‘áº©y code qua branch.

### ThĂ nh viĂªn chÆ°a cĂ³ quyá»n

Chá»§ repository vĂ o GitHub: `Settings` -> `Collaborators` -> `Add people`, thĂªm GitHub
username cá»§a thĂ nh viĂªn. NgÆ°á»i Ä‘Æ°á»£c má»i pháº£i accept invitation rá»“i má»›i clone.

### Cáº¥u hĂ¬nh danh tĂ­nh Git má»™t láº§n trĂªn má»—i mĂ¡y

```powershell
git config --global user.name "TĂªn cá»§a báº¡n"
git config --global user.email "email-github-cua-ban@example.com"
git config --global init.defaultBranch main
```

Email nĂªn lĂ  email Ä‘Ă£ thĂªm vĂ o GitHub hoáº·c email `noreply` cá»§a GitHub.

## 4. CĂ i dependencies

Tá»« thÆ° má»¥c gá»‘c repository:

```powershell
cd backend
mvn -q clean test
cd ..\frontend
npm install
cd ..
```

KhĂ´ng commit `node_modules/`; `.gitignore` Ä‘Ă£ bá» qua chĂºng. Khi frontend thay Ä‘á»•i
`package.json` hoáº·c `package-lock.json`, má»i thĂ nh viĂªn cháº¡y láº¡i `npm install` trong `frontend/`.

## 5. Táº¡o database vĂ  Redis báº±ng Docker

Äáº£m báº£o Docker Desktop Ä‘ang cháº¡y, sau Ä‘Ă³ á»Ÿ thÆ° má»¥c gá»‘c:

```powershell
docker compose up -d postgres redis
docker compose ps
```

Káº¿t quáº£ mong Ä‘á»£i: hai service `postgres` vĂ  `redis` á»Ÿ tráº¡ng thĂ¡i running/healthy.

Kiá»ƒm tra nhanh:

```powershell
docker compose exec postgres pg_isready -U camera -d camera_store
docker compose exec redis redis-cli ping
```

Káº¿t quáº£ mong Ä‘á»£i láº§n lÆ°á»£t cĂ³ `accepting connections` vĂ  `PONG`.

Dá»«ng database khi khĂ´ng lĂ m viá»‡c:

```powershell
docker compose stop postgres redis
```

KhĂ´ng dĂ¹ng `docker compose down -v` trá»« khi muá»‘n xĂ³a toĂ n bá»™ database local vĂ  seed láº¡i
tá»« Ä‘áº§u.

## 6. Cháº¡y Flyway database láº§n Ä‘áº§u

Copy file mĂ´i trÆ°á»ng máº«u:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

File `backend/.env` máº·c Ä‘á»‹nh dĂ¹ng:

```text
DATABASE_URL=jdbc:postgresql://localhost:5432/camera_store
DATABASE_USERNAME=camera
DATABASE_PASSWORD=camera123
PORT=3000
```

Cháº¡y kiá»ƒm tra schema:

```powershell
cd backend
mvn -q clean test
cd ..
```

Flyway tá»± cháº¡y cĂ¡c migration trong `backend/src/main/resources/db/migration` khi á»©ng dá»¥ng
khá»Ÿi Ä‘á»™ng. CĂ³ thá»ƒ kiá»ƒm tra migration báº±ng:

```powershell
cd backend
mvn -q flyway:info
```

## 7. Cháº¡y á»©ng dá»¥ng development

Má»Ÿ hai terminal PowerShell riĂªng.

Terminal 1, backend:

```powershell
cd d:\camera-store\backend
mvn spring-boot:run
```

Backend dĂ¹ng URL: `http://localhost:3000/api`.

Terminal 2, frontend:

```powershell
cd d:\camera-store\frontend
npm run dev
```

Vite thÆ°á»ng dĂ¹ng URL: `http://localhost:5173`.

Dá»«ng tá»«ng tiáº¿n trĂ¬nh báº±ng `Ctrl+C`. KhĂ´ng cáº§n cháº¡y Docker backend/frontend trong lĂºc
lĂ m feature thĂ´ng thÆ°á»ng.

## 8. Kiá»ƒm tra Foundation Gate

Má»—i thĂ nh viĂªn cháº¡y cĂ¡c lá»‡nh sau vĂ  chá»‰ bĂ¡o â€œPhase 1 Ä‘áº¡tâ€ khi táº¥t cáº£ pass:

```powershell
cd d:\camera-store\backend
mvn -q clean test
cd ..\frontend
npm run build
cd ..
docker compose config --quiet
docker compose ps
```

Checklist chĂ­nh náº±m á»Ÿ [checklist.md](checklist.md). Chá»‰ tick má»¥c Ä‘Ă£ cĂ³ báº±ng chá»©ng kiá»ƒm tra.
Náº¿u Docker Engine chÆ°a cháº¡y, ghi rĂµ blocker thay vĂ¬ Ä‘Ă¡nh dáº¥u Ä‘áº¡t.

## 9. Quy trĂ¬nh Git cho nhĂ³m ba ngÆ°á»i

KhĂ´ng lĂ m trá»±c tiáº¿p trĂªn `main` trá»« khi cáº£ nhĂ³m thá»‘ng nháº¥t cho thay Ä‘á»•i nhá». Má»—i task
Ä‘i theo branch riĂªng:

```powershell
git switch main
git pull origin main
git switch -c feature/<ten-task>
```

VĂ­ dá»¥:

```powershell
git switch -c feature/auth-register
```

Sau khi code vĂ  kiá»ƒm tra:

```powershell
git status
git add backend frontend docs
# thĂªm cĂ¡c file khĂ¡c náº¿u task thá»±c sá»± cáº§n
git commit -m "feat: add register flow"
git push -u origin feature/auth-register
```

Táº¡o Pull Request trĂªn GitHub Ä‘á»ƒ thĂ nh viĂªn khĂ¡c review. Sau khi merge:

```powershell
git switch main
git pull origin main
git branch -d feature/auth-register
```

TrÆ°á»›c khi báº¯t Ä‘áº§u task má»›i, luĂ´n cáº­p nháº­t branch:

```powershell
git switch main
git pull origin main
```

KhĂ´ng commit cĂ¡c file sau:

- `backend/.env` hoáº·c báº¥t ká»³ `.env` tháº­t nĂ o.
- `node_modules/`, `dist/`, `build/`, `.venv/`.
- Password, JWT secret tháº­t, Cloudinary secret.

## 10. CĂ¡ch chia viá»‡c ban Ä‘áº§u

- ThĂ nh viĂªn 1: backend foundation, JPA/Flyway, auth/users.
- ThĂ nh viĂªn 2: frontend foundation, routing, API client, cĂ¡c page chĂ­nh.
- ThĂ nh viĂªn 3: catalog/products, sau Ä‘Ă³ cart/order hoáº·c recommendation theo phase.

CĂ¡c vai trĂ² cĂ³ thá»ƒ Ä‘á»•i, nhÆ°ng khĂ´ng Ä‘á»ƒ hai ngÆ°á»i cĂ¹ng sá»­a má»™t file lá»›n hoáº·c cĂ¹ng táº¡o
migration cho cĂ¹ng má»™t thay Ä‘á»•i. Schema change pháº£i Ä‘Æ°á»£c trao Ä‘á»•i trÆ°á»›c; migration
Ä‘Æ°á»£c commit cĂ¹ng code dĂ¹ng nĂ³.

## 11. Thá»© tá»± phase

1. Foundation: Docker PostgreSQL/Redis, Flyway migration/seed, build backend/frontend.
2. Identity: auth, users, addresses.
3. Catalog: products, categories, brands, variants, search/filter.
4. Customer Flow: cart, wishlist, reviews.
5. Commerce: orders, inventory, checkout, payment/shipment placeholder.
6. Recommendation: behavior tracking vĂ  content-based recommendation.
7. Admin and Support: admin, analytics, coupon, logs, Redis cache.
8. Release: regression, Swagger, deployment notes, report, slides, demo.

KhĂ´ng báº¯t Ä‘áº§u phase sau náº¿u exit gate cá»§a phase trÆ°á»›c chÆ°a Ä‘áº¡t. Chi tiáº¿t náº±m á»Ÿ
[plan.md](plan.md) vĂ  [workflow.md](workflow.md).

## 12. Sá»± cá»‘ thÆ°á»ng gáº·p

### `docker compose` khĂ´ng káº¿t ná»‘i Ä‘Æ°á»£c Docker API

Má»Ÿ Docker Desktop, Ä‘á»£i Docker Engine cháº¡y, rá»“i thá»­ láº¡i `docker compose ps`.

### Port `5432` hoáº·c `6379` Ä‘Ă£ Ä‘Æ°á»£c dĂ¹ng

Dá»«ng PostgreSQL/Redis cĂ i trá»±c tiáº¿p trĂªn mĂ¡y hoáº·c process Ä‘ang chiáº¿m port. KhĂ´ng Ä‘á»•i port
má»—i mĂ¡y má»™t kiá»ƒu náº¿u chÆ°a cáº­p nháº­t `DATABASE_URL` vĂ  trao Ä‘á»•i vá»›i nhĂ³m.

### Spring Boot khĂ´ng káº¿t ná»‘i Ä‘Æ°á»£c database

Kiá»ƒm tra ba Ä‘iá»u: Docker PostgreSQL Ä‘ang running, file `backend/.env` tá»“n táº¡i, vĂ  URL dĂ¹ng
`localhost:5432` khi backend cháº¡y trĂªn mĂ¡y local. Náº¿u backend cháº¡y trong Docker, URL pháº£i
trá» tá»›i hostname service `postgres`, khĂ´ng pháº£i `localhost`.

### Frontend bĂ¡o thiáº¿u `tsc` hoáº·c package

Cháº¡y láº¡i `npm install` trong `frontend/`. KhĂ´ng cĂ i package ngáº«u nhiĂªn á»Ÿ thÆ° má»¥c gá»‘c.

### Git bĂ¡o conflict

KhĂ´ng dĂ¹ng `git reset --hard` khi chÆ°a hiá»ƒu thay Ä‘á»•i. LÆ°u thay Ä‘á»•i Ä‘ang lĂ m, kĂ©o
`main`, giáº£i quyáº¿t conflict tá»«ng file, cháº¡y build, rá»“i má»›i commit tiáº¿p.

