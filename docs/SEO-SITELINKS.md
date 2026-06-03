# Google sitelinks (enhanced search results)

The indented sub-links under a main Google result (like the ChatGPT example) are called **sitelinks**. Google generates them **automatically** — you cannot pick exact titles or force them to appear. You *can* improve your chances by making site structure obvious.

## What we implemented on ExtraPaints

| Change | Purpose |
|--------|---------|
| **ItemList + SiteNavigationElement** JSON-LD (`#primary-navigation`) | Tells Google which sub-pages matter (invisible in page HTML) |
| **WebSite** schema with `hasPart`, `alternateName`, `inLanguage` | Links homepage entity to navigation and brand names |
| **Organization** logo as `ImageObject` | Supports brand icon/favicon in results |
| **Sitemap priorities** | Higher priority for product/color/contact/about pages |
| **Rich meta descriptions** | Better main-result snippet text |

Structured data is output on every page via `templates/base.html`.

## Pages we target for sitelinks

These match real ExtraPaints journeys (all **indexable**):

1. `/products/` — Paint products  
2. `/colors/` — Color library  
3. `/contact/` — Contact & quotes  
4. `/about/` — About ExtraPaints  
5. `/guides/` — Guides & resources  
6. `/portfolio/` — Project portfolio  

Quote/cart pages stay **noindex** (correct for UX, not ideal sitelink targets).

## Google Search Console (required)

1. Add property: `https://www.extrapaints.co.ke`  
2. Verify ownership (DNS TXT or HTML file)  
3. Submit sitemap: `https://www.extrapaints.co.ke/sitemap.xml`  
4. Request indexing for homepage after deploy  
5. Monitor **Performance → Search results** and **Enhancements → Unparsable structured data**

## Timeline

- Sitelinks usually appear only after Google trusts the site (often **weeks to months**)
- Brand searches (`extrapaints`, `extrapaints kenya`) show sitelinks first
- Generic queries may never show them

## What you cannot control

- Google chooses sitelink titles and order  
- Google may show fewer or different links than our JSON-LD list  
- Competitors with higher authority get sitelinks more often

## After deploy

```bash
cd /home/james/extrapaints
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build web nginx
```

Validate structured data:

- [Google Rich Results Test](https://search.google.com/test/rich-results) — test homepage URL  
- View page source — search for `"SiteNavigationElement"` and `"#primary-navigation"`
