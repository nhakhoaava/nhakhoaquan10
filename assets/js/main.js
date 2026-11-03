(function () {
  "use strict";

  /* ---------- Mobile nav ---------- */
  var navToggle = document.querySelector(".nav-toggle");
  var mainNav = document.querySelector(".main-nav");
  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = mainNav.classList.toggle("nav-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
    mainNav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        mainNav.classList.remove("nav-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- Nav dropdown: Kiến thức niềng răng ---------- */
  document.querySelectorAll(".nav-item.has-dropdown").forEach(function (item) {
    var toggle = item.querySelector(".nav-dd-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var isOpen = item.classList.toggle("open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      document.querySelectorAll(".nav-item.has-dropdown").forEach(function (other) {
        if (other !== item) {
          other.classList.remove("open");
          var t = other.querySelector(".nav-dd-toggle");
          if (t) t.setAttribute("aria-expanded", "false");
        }
      });
    });
  });
  document.addEventListener("click", function () {
    document.querySelectorAll(".nav-item.has-dropdown.open").forEach(function (item) {
      item.classList.remove("open");
      var t = item.querySelector(".nav-dd-toggle");
      if (t) t.setAttribute("aria-expanded", "false");
    });
  });

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll(".faq-item").forEach(function (item) {
    var q = item.querySelector(".faq-q");
    if (!q) return;
    q.addEventListener("click", function () {
      var wasOpen = item.classList.contains("open");
      item.closest(".faq-list").querySelectorAll(".faq-item").forEach(function (i) {
        i.classList.remove("open");
        var btn = i.querySelector(".faq-q");
        if (btn) btn.setAttribute("aria-expanded", "false");
      });
      if (!wasOpen) {
        item.classList.add("open");
        q.setAttribute("aria-expanded", "true");
      }
    });
  });

  /* ---------- Gallery lightbox ---------- */
  var lightbox = document.querySelector(".lightbox");
  if (lightbox) {
    var lbImg = lightbox.querySelector("img");
    var lbCaption = lightbox.querySelector(".lightbox-caption");
    var lbClose = lightbox.querySelector(".lightbox-close");

    document.querySelectorAll(".gallery-item").forEach(function (item) {
      item.addEventListener("click", function () {
        var img = item.querySelector("img");
        if (!img) return;
        lbImg.src = item.getAttribute("data-full") || img.currentSrc || img.src;
        lbImg.alt = img.alt || "";
        if (lbCaption) lbCaption.textContent = img.alt || "";
        lightbox.classList.add("open");
        document.body.style.overflow = "hidden";
      });
    });

    function closeLightbox() {
      lightbox.classList.remove("open");
      document.body.style.overflow = "";
    }
    if (lbClose) lbClose.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLightbox();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeLightbox();
    });
  }

  /* ---------- Back-to-top in floating sidebar ---------- */
  var fsTop = document.querySelector(".fs-top");
  if (fsTop) {
    window.addEventListener(
      "scroll",
      function () {
        if (window.scrollY > 480) fsTop.classList.add("show");
        else fsTop.classList.remove("show");
      },
      { passive: true }
    );
    fsTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- Gallery: xem thêm ---------- */
  var moreBtn = document.getElementById("gallery-load-more");
  if (moreBtn) {
    var left = document.getElementById("gallery-left");
    moreBtn.addEventListener("click", function () {
      var hidden = document.querySelectorAll(".gallery-item[data-more][hidden]");
      for (var i = 0; i < 24 && i < hidden.length; i++) hidden[i].removeAttribute("hidden");
      var remain = document.querySelectorAll(".gallery-item[data-more][hidden]").length;
      if (left) left.textContent = remain;
      if (!remain) moreBtn.parentNode.style.display = "none";
    });
  }
})();
