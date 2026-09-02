/* ============================================================
   ICEN Medical Equipment Limited — Main Scripts
   ============================================================ */
(function () {
  "use strict";

  /* ---------- Sticky header shadow ---------- */
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (header) {
      header.classList.toggle("scrolled", window.scrollY > 8);
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav-links");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.innerHTML = open
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.innerHTML =
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
      }
    });
  }

  /* ---------- Active nav link ---------- */
  var path = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-links a").forEach(function (a) {
    var href = a.getAttribute("href");
    if (!href || href.indexOf("#") === 0) return;
    if (href === path || (path === "" && href === "index.html")) {
      a.classList.add("active");
    }
  });

  /* ---------- Reveal on scroll ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) {
      io.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("visible");
    });
  }

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll(".faq-item").forEach(function (item) {
    var q = item.querySelector(".faq-q");
    if (!q) return;
    q.addEventListener("click", function () {
      var isOpen = item.classList.contains("open");
      document.querySelectorAll(".faq-item.open").forEach(function (o) {
        o.classList.remove("open");
      });
      if (!isOpen) item.classList.add("open");
    });
  });

  /* ---------- Contact form (front-end demo handler) ---------- */
  var form = document.getElementById("inquiry-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var required = form.querySelectorAll("[required]");
      var valid = true;
      required.forEach(function (field) {
        if (!field.value.trim()) {
          valid = false;
          field.style.borderColor = "#d64545";
        } else {
          field.style.borderColor = "";
        }
      });
      var email = document.getElementById("cf-email");
      if (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        valid = false;
        email.style.borderColor = "#d64545";
      }
      if (!valid) return;

      var success = document.getElementById("form-success");
      if (success) {
        success.style.display = "block";
        success.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      form.reset();
      setTimeout(function () {
        if (success) success.style.display = "none";
      }, 9000);
    });
  }

  /* ---------- Preselect product interest from query string ---------- */
  var params = new URLSearchParams(window.location.search);
  var product = params.get("product");
  var interest = document.getElementById("cf-product");
  if (product && interest) {
    interest.value = product;
  }

  /* ---------- Footer year ---------- */
  var year = document.getElementById("year");
  if (year) {
    year.textContent = new Date().getFullYear();
  }
})();
