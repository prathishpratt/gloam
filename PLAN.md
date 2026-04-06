# Gloam — Personal Blog Collection Website

## Context
Building a personal website called "Gloam" — not a blog for publishing original content, but a curated archive of interesting posts found around the web. The owner clones blog posts from various sites (Substack, Medium, personal blogs, course pages) and re-hosts them in a single, beautifully-designed personal collection. The core workflow is: find a URL → run a cloner script → post appears live on the site.

Design inspiration: eugeneyan.com — clean, minimal, content-first, dark/light mode.

---

## Architecture Decisions

### Framework: Astro
- Content Collections API gives type-safe frontmatter validation via Zod — if the cloner outputs wrong fields, build fails, not silently
- Adding a new post = drop one `.mdx` file, `git push`, done. No config changes.
- Ships zero JS by default (Lighthouse 100 achievable)
- MDX + Shiki syntax highlighting built-in (2 lines of config)
- Static export → deploys to Vercel free tier

### Styling: Custom CSS with CSS Custom Properties
- No Tailwind — a warm custom design system is easier to maintain as plain CSS variables
- Dual-theme (light/dark) via `[data-theme="dark"]` attribute on `<html>`
- Warm neutral palette (off-white `#FAFAF8`, not harsh white) — reduces eye strain for long reads
- Violet accent (`#8B6CF7`) — distinctive, not the cliché blue

### Content: MDX files in `src/content/posts/`
- File naming: `YYYY-MM-DD--<slug>.mdx` (chronological ordering from filesystem)
- Frontmatter schema enforced by Zod: title, source_url, source_site, original_author, date_saved, tags, etc.
- `<link rel="canonical" href="source_url">` in post head — ethical, prevents SEO harm to originals

### Cloner: Python script in `cloner/`
- `trafilatura` for content extraction (beats BeautifulSoup for "main content vs. boilerplate" detection)
- `markdownify` for HTML → Markdown conversion
- Site-specific extractors for Substack, Medium (different DOM structures, paywall handling)
- Downloads images → converts to WebP → saves locally
- Interactive CLI prompts for missing metadata (tags, description)

---

## Folder Structure

```
Gloam/                              ← New folder to create
├── astro.config.mjs
├── package.json
├── tsconfig.json
├── .gitignore
├── .env.example
├── vercel.json
├── netlify.toml
│
├── public/
│   ├── favicon.svg
│   ├── og-default.png
│   └── images/posts/<slug>/        ← Downloaded post images (WebP)
│
├── src/
│   ├── content/
│   │   ├── config.ts               ← Zod schema (CRITICAL: single source of truth)
│   │   └── posts/                  ← All cloned posts as MDX
│   │       └── YYYY-MM-DD--<slug>.mdx
│   │
│   ├── layouts/
│   │   ├── Base.astro              ← <html>, <head>, theme init script
│   │   ├── PostLayout.astro        ← Individual post wrapper
│   │   └── PageLayout.astro        ← Home/Collection/Tags/About wrapper
│   │
│   ├── components/
│   │   ├── Nav.astro
│   │   ├── Footer.astro
│   │   ├── ThemeToggle.astro       ← sun/moon button, reads localStorage
│   │   ├── PostCard.astro          ← Card for listing pages
│   │   ├── PostMeta.astro          ← Author, source badge, date, "View Original" link
│   │   ├── SourceBadge.astro       ← Colored pill (Substack=orange, Medium=black, etc.)
│   │   ├── TagBadge.astro
│   │   ├── CollectionFilter.astro  ← Only interactive island (tag/source filter)
│   │   ├── TableOfContents.astro   ← Sticky sidebar on desktop
│   │   └── Prose.astro             ← Typography wrapper for MDX content
│   │
│   ├── pages/
│   │   ├── index.astro             ← Home: hero + recent posts
│   │   ├── collection.astro        ← All posts, filterable
│   │   ├── about.astro
│   │   ├── tags/
│   │   │   ├── index.astro
│   │   │   └── [tag].astro
│   │   └── posts/
│   │       └── [...slug].astro     ← Dynamic post route
│   │
│   ├── styles/
│   │   ├── global.css
│   │   ├── theme.css               ← CRITICAL: all CSS custom properties
│   │   └── typography.css          ← Prose/reading styles
│   │
│   └── utils/
│       ├── posts.ts                ← getCollection helpers
│       ├── tags.ts
│       └── reading-time.ts
│
└── cloner/
    ├── cloner.py                   ← Main entry point: python cloner.py <url>
    ├── requirements.txt
    ├── extractors/
    │   ├── base.py
    │   ├── generic.py              ← trafilatura fallback
    │   ├── substack.py
    │   └── medium.py
    ├── processors/
    │   ├── html_cleaner.py
    │   ├── md_converter.py         ← markdownify pipeline
    │   └── image_handler.py        ← download + WebP convert
    └── templates/
        └── frontmatter.yaml.j2
```

