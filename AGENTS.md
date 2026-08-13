# Full Throttle Performance repository instructions

## Project boundaries

- Treat this directory as the project root.
- Edit source files under `src/`. Never hand-edit `public/`, `node_modules/`, `.history/`, `.git/`, or cache folders.
- Prefer the matching file in `src/assets/less/` when changing styles. If a stylesheet has no LESS source, edit its source CSS under `src/assets/css/` and note that exception.
- Read `docs/business-facts.md`, `docs/site-brief.md`, and `docs/brand-guide.md` before changing public content or design.
- Do not treat the current `src/_data/client.js` values as authoritative; several are starter placeholders. Never guess missing client information.

## Local workflow

- Use `npm start` for the local Eleventy and LESS development workflow.
- Use `npm run build` for a production build. Netlify publishes `public/` using the same command.
- Keep routes, asset paths, and filename capitalization compatible with Netlify's case-sensitive environment.
- Keep changes focused. Do not upgrade dependencies, replace the framework, change hosting, or enable external services unless the task explicitly requires it.

## Definition of done

- Run the production build after source changes and report the result.
- Check affected pages at mobile, tablet, and desktop sizes.
- Verify keyboard access, visible focus, headings, image alternatives, form labels, and useful error states.
- Check internal links, canonical URLs, social metadata, sitemap behavior, and case-sensitive asset paths.
- Follow the shared small-business website performance playbook. Replace oversized page media with appropriately encoded and responsive variants.
- Review `docs/launch-checklist.md` for launch or broad site work and report unresolved items.

## Safety

- Do not deploy, change DNS, alter Netlify or GitHub configuration, delete content, or modify credentials without explicit approval.
- Do not expose private client information or put secrets in committed files.
- Preserve unrelated user changes and inspect the Git diff before handing work back.
