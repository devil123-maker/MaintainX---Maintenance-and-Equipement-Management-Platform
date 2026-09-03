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

  function showToast(message) {
    let existing = document.querySelector(".toast-notification");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "toast-notification";
    toast.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease-out, transform 0.4s ease-out";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(100%)";
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  }

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const cookie = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  }

  function updateColumnCounts() {
    const columns = ["new", "in_progress", "repaired", "scrap"];
    columns.forEach((status) => {
      const dropZone = document.querySelector(`[data-status-drop="${status}"]`);
      const countEl = document.querySelector(`[data-col-count="${status}"]`);
      if (!dropZone) return;

      const cards = dropZone.querySelectorAll(".kanban-card");
      if (countEl) countEl.textContent = cards.length;

      let emptyState = dropZone.querySelector(".kanban-empty");
      if (cards.length === 0) {
        if (!emptyState) {
          emptyState = document.createElement("div");
          emptyState.className = "kanban-empty";
          emptyState.textContent = "No requests";
          dropZone.appendChild(emptyState);
        }
      } else {
        if (emptyState) emptyState.remove();
      }
    });
  }

  function initViewSwitcher() {
    const switcher = id("view-switcher") || document.getElementById("view-switcher");
    const tableView = document.getElementById("table-view");
    const kanbanView = document.getElementById("kanban-view");
    if (!switcher || !tableView || !kanbanView) return;

    function id(s) { return document.getElementById(s); }

    const buttons = switcher.querySelectorAll("[data-view-target]");
    const savedView = localStorage.getItem("maintainx-view-mode") || "table";

    function setView(target) {
      buttons.forEach((btn) => {
        const isTarget = btn.getAttribute("data-view-target") === target;
        btn.classList.toggle("is-active", isTarget);
      });
      if (target === "kanban") {
        tableView.style.display = "none";
        kanbanView.style.display = "grid";
        updateColumnCounts();
      } else {
        kanbanView.style.display = "none";
        tableView.style.display = "block";
      }
      localStorage.setItem("maintainx-view-mode", target);
    }

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-view-target");
        setView(target);
      });
    });

    if (savedView === "kanban") {
      setView("kanban");
    } else {
      updateColumnCounts();
    }
  }

  async function updateTicketStatus(ticketId, newStatus) {
    const response = await fetch(`/requests/${ticketId}/`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ status: newStatus }),
    });

    const data = await response.json();
    if (!response.ok) {
      let msg = "Unable to update status.";
      if (typeof data.error === "string") {
        msg = data.error;
      } else if (typeof data.error === "object") {
        msg = Object.values(data.error).flat().join(" ");
      }
      throw new Error(msg);
    }
    return data;
  }

  function initKanbanDragAndDrop() {
    let draggedCard = null;
    let sourceStatus = null;

    document.addEventListener("dragstart", (e) => {
      const card = e.target.closest(".kanban-card");
      if (!card) return;

      draggedCard = card;
      sourceStatus = card.getAttribute("data-status");
      card.classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", card.getAttribute("data-ticket-id"));
    });

    document.addEventListener("dragend", (e) => {
      const card = e.target.closest(".kanban-card");
      if (card) card.classList.remove("is-dragging");
      document.querySelectorAll(".kanban-column__body").forEach((col) => col.classList.remove("is-dragover"));
      draggedCard = null;
      sourceStatus = null;
    });

    document.querySelectorAll("[data-status-drop]").forEach((dropZone) => {
      dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        dropZone.classList.add("is-dragover");
      });

      dropZone.addEventListener("dragleave", (e) => {
        if (!dropZone.contains(e.relatedTarget)) {
          dropZone.classList.remove("is-dragover");
        }
      });

      dropZone.addEventListener("drop", async (e) => {
        e.preventDefault();
        dropZone.classList.remove("is-dragover");
        if (!draggedCard) return;

        const targetStatus = dropZone.getAttribute("data-status-drop");
        const ticketId = draggedCard.getAttribute("data-ticket-id");

        if (targetStatus === sourceStatus) return;

        const originalParent = draggedCard.parentElement;
        const originalNextSibling = draggedCard.nextSibling;

        // Optimistically move card
        dropZone.appendChild(draggedCard);
        updateColumnCounts();

        try {
          await updateTicketStatus(ticketId, targetStatus);
          draggedCard.setAttribute("data-status", targetStatus);

          // Update quick select in card
          const select = draggedCard.querySelector("[data-card-status-select]");
          if (select) select.value = targetStatus;

          // Update table row if present
          const row = document.querySelector(`tr[data-ticket-id="${ticketId}"]`);
          if (row) row.setAttribute("data-status", targetStatus);

        } catch (err) {
          // Revert move on failure
          if (originalNextSibling) {
            originalParent.insertBefore(draggedCard, originalNextSibling);
          } else {
            originalParent.appendChild(draggedCard);
          }
          updateColumnCounts();
          showToast(err.message || "Failed to update ticket status");
        }
      });
    });
  }

  function initQuickStatusSelect() {
    document.addEventListener("change", async (e) => {
      const select = e.target.closest("[data-card-status-select]");
      if (!select) return;

      const ticketId = select.getAttribute("data-ticket-id");
      const newStatus = select.value;
      const card = select.closest(".kanban-card");
      const oldStatus = card ? card.getAttribute("data-status") : select.defaultValue;

      if (newStatus === oldStatus) return;

      try {
        await updateTicketStatus(ticketId, newStatus);
        if (card) {
          card.setAttribute("data-status", newStatus);
          const targetZone = document.querySelector(`[data-status-drop="${newStatus}"]`);
          if (targetZone) {
            targetZone.appendChild(card);
            updateColumnCounts();
          }
        }
      } catch (err) {
        select.value = oldStatus;
        showToast(err.message || "Failed to update ticket status");
      }
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
    initViewSwitcher();
    initKanbanDragAndDrop();
    initQuickStatusSelect();
  });
})();
