# Lessons Learned

Chá»‰ ghi láº¡i khi cĂ³ sá»± cá»‘ báº¥t ngá», quyáº¿t Ä‘á»‹nh thiáº¿t káº¿ quan trá»ng hoáº·c lá»—i tĂ¡i diá»…n.

## Cáº¥u trĂºc má»™t bĂ i há»c

```markdown
## [Váº¥n Ä‘á»] MĂ´ táº£ ngáº¯n

- **Cause**: nguyĂªn nhĂ¢n gá»‘c rá»…
- **Fix**: cĂ¡ch Ä‘Ă£ sá»­a
- **Prevention**: cĂ¡ch trĂ¡nh láº·p láº¡i
```

---

## [VĂ­ dá»¥] Lá»—i circular dependency giá»¯a ProductService vĂ  CategoryService

- **Cause**: ProductService import CategoryService, CategoryService import ProductService.
- **Fix**: TĂ¡ch logic chung ra má»™t service trung gian.
- **Prevention**: Khi thiáº¿t káº¿, xĂ¡c Ä‘á»‹nh rĂµ module nĂ o á»Ÿ táº§ng tháº¥p hÆ¡n.

