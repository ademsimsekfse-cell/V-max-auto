/**
 * V-max Auto – UI interactions & page transitions
 */

(function () {
  "use strict";

  /* ── Page-enter animation ───────────────────────────────── */
  const wrapper = document.querySelector(".page-wrapper");
  if (wrapper) {
    // Trigger the enter animation on next paint
    requestAnimationFrame(() => {
      requestAnimationFrame(() => wrapper.classList.add("page-visible"));
    });
  }

  /* ── Page-leave animation on navigation ─────────────────── */
  function leave(href) {
    if (!wrapper) { window.location.href = href; return; }
    wrapper.classList.remove("page-visible");
    wrapper.classList.add("page-leaving");
    setTimeout(() => { window.location.href = href; }, 230);
  }

  // Intercept all same-origin <a> clicks (not target=_blank, not #anchors)
  document.addEventListener("click", function (e) {
    const link = e.target.closest("a[href]");
    if (!link) return;
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return;
    if (link.target === "_blank") return;
    // Only intercept same-origin navigations
    try {
      const url = new URL(href, window.location.origin);
      if (url.origin !== window.location.origin) return;
    } catch (_) { return; }

    e.preventDefault();
    leave(href);
  });

  // Intercept form submits with action="" (same-origin HTML forms only)
  document.addEventListener("submit", function (e) {
    const form = e.target;
    if (form.method && form.method.toLowerCase() !== "get") return; // only GET forms need this
    const action = form.action || window.location.href;
    try {
      const url = new URL(action, window.location.origin);
      if (url.origin !== window.location.origin) return;
    } catch (_) { return; }
    // Let POST forms submit normally (they navigate after); just trigger leave animation
    if (!wrapper) return;
    wrapper.classList.remove("page-visible");
    wrapper.classList.add("page-leaving");
    // Don't prevent default – let the form submit and the browser navigate
  });

  /* ── Mobile hamburger menu ───────────────────────────────── */
  const toggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (toggle && navLinks) {
    toggle.addEventListener("click", () => {
      const open = navLinks.classList.toggle("open");
      toggle.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
      if (!toggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove("open");
        toggle.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });

    // Close on nav link click (mobile)
    navLinks.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        navLinks.classList.remove("open");
        toggle.classList.remove("open");
      });
    });
  }

  /* ── Active nav link highlight ───────────────────────────── */
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-links a").forEach((a) => {
    const linkPath = new URL(a.href, window.location.origin).pathname;
    if (
      linkPath === currentPath ||
      (linkPath !== "/" && currentPath.startsWith(linkPath))
    ) {
      a.classList.add("active");
    }
  });

  /* ── Ripple effect on module cards ───────────────────────── */
  document.querySelectorAll(".module-card, .btn").forEach((el) => {
    el.addEventListener("pointerdown", function (e) {
      const rect = el.getBoundingClientRect();
      const ripple = document.createElement("span");
      const size = Math.max(rect.width, rect.height) * 1.6;
      ripple.style.cssText = `
        position:absolute;
        border-radius:50%;
        background:rgba(255,255,255,0.14);
        width:${size}px;height:${size}px;
        left:${e.clientX - rect.left - size / 2}px;
        top:${e.clientY - rect.top - size / 2}px;
        transform:scale(0);
        animation:ripple 0.5s linear;
        pointer-events:none;
      `;
      if (getComputedStyle(el).position === "static") el.style.position = "relative";
      el.style.overflow = "hidden";
      el.appendChild(ripple);
      ripple.addEventListener("animationend", () => ripple.remove());
    });
  });

  /* Inject ripple keyframe once */
  if (!document.getElementById("vmax-ripple-style")) {
    const s = document.createElement("style");
    s.id = "vmax-ripple-style";
    s.textContent = "@keyframes ripple{to{transform:scale(1);opacity:0}}";
    document.head.appendChild(s);
  }
})();
