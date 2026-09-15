/* ============================================================
   ICEN Medical Equipment Limited - Conversion tracking
   Reports the two actions that actually matter to GA4:
     1. whatsapp_click  - any click on a wa.me link
     2. generate_lead   - arrival on /thank-you.html (form submitted)
   Loaded on every page. Requires the GA snippet in <head>.
   ============================================================ */
(function () {
  "use strict";

  function send(name, params) {
    if (typeof window.gtag === "function") {
      window.gtag("event", name, params);
    }
  }

  function placementOf(a) {
    if (a.classList && a.classList.contains("whatsapp-float")) return "floating_button";
    if (a.closest && a.closest("footer")) return "footer";
    if (a.closest && a.closest(".seo-links")) return "related_links";
    if (a.classList && a.classList.contains("btn")) return "inline_button";
    return "inline_link";
  }

  function modelOnPage() {
    var h1 = document.querySelector("main h1") || document.querySelector("h1");
    var t = h1 ? (h1.textContent || "").trim() : "";
    return t.replace(/\s+/g, " ").slice(0, 80);
  }

  /* ---- 1. WhatsApp clicks ------------------------------------------------
     Event delegation, so it also covers links added later. Capture phase so the
     hit is registered before the browser leaves the page. */
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href*="wa.me/"]') : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var num = (href.match(/wa\.me\/([0-9]+)/) || [])[1] || "";
    send("whatsapp_click", {
      link_domain: "wa.me",
      whatsapp_number: num,
      page_path: location.pathname,
      page_title: document.title,
      product: modelOnPage(),
      link_placement: placementOf(a),
      link_text: (a.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60)
    });
  }, true);

  /* ---- 2. Inquiry form submitted ----------------------------------------
     The form redirects to /thank-you.html?name=..&company=..&country=..&product=..
     so the query string doubles as proof that a submit just happened - a direct
     visit to the page fires nothing. */
  if (/\/thank-you\.html$/.test(location.pathname)) {
    var p = new URLSearchParams(location.search);
    var keys = ["name", "company", "country", "product"];
    var came = keys.some(function (k) { return p.get(k); });
    if (came) {
      send("generate_lead", {
        method: "inquiry_form",
        product: p.get("product") || "",
        country: p.get("country") || "",
        company: p.get("company") || ""
      });
    }
  }
})();
