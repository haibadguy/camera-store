# Camera Store Project Overview

## Má»¥c tiĂªu sáº£n pháº©m
XĂ¢y dá»±ng má»™t website thÆ°Æ¡ng máº¡i Ä‘iá»‡n tá»­ mĂ¡y áº£nh cĂ³ thá»ƒ demo nhÆ° má»™t sáº£n pháº©m Ä‘ang hoáº¡t Ä‘á»™ng: khĂ¡ch cĂ³ thá»ƒ tĂ¬m hiá»ƒu vĂ  mua hĂ ng tá»« Ä‘áº§u Ä‘áº¿n cuá»‘i, admin cĂ³ thá»ƒ váº­n hĂ nh dá»¯ liá»‡u, vĂ  há»‡ thá»‘ng recommendation cĂ³ thá»ƒ giáº£i thĂ­ch vĂ  Ä‘o lÆ°á»ng Ä‘Æ°á»£c.

## Hai má»¥c tiĂªu ngang nhau

### 1. E-commerce hoĂ n chá»‰nh
- Guest browse: home, catalog, search, filter, sort, pagination vĂ  product detail.
- Customer flow: register, login, profile, address, cart, wishlist, review, checkout vĂ  order tracking.
- Admin flow: product, category, brand, variant, inventory, order, user, coupon vĂ  dashboard cÆ¡ báº£n.
- Má»i mĂ n hĂ¬nh quan trá»ng cĂ³ loading, empty, error, unauthorized vĂ  out-of-stock states.

### 2. Recommendation lĂ  Ä‘iá»ƒm nháº¥n há»c thuáº­t
- Thu tháº­p `VIEW`, `ADD_TO_CART`, `PURCHASE` vĂ  cĂ¡c event má»Ÿ rá»™ng.
- Content-based recommendation lĂ  phiĂªn báº£n báº¯t buá»™c.
- CĂ³ cold-start fallback, lĂ½ do gá»£i Ă½, model artifact vĂ  API tĂ­ch há»£p vĂ o storefront.
- CĂ³ offline evaluation tá»‘i thiá»ƒu: Precision@K, Recall@K, Hit Rate@K, coverage vĂ  response time.
- CĂ³ khu vá»±c admin hiá»ƒn thá»‹ recommendation metrics.

## CĂ´ng nghá»‡
- Frontend: React, Vite, TypeScript, React Router, TanStack Query.
- Backend: Spring Boot, Java, REST API, Swagger, JWT, Bean Validation.
- Data: JPA/Hibernate, Flyway, PostgreSQL.
- Recommendation: Python, pandas, numpy, scikit-learn; cháº¡y batch/offline á»Ÿ phiĂªn báº£n Ä‘áº§u.
- Runtime: Docker Compose cho PostgreSQL; Redis chá»‰ dĂ¹ng sau khi cĂ³ use case cache cá»¥ thá»ƒ.

## Kiáº¿n trĂºc
DĂ¹ng modular monolith. Má»—i business domain náº±m trong má»™t package/module Spring Boot, nhÆ°ng chá»‰ cĂ³ má»™t backend deployment vĂ  má»™t database. KhĂ´ng tĂ¡ch microservice cho recommendation trong phiĂªn báº£n Ä‘áº§u.

## NguyĂªn táº¯c triá»ƒn khai
- LĂ m theo vertical slice: má»—i phase pháº£i táº¡o ra má»™t flow cháº¡y Ä‘Æ°á»£c á»Ÿ cáº£ API vĂ  UI.
- Chá»‘t database/API contract trÆ°á»›c khi giao AI sinh code.
- Má»—i task AI cĂ³ acceptance criteria, test case vĂ  file scope rĂµ rĂ ng.
- KhĂ´ng má»Ÿ rá»™ng feature má»›i khi exit gate cá»§a phase trÆ°á»›c chÆ°a Ä‘áº¡t.

