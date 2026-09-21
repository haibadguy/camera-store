# Skill: Review Code / Fix Bug

## When to use
- Review má»™t pull request hoáº·c Ä‘oáº¡n code.
- Fix má»™t bug Ä‘Æ°á»£c bĂ¡o cĂ¡o.

## Steps

### 1. Äá»c ngá»¯ cáº£nh
- Äá»c `docs/coding-style.md` vĂ  `docs/architecture.md`.
- Náº¿u lĂ  bug: Ä‘á»c description vĂ  tĂ¬m hiá»ƒu cĂ¡ch tĂ¡i hiá»‡n.

### 2. Náº¿u review code
- Kiá»ƒm tra cĂ¡c váº¥n Ä‘á»:
  - [ ] CĂ³ tuĂ¢n theo `docs/coding-style.md` khĂ´ng?
  - [ ] CĂ³ vi pháº¡m anti-pattern nĂ o khĂ´ng?
  - [ ] CĂ³ truy cáº­p JPA/Hibernate + Flyway trá»±c tiáº¿p tá»« controller khĂ´ng?
  - [ ] CĂ³ throw domain-specific exception khĂ´ng?
  - [ ] CĂ³ validation Ä‘áº§u vĂ o Ä‘áº§y Ä‘á»§ khĂ´ng?
  - [ ] CĂ³ import vĂ²ng trĂ²n khĂ´ng?
- NĂªu cá»¥ thá»ƒ váº¥n Ä‘á» vĂ  Ä‘á» xuáº¥t cáº£i tiáº¿n.

### 3. Náº¿u fix bug
- XĂ¡c Ä‘á»‹nh nguyĂªn nhĂ¢n gá»‘c rá»….
- Sá»­a code.
- Náº¿u bug thĂº vá»‹ hoáº·c khĂ³: ghi vĂ o `docs/lessons.md` vá»›i cáº¥u trĂºc:
  ```markdown
  ## [Problem] MĂ´ táº£
  - **Cause**: ...
  - **Fix**: ...
  - **Prevention**: ...
  ```

### 4. Sau khi review/fix
- Náº¿u lĂ  PR, comment káº¿t quáº£ review.
- Náº¿u fix bug, tick checklist náº¿u cĂ³.

