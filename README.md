# ICEN Medical Equipment Limited — B2B Export Website

A fully static, English-language marketing website for **ICEN Medical Equipment Limited**, a medical device manufacturer and exporter. Built as a responsive multi-page site with no build step — open `index.html` in any browser or host it on any static server.

## Pages

| Page | Description |
| --- | --- |
| `index.html` | Home: hero, trust bar, product categories, featured products, why-us, statistics, CTA |
| `products.html` | Full catalog: 8 models across 6 categories with specifications |
| `about.html` | Company profile, mission, quality & compliance, OEM/ODM, milestones |
| `contact.html` | Inquiry form, contact details, FAQ |

## Structure

```
icen-b2b-site/
├── index.html          # Home page
├── products.html       # Product catalog
├── about.html          # About page
├── contact.html        # Contact / inquiry page
├── robots.txt
├── css/
│   └── style.css       # Shared design system (responsive)
├── js/
│   └── main.js         # Nav, reveal, FAQ, form handling
└── assets/
    ├── icen-logo.png   # ICEN brand logo (transparent PNG)
    └── img/            # Hero + product images
```

## Customization Notes

Before production use, replace the **sample content** with verified company data:

- Contact details in the footer and contact page (email, phone, address) are placeholders.
- Company statistics and milestone years on the home/about pages are sample figures.
- Certification claims (ISO 13485, CE, RoHS) and product specifications should be reviewed against the real product documentation and quality files.
- Product model numbers (ICEN-BP200, etc.) are sample SKUs.
- The contact form is a front-end demo — connect it to your CRM, email service or backend endpoint (`js/main.js` → `#inquiry-form` handler).

## Deployment

This repository is deployed with GitHub Pages from the `main` branch, root directory.

```
https://<owner>.github.io/<repository>/
```
