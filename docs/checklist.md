# Development Checklist

## Phase 0: Contract vĂ  scope lock
- [ ] Specification, architecture, JPA entities vĂ  Flyway migrations thá»‘ng nháº¥t
- [ ] Wishlist items, inventory, camera specifications vĂ  behavior events Ä‘Ă£ chá»‘t
- [ ] Seed scenarios: guest, cold-start customer, active customer, admin
- [ ] Gate: migration cháº¡y tá»« database sáº¡ch vĂ  schema review Ä‘áº¡t

## Phase 1: Foundation vĂ  design system
- [ ] PostgreSQL cháº¡y báº±ng Docker Compose; Redis chÆ°a lĂ  dependency báº¯t buá»™c
- [ ] Config validation, global error format, Swagger vĂ  validation pipe
- [ ] Frontend routing, layout storefront/admin vĂ  shared UI states
- [ ] Seed catalog Ä‘á»§ cho browse vĂ  recommendation
- [ ] Gate: backend/frontend build pass, reset + seed pass

## Phase 2: Catalog vertical slice
- [ ] Product/category/brand/variant/image queries vĂ  CRUD
- [ ] Home, catalog, search, filter, sort, pagination
- [ ] Product detail, variant selection, stock display, review summary
- [ ] Camera specifications Ä‘Æ°á»£c lÆ°u vĂ  tráº£ qua API
- [ ] Gate: guest hoĂ n thĂ nh browse â†’ search/filter â†’ detail

## Phase 3: Identity vĂ  customer account
- [ ] Register, login, JWT, profile, update profile
- [ ] Password hashing, DTO validation, role guard
- [ ] Address CRUD vĂ  protected routes
- [ ] Auth loading/error/unauthorized states
- [ ] Gate: customer login Ä‘Æ°á»£c; admin API bá»‹ cháº·n Ä‘Ăºng role

## Phase 4: Customer flow vĂ  behavior
- [ ] Cart add/update/remove/clear
- [ ] Wishlist add/remove/list
- [ ] Review create/list vĂ  duplicate-purchase rule
- [ ] Track VIEW, ADD_TO_CART, WISHLIST
- [ ] Related products vĂ  recently viewed fallback
- [ ] Gate: customer browse â†’ save/cart â†’ review; events cĂ³ trong database

## Phase 5: Checkout vĂ  order operations
- [ ] Checkout DTO vĂ  stock validation
- [ ] JPA transaction: order, items, inventory, clear cart
- [ ] Fake payment, shipment status vĂ  order status
- [ ] Customer order history/detail
- [ ] Admin update order status
- [ ] Track PURCHASE sau order há»£p lá»‡
- [ ] Gate: khĂ´ng oversell, khĂ´ng partial order, checkout láº·p láº¡i Ä‘Æ°á»£c

## Phase 6: Recommendation engine
- [ ] Product feature dataset vĂ  behavior dataset
- [ ] Content-based vectorization vĂ  cosine similarity
- [ ] Python train/predict, artifact vĂ  model version
- [ ] Similar, personalized vĂ  cold-start APIs
- [ ] Score, reason, fallback vĂ  inactive/out-of-stock filtering
- [ ] Offline Precision@K, Recall@K, Hit Rate@K, coverage
- [ ] Gate: Ă­t nháº¥t ba user scenarios tráº£ káº¿t quáº£ khĂ¡c nhau vĂ  cĂ³ test relevance

## Phase 7: Admin, metrics vĂ  support
- [ ] Admin product/category/brand/variant/inventory/user management
- [ ] Coupon cÆ¡ báº£n
- [ ] Notification database vĂ  system log cho action quan trá»ng
- [ ] Recommendation dashboard vĂ  CTR tracking
- [ ] Redis chá»‰ thĂªm sau khi cĂ³ cache policy cá»¥ thá»ƒ
- [ ] Gate: admin váº­n hĂ nh Ä‘Æ°á»£c vĂ  xem Ä‘Æ°á»£c recommendation metrics

## Phase 8: Release
- [ ] Responsive, loading, empty, error vĂ  out-of-stock states
- [ ] Security review: auth, authorization, price, stock, secrets, CORS
- [ ] Backend/frontend/Docker build pass
- [ ] Swagger/OpenAPI cáº­p nháº­t
- [ ] Regression smoke flows pass tá»« database sáº¡ch
- [ ] Demo script, report, slides vĂ  deployment notes
- [ ] Gate: demo láº·p láº¡i Ä‘Æ°á»£c vĂ  cĂ³ evidence cho recommendation

