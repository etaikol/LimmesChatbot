# CLAUDE.md

Guidance for Claude Code when working in this repository. Describes what's **non-obvious** from reading the code — architecture seams, deploy workflow, gotchas. Project *state* (what's shipped / what's next) lives in [`PROGRESS.md`](PROGRESS.md) — read that when resuming work.

## What this is

Custom WordPress theme **Limes** for a Hebrew/RTL WooCommerce store (design business — curtains, seating, home textiles). Built on Automattic Underscores (`_s`), heavily customized for a single-store use case. Not a parent theme. Active upgrade scoped in `../שדרוג אתר לימס.pdf`; work happens on the `dev` branch.

## Commands

From the theme root (requires Composer):

```bash
composer install              # first-time setup
composer run lint:php         # parallel PHP syntax check
composer run lint:wpcs        # WordPress Coding Standards via PHPCS
composer run make-pot         # regenerate languages/_s.pot
```

No unit tests. No JS build pipeline — plain jQuery files in `js/` loaded via `wp_enqueue_script`.

## Deploy + dev loop

No build step. Edits upload directly via VSCode's SFTP extension.

- **Dev site:** http://limmes-co-il-newdev.s201.upress.link/wp-admin
- **SFTP config:** `.vscode/sftp.json` (maps theme root → `/wp-content/themes/limes-wordpress-master/` on server — the `-master` suffix is from an old GitHub zip extraction; don't rename without updating the server).
- **Workflow:** edit locally → right-click file → `SFTP: Upload Active File` → hard-reload dev (Ctrl+F5).
- **`uploadOnSave` is intentionally off** — uploads are manual.

**WP Rocket cache gotcha:** WP Rocket is active on dev and serves stale CSS/JS. After uploading theme assets, **clear WP Rocket cache** (admin toolbar → WP Rocket → Clear cache) or deactivate the plugin. Hard-reload alone is not enough. This is the #1 cause of "my CSS change isn't showing up".

## Viewport zoom hack — read before touching layout

`header.php` contains an inline script (lines ~16–167) that applies `document.body.style.zoom` based on viewport width vs. a 1920px base. **Every pixel dimension in CSS is effectively multiplied by this zoom factor** on desktops smaller than 1920px.

- "Shrink to 50px" ≠ 50 real pixels on a 1440 screen — it's ~37px after zoom.
- Media queries still fire on actual viewport, creating layering confusion.
- Below 975px the zoom resets to 1.

When "my CSS looks wrong on laptop but right in the mock" — suspect this first.

## Architecture

### File loading order (`functions.php`)

Orchestrates everything; order matters:

1. **Core** (`inc/core/*`) — theme support, enqueues, image sizes, menus, CPTs, taxonomies, utilities, admin.
2. **Templates** (`inc/templates/*`) — product/post/blog template helpers.
3. **Features** (`inc/features/*`) — e.g. Yoast breadcrumb customizations.
4. **WooCommerce** (only if `class_exists('WooCommerce')`):
   - `inc/woo-product-control.php` first (gates downstream behavior).
   - Modern modular: `inc/woocommerce/woocommerce-integration.php`.
   - Legacy: `inc/woocommerce.php`, `inc/woo-product-page.php`, `inc/woo-cart-calculations.php`, `inc/woo-simple-product-*.php`, `inc/woo-final-price-display.php`, `inc/woo-ensure-form-handler.php` — still active, pending phase-out.
5. `functions-loaders.php` / `functions-templates.php` / `functions-woocommerce.php` at theme root are **empty stubs** kept so old `require_once` calls don't fatal. Don't add code to them.

### Legacy vs. modular tension

The theme is mid-refactor with two overlapping systems for product customization, cart totals, and price display. When touching any of those:

- **Check both** `inc/woocommerce/*` (modular) and `inc/woo-*.php` (legacy) — behavior may be set by either.
- Files named `woo-simple-product-*` are scar tissue from past fights with WC Product Add-Ons. `debug` / `form-fix` / `fix-final` in names = iterative patches that sometimes disable each other. Read top-to-bottom before changing.
- Safer to add new behavior via the modular system and remove the legacy counterpart than to edit legacy files in place.

### WooCommerce template overrides (`woocommerce/`)

Standard WC override folder — files here replace plugin defaults. Deepest customizations:

- `woocommerce/cart/*` — cart page (cart.php, cart-totals.php, mini-cart.php, shipping-calculator.php).
- `woocommerce/checkout/*` — form-checkout, form-billing, form-shipping, review-order.
- `woocommerce/single-product/*` — product page including a custom `product-form/` subfolder.
- `woocommerce/content-product.php` — product card in shop/category grids.

Template overrides go here; hook/filter logic goes in `inc/woocommerce/` or legacy `inc/woo-*.php`.

### Styles

- `style.css` — theme header only (required by WP); actual CSS is in `css/style.css`.
- `css/style.css` — long single file organized by section comments (`/* ---- Section X ---- */`). Grep section names rather than scrolling.
- `style-rtl.css` — RTL overrides (site is Hebrew, `<html dir="rtl">` hard-coded in `header.php`).
- `woocommerce.css` — WC-specific, enqueued separately.

### Page chrome

- `header.php` — logo, top nav, mobile menu, cart icon + the body-zoom script + GTM/Meta Pixel tags.
- `template-parts/top-inner.php` — brown banner with page title + Yoast breadcrumbs on every inner page. Styled in [css/style.css:1461](css/style.css:1461).
- `footer.php`, `sidebar.php` — self-explanatory.

## Conventions

- **RTL first.** Site is Hebrew. Verify layout in RTL before declaring done — don't assume left/right.
- **Theme-slug inconsistency is intentional.** `Limes` (theme name) / `_s` (starter leftovers) / `limes-wordpress-master` (server folder, from an old GitHub zip) / `extra` (text domain, template leftover). Don't "fix" without a coordinated deploy — references exist across code + WP options table.
- **ACF options are heavy.** Header contact info, social icons, many content fields come from `get_field('header', 'options')` etc. Check the "Limes Options" ACF group in wp-admin when a field is missing at render.
- **`wp_is_mobile()` gates markup in header.php** — server-side UA check, not a CSS breakpoint. Mobile vs. desktop changes usually need edits in two places (the PHP branch + `desktop_only` / `mobile_only` CSS classes).
- **Never commit `.vscode/sftp.json`** — contains the FTP password. In the SFTP extension's ignore, but not in `.gitignore`. Unstage if you see it.

## Branches

- `main`, `dev`, `upload-project` on origin.
- **Active work is on `dev`.** `upload-project` is stale — ignore unless explicitly asked.
- Production deploy path not yet established — treat merges to `main` as "about to push to live site" and confirm before doing so.
