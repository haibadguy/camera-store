# Agent Workflow and Phase Gates

## 1. XĂ¡c Ä‘á»‹nh nguá»“n sá»± tháº­t
Äá»c theo thá»© tá»±:

1. `AGENTS.md`
2. `docs/constitution.md`
3. `docs/decisions.md`
4. `docs/architecture.md`
5. `docs/plan.md`
6. `docs/checklist.md`

Specification mĂ´ táº£ scope sáº£n pháº©m; plan vĂ  checklist quyáº¿t Ä‘á»‹nh thá»© tá»± triá»ƒn khai.

## 2. Chá»n Ä‘Ăºng phase vĂ  vertical slice
- Má»—i task pháº£i ghi rĂµ phase, module, API/UI surface vĂ  acceptance criteria.
- KhĂ´ng báº¯t Ä‘áº§u phase má»›i khi gate cá»§a phase trÆ°á»›c chÆ°a Ä‘áº¡t.
- Æ¯u tiĂªn flow hoĂ n chá»‰nh tá»« database â†’ API â†’ UI â†’ smoke test.
- KhĂ´ng giao cho AI má»™t task bao phá»§ toĂ n bá»™ project.

## 3. TrÆ°á»›c khi code
- XĂ¡c Ä‘á»‹nh entity, authorization, validation, error cases vĂ  API response.
- Náº¿u Ä‘á»•i schema, kiá»ƒm tra quan há»‡ vĂ  migration trÆ°á»›c khi viáº¿t service.
- Náº¿u Ä‘á»•i recommendation, xĂ¡c Ä‘á»‹nh feature source, fallback vĂ  metric bá»‹ áº£nh hÆ°á»Ÿng.
- Giá»›i háº¡n file Ä‘Æ°á»£c phĂ©p thay Ä‘á»•i trong prompt/task.

## 4. Trong khi code
- TuĂ¢n theo `docs/coding-style.md`.
- Controller má»ng; business logic náº±m trong service/module.
- DĂ¹ng DTO validation cho input vĂ  Spring transaction cho checkout.
- KhĂ´ng tin giĂ¡, role hoáº·c stock do frontend gá»­i lĂªn.
- KhĂ´ng log password, token hoáº·c dá»¯ liá»‡u nháº¡y cáº£m.
- Cáº­p nháº­t Swagger khi API thay Ä‘á»•i.

## 5. Sau má»—i task
Cháº¡y kiá»ƒm tra nhá» nháº¥t phĂ¹ há»£p:

1. Typecheck/build cá»§a pháº§n vá»«a sá»­a.
2. Unit/service test cho logic má»›i.
3. API smoke test cho endpoint quan trá»ng.
4. Frontend flow test náº¿u sá»­a UI.
5. Flyway migration/seed check náº¿u sá»­a schema.

Vá»›i auth, cart, order, inventory vĂ  recommendation, khĂ´ng Ä‘Æ°á»£c chá»‰ dá»±a vĂ o build pass.

## 6. Gate cá»§a phase
Chá»‰ tick checklist khi cĂ³ evidence:

- command Ä‘Ă£ cháº¡y vĂ  káº¿t quáº£ pass;
- endpoint/UI flow Ä‘Ă£ kiá»ƒm tra;
- lá»—i chĂ­nh vĂ  boundary cases Ä‘Ă£ Ä‘Æ°á»£c xá»­ lĂ½;
- Swagger, schema hoáº·c docs Ä‘Ă£ Ä‘á»“ng bá»™ náº¿u cĂ³ thay Ä‘á»•i.

## 7. Káº¿t thĂºc task
- Kiá»ƒm tra `docs/done.md`.
- Cáº­p nháº­t `docs/checklist.md` Ä‘Ăºng má»¥c, khĂ´ng tick thay cho phase khĂ¡c.
- Cáº­p nháº­t `docs/lessons.md` khi cĂ³ lá»—i báº¥t thÆ°á»ng, migration issue hoáº·c quyáº¿t Ä‘á»‹nh má»›i.
- KhĂ´ng táº¡o abstraction, service hoáº·c dependency chá»‰ Ä‘á»ƒ lĂ m task â€œcĂ³ váº» Ä‘áº§y Ä‘á»§â€.

