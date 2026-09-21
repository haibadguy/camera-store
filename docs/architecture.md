# Architecture Notes

## Overall Architecture
Project dĂ¹ng modular monolith - má»™t á»©ng dá»¥ng Spring Boot duy nháº¥t, cĂ¡c package tĂ¡ch biá»‡t theo business domain.

Docker Compose lĂ  mĂ´i trÆ°á»ng cháº¡y vĂ  chuáº©n hĂ³a local/deployment, khĂ´ng pháº£i ranh giá»›i
microservice. `backend` váº«n lĂ  má»™t Spring Boot application/deployment duy nháº¥t.

## Module Boundaries
- `auth`: authentication & authorization
- `users`: user profile & account
- `products`: catalog, categories, variants
- `cart`: shopping cart
- `orders`: order & checkout flow
- `reviews`: product reviews
- `wishlist`: saved products
- `user-behavior`: behavior tracking cho recommendation
- `recommendations`: recommendation logic (isolated)

## Business Context
**Actors:**
- **Guest**: xem sáº£n pháº©m, tĂ¬m kiáº¿m.
- **User (Ä‘Ă£ Ä‘Äƒng kĂ½)**: thĂªm giá», wishlist, Ä‘áº·t hĂ ng, viáº¿t review.
- **Admin**: quáº£n lĂ½ sáº£n pháº©m, Ä‘Æ¡n hĂ ng, ngÆ°á»i dĂ¹ng.

**Core Workflows:**
1. Duyá»‡t sáº£n pháº©m â†’ xem chi tiáº¿t
2. ThĂªm vĂ o giá» â†’ cáº­p nháº­t sá»‘ lÆ°á»£ng â†’ checkout
3. Äáº·t hĂ ng â†’ payment placeholder
4. Viáº¿t review (1-5 sao, comment)
5. Wishlist (lÆ°u sáº£n pháº©m yĂªu thĂ­ch)
6. Recommendation (gá»£i Ă½ sáº£n pháº©m tÆ°Æ¡ng tá»±)

**Data Relationships:**
- User â†’ Cart (1-1)
- User â†’ Order (1-n)
- Product â†’ Category (n-1)
- Cart â†’ CartItem (1-n)
- Order â†’ OrderItem (1-n)

## Dependency Map
- **Auth** â†’ Users
- **Products** â†’ Categories
- **Cart** â†’ Users, Products
- **Orders** â†’ Users, Products, Cart
- **Reviews** â†’ Users, Products
- **Wishlist** â†’ Users, Products
- **UserBehavior** â†’ Users, Products
- **Recommendations** â†’ Products, UserBehavior

## Data Layer
- **PostgreSQL**: main data store
- **JPA/Hibernate + Flyway**: persistence and migration source of truth
- **Redis**: optional cache layer

## Recommendation Boundary
Recommendation logic náº±m trong service/module Spring Boot riĂªng. Python á»Ÿ `ai/recommendation/` phá»¥ trĂ¡ch
dataset preparation, training, offline evaluation vĂ  batch inference; nĂ³ khĂ´ng cháº¡y nhÆ° má»™t
Python microservice. Artifact/version do pipeline táº¡o ra Ä‘Æ°á»£c Spring Boot Ä‘á»c Ä‘á»ƒ phá»¥c vá»¥ API.
PhiĂªn báº£n Ä‘áº§u dĂ¹ng content-based filtering vĂ  cĂ³ cold-start fallback.

## Runtime Composition
- `frontend`: React SPA.
- `backend`: má»™t Spring Boot modular monolith, phá»¥c vá»¥ REST API.
- `postgres`: database chĂ­nh qua JPA/Flyway.
- `redis`: cache tĂ¹y chá»n cho recommendation vĂ  cĂ¡c dá»¯ liá»‡u phĂ¹ há»£p.
- `ai/recommendation`: component Python cháº¡y batch/offline Ä‘á»ƒ táº¡o model hoáº·c recommendation artifact;
	khĂ´ng cĂ³ API/deployment Ä‘á»™c láº­p.

