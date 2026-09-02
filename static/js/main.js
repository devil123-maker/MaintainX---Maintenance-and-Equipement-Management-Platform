(function () {
  "use strict";

  const THEME_KEY = "maintainx-theme";

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;
    const theme = saved || (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
    updateThemeIcons(theme);
  }

  function toggleTheme() {
    const current =
      document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(THEME_KEY, next);
    updateThemeIcons(next);
    window.dispatchEvent(
      new CustomEvent("themechange", { detail: { theme: next } }),
    );
  }

  function updateThemeIcons(theme) {
    document.querySelectorAll("[data-theme-icon]").forEach((el) => {
      el.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
    });
  }

  function initThemeToggles() {
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      btn.addEventListener("click", toggleTheme);
    });
  }

  function initSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.querySelector(".sidebar-overlay");
    const menuBtn = document.querySelector("[data-sidebar-toggle]");

    if (!sidebar || !menuBtn) return;

    function open() {
      sidebar.classList.add("is-open");
      overlay?.classList.add("is-visible");
      document.body.style.overflow = "hidden";
    }

    function close() {
      sidebar.classList.remove("is-open");
      overlay?.classList.remove("is-visible");
      document.body.style.overflow = "";
    }

    menuBtn.addEventListener("click", () => {
      sidebar.classList.contains("is-open") ? close() : open();
    });

    overlay?.addEventListener("click", close);

    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) close();
    });
  }

  function initLandingNav() {
    const nav = document.querySelector(".landing-nav");
    const toggle = document.querySelector("[data-nav-toggle]");
    if (!nav || !toggle) return;

    toggle.addEventListener("click", () => {
      nav.classList.toggle("is-mobile-open");
    });
  }

  function initDropdowns() {
    document.querySelectorAll(".dropdown").forEach((dropdown) => {
      const trigger = dropdown.querySelector("[data-dropdown-trigger]");
      if (!trigger) return;

      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        const wasOpen = dropdown.classList.contains("is-open");
        document
          .querySelectorAll(".dropdown.is-open")
          .forEach((d) => d.classList.remove("is-open"));
        if (!wasOpen) dropdown.classList.add("is-open");
      });
    });

    document.addEventListener("click", () => {
      document
        .querySelectorAll(".dropdown.is-open")
        .forEach((d) => d.classList.remove("is-open"));
    });
  }

  function initTabs() {
    document.querySelectorAll("[data-tabs]").forEach((container) => {
      const buttons = container.querySelectorAll(".tab-btn");
      const panels = container.querySelectorAll(".tab-panel");

      buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
          const target = btn.getAttribute("data-tab");
          buttons.forEach((b) => b.classList.remove("is-active"));
          panels.forEach((p) => p.classList.remove("is-active"));
          btn.classList.add("is-active");
          const panel = container.querySelector(`[data-panel="${target}"]`);
          panel?.classList.add("is-active");
        });
      });
    });
  }

  function initModals() {
    document.querySelectorAll("[data-modal-open]").forEach((trigger) => {
      const id = trigger.getAttribute("data-modal-open");
      const overlay = document.getElementById(id);
      if (!overlay) return;

      trigger.addEventListener("click", () => overlay.classList.add("is-open"));

      overlay.querySelectorAll("[data-modal-close]").forEach((close) => {
        close.addEventListener("click", () =>
          overlay.classList.remove("is-open"),
        );
      });

      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.classList.remove("is-open");
      });
    });
  }

  function initTicketFilter() {
    const search = document.getElementById("ticket-search");
    const statusFilter = document.getElementById("ticket-status-filter");
    const rows = document.querySelectorAll("[data-ticket-row]");
    const cards = document.querySelectorAll("[data-ticket-card]");

    if (!search && !statusFilter) return;

    function filter() {
      const query = (search?.value || "").toLowerCase();
      const status = statusFilter?.value || "all";

      const match = (el) => {
        const text = el.textContent.toLowerCase();
        const rowStatus = el.getAttribute("data-status") || "";
        const matchesSearch = !query || text.includes(query);
        const matchesStatus = status === "all" || rowStatus === status;
        return matchesSearch && matchesStatus;
      };

      rows.forEach((row) => {
        row.style.display = match(row) ? "" : "none";
      });
      cards.forEach((card) => {
        card.style.display = match(card) ? "" : "none";
      });
    }

    search?.addEventListener("input", filter);
    statusFilter?.addEventListener("change", filter);
  }

  function initFormValidation() {
    const form = document.getElementById("create-ticket-form");
    if (!form) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let valid = true;

      form.querySelectorAll("[required]").forEach((field) => {
        const group =
          field.closest(".form-group") || field.closest(".float-field");
        field.classList.remove("form-input--error");

        if (!field.value.trim()) {
          valid = false;
          field.classList.add("form-input--error");
          let err = group?.querySelector(".form-error");
          if (!err && group) {
            err = document.createElement("p");
            err.className = "form-error";
            err.textContent = "This field is required";
            group.appendChild(err);
          }
        } else {
          group?.querySelector(".form-error")?.remove();
        }
      });

      if (valid) {
        const btn = form.querySelector('[type="submit"]');
        const original = btn.textContent;
        btn.textContent = "Ticket Created!";
        btn.disabled = true;
        setTimeout(() => {
          btn.textContent = original;
          btn.disabled = false;
          form.reset();
        }, 2000);
      }
    });
  }

  function initToggleButtons() {
    const techBtn = document.getElementById("techBtn");
    const customerBtn = document.getElementById("custBtn");
    const userType = document.getElementById("userType");

    if (!techBtn || !customerBtn) return;

    techBtn.addEventListener("click", () => {
      
      userType.value = "technician";
      techBtn.classList.add("active");
      customerBtn.classList.remove("active");
    });

    customerBtn.addEventListener("click", () => {

      userType.value = "customer";
      customerBtn.classList.add("active");
      techBtn.classList.remove("active");
    });
  }

  function initPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = btn.getAttribute("data-password-toggle");
        let input = targetId ? document.getElementById(targetId) : null;
        if (!input) {
          input = btn.closest(".float-field, .form-group")?.querySelector("input");
        }
        if (!input) return;

        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";

        const icon = btn.querySelector("i");
        if (icon) {
          icon.className = isPassword ? "fa-solid fa-eye-slash" : "fa-solid fa-eye";
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initThemeToggles();
    initSidebar();
    initLandingNav();
    initDropdowns();
    initTabs();
    initModals();
    initTicketFilter();
    initFormValidation();
    initToggleButtons();
    initPasswordToggles();
  });
})();
