# Gloam

A personal reading archive — the best writing from across the web, curated in one place.

Built with [Astro](https://astro.build), deployed on [Vercel](https://vercel.com).

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Framework | Astro 5 (static site generation) |
| Styling | Custom CSS with CSS custom properties (warm teal design system) |
| Content | MDX files in `src/content/posts/` |
| Fonts | Inter + JetBrains Mono (self-hosted via @fontsource) |
| Syntax highlighting | Shiki (dual theme: github-light / github-dark-dimmed) |
| Search | Pagefind (built at deploy time, zero-server) |
| Cloner | Python script in `cloner/` using trafilatura + markdownify |

Adding a new post = run the cloner → `git push` → live in ~30 seconds.

---

## Local Setup

**Requirements:** Node.js 22+, Python 3.10+

```bash
# 1. Install Node dependencies
npm install

# 2. Start dev server
npm run dev
# → http://localhost:4321

# 3. Build for production
npm run build

# 4. Preview production build
npm run preview
```

---

## Adding a Post (The Cloner)

```bash
# Install Python dependencies (one-time)
cd cloner
pip install -r requirements.txt

# Clone a post from any URL
python cloner.py "https://magazine.sebastianraschka.com/p/visual-attention-variants"

# Options
python cloner.py "https://..." --tags "ml,llm" --author "Jane Doe"
python cloner.py "https://..." --draft          # Save as draft, not published
python cloner.py "https://..." --skip-images    # Skip image downloading
```

The script will:
1. Fetch and extract the article content
2. Convert HTML → clean Markdown
3. Prompt you for any missing metadata (title, tags, description)
4. Download and convert images to WebP
5. Write `src/content/posts/YYYY-MM-DD--<slug>.mdx`

After cloning, preview with `npm run dev`, then:

```bash
git add src/content/posts/ public/images/
git commit -m "add: <post title>"
git push
# Vercel deploys automatically in ~30 seconds
```

---

## Folder Structure

```
Gloam/
├── src/
│   ├── content/
│   │   ├── config.ts          ← Zod schema (edit to add new fields)
│   │   └── posts/             ← All saved posts as MDX
│   ├── components/            ← Reusable UI components
│   ├── layouts/               ← Base, PageLayout, PostLayout
│   ├── pages/                 ← Routes
│   ├── styles/                ← theme.css (colors), typography.css
│   └── utils/                 ← posts.ts, tags.ts, reading-time.ts
├── cloner/                    ← Python cloner script
├── public/
│   └── images/posts/          ← Downloaded post images
└── dist/                      ← Build output (git-ignored)
```

---

## Deploy to Vercel

1. Push this repo to GitHub: `https://github.com/prathishpratt/gloam`
2. Go to [vercel.com](https://vercel.com) → "Add New Project"
3. Import the `gloam` repo
4. Framework: **Astro** (auto-detected)
5. Build command: `npm run build`
6. Output directory: `dist`
7. Click **Deploy**

Your site will be live at `https://gloam.vercel.app` (or your custom domain).

Every `git push` to `main` triggers an automatic redeploy.

### Deploy to Netlify (alternative)

```bash
# One-time setup
npm install -g netlify-cli
netlify login
netlify init

# Manual deploy
netlify deploy --prod
```

Or connect the GitHub repo at [app.netlify.com](https://app.netlify.com).

---

## Customization

| What to change | Where |
|----------------|-------|
| Site name / tagline | `src/pages/index.astro` hero section |
| Accent color | `src/styles/theme.css` → `--color-accent` / `--color-accent-hover` |
| Nav links | `src/components/Nav.astro` |
| Footer links / copyright | `src/components/Footer.astro` |
| About page text | `src/pages/about.astro` |
| Site URL (for RSS/sitemap) | `astro.config.mjs` → `site:` |
| Favicon | `public/favicon.svg` |
| Post frontmatter fields | `src/content/config.ts` (Zod schema) |

---

## GitHub Setup (first time)

```bash
# Authenticate GitHub CLI
gh auth login

# Create the repo and push
gh repo create gloam --public --source=. --remote=origin --push
```

Or manually:
```bash
git remote add origin https://github.com/prathishpratt/gloam.git
git push -u origin main
```

---

## Next Improvements

- [ ] Add Pagefind search UI (search bar in Nav)
- [ ] Dark mode cover image variants
- [ ] Reading list / "Want to read" bookmarks
- [ ] Newsletter integration (ConvertKit)
- [ ] Automated cloning via GitHub Action (paste URL in issue → auto-clones)
- [ ] Webmentions / reactions on posts