---

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Hero + 6 most recent posts + link to full collection |
| `/collection` | All posts, filterable by tag and source site |
| `/posts/[slug]` | Individual post with ToC, PostMeta, source attribution |
| `/tags` | Tag cloud / all tags |
| `/tags/[tag]` | Posts filtered by tag |
| `/about` | What Gloam is, how it works |

---

## Design System

**Font:** Inter (self-hosted via `@fontsource/inter`) — no Google Fonts latency  
**Monospace:** JetBrains Mono (code blocks)  
**Base size:** 18px, line-height 1.75  
**Prose max-width:** 720px  

**Colors (light/dark via CSS variables):**
- Background: `#FAFAF8` / `#141412` (warm, not harsh)
- Text: `#1A1917` / `#E8E6E0`
- Accent: `#0D9488` / `#2DD4BF` (teal — user-selected)
- Muted: `#6B6860` / `#9B9890`
- Source badges: Substack=orange, Medium=black, Personal=green, Course=red

**Shiki themes:** `github-light` / `github-dark-dimmed` (dual-theme, tied to `[data-theme]`)

---

## Cloner Script Usage

```bash
cd Gloam/cloner
pip install -r requirements.txt

# Basic usage
python cloner.py "https://magazine.sebastianraschka.com/p/..."

# With pre-specified tags
python cloner.py "https://medium.com/..." --tags "ml,transformers" --author "Jane Doe"

# Save as draft (not shown on site until draft: false)
python cloner.py "https://..." --draft
```

Output: `src/content/posts/YYYY-MM-DD--<slug>.mdx` + images in `public/images/posts/<slug>/`

---

## End-to-End: URL → Live

1. `python cloner/cloner.py "<url>"` — creates MDX + downloads images
2. `npm run dev` — preview at localhost:4321
3. Edit `.mdx` if needed (it's plain text)
4. `git add . && git commit -m "add: <title>" && git push` — Vercel auto-deploys in ~30s

---

## GitHub Setup Steps

1. Create `Gloam/` folder in current working directory
2. `git init && git branch -M main`
3. Create GitHub repo `gloam` (public or private)
4. `git remote add origin https://github.com/<username>/gloam.git`
5. Initial commit and push

---

## Deployment

**Vercel (primary):**
- Connect GitHub repo in Vercel dashboard
- Framework: Astro (auto-detected)
- Build: `npm run build`, Output: `dist`
- Free domain: `gloam.vercel.app`
- Custom domain: add in Vercel dashboard → auto-HTTPS

**Netlify (alternative):**
- `netlify.toml` included with `command = "npm run build"` and `publish = "dist"`

**Domain options:**
- Free: `gloam.vercel.app` (ready immediately)
- Cheap paid: `gloam.xyz` (~$1-10/yr), `gloam.dev` (~$12/yr), `readgloam.com` (~$12/yr)

---

## Implementation Order

1. Create `Gloam/` folder, `git init`, create GitHub repo, initial commit
2. Scaffold Astro project: `npm create astro@latest`
3. Configure `astro.config.mjs` (MDX, Shiki dual-theme, sitemap)
4. Write `src/content/config.ts` (Zod schema)
5. Build CSS design system (`theme.css`, `global.css`, `typography.css`)
6. Build layout components (`Base.astro`, `PageLayout.astro`, `PostLayout.astro`)
7. Build UI components (`Nav`, `Footer`, `ThemeToggle`, `PostCard`, `PostMeta`, `SourceBadge`, `TagBadge`, `CollectionFilter`, `Prose`, `TableOfContents`)
8. Build pages (`index`, `collection`, `posts/[...slug]`, `tags`, `about`)
9. Add RSS feed (`@astrojs/rss`) and sitemap
10. Build cloner Python script (extractors → converter → image handler → file writer)
11. Write sample post MDX to verify end-to-end
12. Add `vercel.json` and `netlify.toml`
13. Deploy to Vercel, verify Lighthouse scores
14. Write README with exact setup, run, and deploy instructions

---

## Verification

- `npm run dev` — site runs at `localhost:4321`
- `npm run build` — build succeeds with no Zod errors
- `python cloner/cloner.py "<test-url>"` — creates a valid MDX file
- New post appears on home page and collection after build
- Dark/light toggle works, persists on reload (localStorage)
- Lighthouse: Performance ≥ 95, Accessibility ≥ 95, Best Practices 100, SEO 100
- Mobile layout correct at 375px width
- All original source links open correctly

---

## Confirmed Decisions

- **GitHub repo**: `https://github.com/prathishpratt/gloam` (public)
- **Domain**: `gloam.vercel.app` (free Vercel subdomain)
- **Accent color**: Teal `#0D9488` (light) / `#2DD4BF` (dark)
