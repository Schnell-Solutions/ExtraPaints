# ExtraPaints documentation

| Document | Purpose |
|----------|---------|
| **[OPERATIONS-GUIDE.md](OPERATIONS-GUIDE.md)** | **Start here** — deploy, update, backup, SSL, DNS, rollback |
| [SITE-TROUBLESHOOTING.md](SITE-TROUBLESHOOTING.md) | Site not loading, ports, LiteSpeed, SSL |
| [SEO-SITELINKS.md](SEO-SITELINKS.md) | Google sitelinks & Search Console |
| [../LEGACY-DATA-IMPORT.md](../LEGACY-DATA-IMPORT.md) | Import old SQLite catalog via CSV |
| [../DEPLOY-FRESH.md](../DEPLOY-FRESH.md) | First-time clean server install |
| [../DEPLOY-NOW.md](../DEPLOY-NOW.md) | Go live with empty DB + existing media |

**Routine production update:**

```bash
cd /home/james/extrapaints
./scripts/deploy.sh --pull
```
