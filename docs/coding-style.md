# Coding Style

## NguyĂªn táº¯c chung
- DĂ¹ng `camelCase` cho biáº¿n vĂ  phÆ°Æ¡ng thá»©c.
- DĂ¹ng `PascalCase` cho class, component, vĂ  model.
- DĂ¹ng `kebab-case` cho tĂªn thÆ° má»¥c vĂ  file (trá»« khi framework yĂªu cáº§u khĂ¡c).

## Xá»­ lĂ½ lá»—i
- Æ¯u tiĂªn domain-specific exceptions thay vĂ¬ generic `Error`.
- Validate input á»Ÿ táº§ng DTO trÆ°á»›c khi vĂ o service.
- KhĂ´ng báº¯t lá»—i mĂ  khĂ´ng xá»­ lĂ½ (log vĂ  rethrow).

## Tá»• chá»©c module (backend Spring Boot)
- Má»—i module cĂ³ thÆ° má»¥c riĂªng dÆ°á»›i `backend/src/modules/`.
- BĂªn trong module: chia rĂµ `controllers`, `services`, `dto`.
- KhĂ´ng truy cáº­p database trá»±c tiáº¿p tá»« controller â€“ dĂ¹ng service.

## Logging
- DĂ¹ng logger cá»§a framework (SLF4J/Logback).
- Log á»Ÿ má»©c INFO cho cĂ¡c hoáº¡t Ä‘á»™ng bĂ¬nh thÆ°á»ng, ERROR cho ngoáº¡i lá»‡.
- KhĂ´ng log password, token, thĂ´ng tin cĂ¡ nhĂ¢n nháº¡y cáº£m.

## Database
- DĂ¹ng Spring Data JPA repository Ä‘á»ƒ truy váº¥n.
- KhĂ´ng viáº¿t SQL thĂ´ trá»« khi thá»±c sá»± cáº§n thiáº¿t vĂ  cĂ³ lĂ½ do rĂµ rĂ ng.
- Vá»›i cĂ¡c thao tĂ¡c ghi nhiá»u báº£ng, dĂ¹ng transaction.

## Module vĂ  phá»¥ thuá»™c
- TrĂ¡nh vĂ²ng láº·p import.
- Náº¿u hai module cáº§n dĂ¹ng chung logic, cĂ¢n nháº¯c táº¡o má»™t shared service hoáº·c module trung gian.

## Anti-patterns cáº§n trĂ¡nh
- âŒ Truy cáº­p repository trá»±c tiáº¿p trong Controller khi cáº§n business logic.
- âŒ Import vĂ²ng trĂ²n giá»¯a cĂ¡c service.
- âŒ Throw generic `Error`.
- âŒ DTO chá»©a logic nghiá»‡p vá»¥.
- âŒ Controller quĂ¡ dĂ y (nĂªn má»ng, chá»‰ nháº­n request vĂ  gá»i service).

