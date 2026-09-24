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

  window.closeModal = function (target) {
    if (!target) {
      document.querySelectorAll(".modal-overlay.is-open").forEach((m) => m.classList.remove("is-open"));
      return;
    }
    const overlay = typeof target === "string"
      ? document.getElementById(target)
      : (target.closest ? target.closest(".modal-overlay") : null);
    if (overlay) overlay.classList.remove("is-open");
  };

  function initModals() {
  // Open modal buttons
  document.querySelectorAll("[data-modal-open]").forEach((trigger) => {
    const id = trigger.getAttribute("data-modal-open");
    const overlay = document.getElementById(id);

    if (!overlay) return;

    trigger.addEventListener("click", () => {
      overlay.classList.add("is-open");
    });
  });

  // Close modal buttons
  document.addEventListener("click", (e) => {
    const closeBtn = e.target.closest("[data-modal-close]");

    if (closeBtn) {
      e.preventDefault();
      e.stopPropagation();

      const modal = closeBtn.closest(".modal-overlay");

      if (modal) {
        modal.classList.remove("is-open");
      }

      return;
    }

    // Close when clicking directly on dark overlay
    if (e.target.classList.contains("modal-overlay")) {
      e.preventDefault();
      e.target.classList.remove("is-open");
    }
  });

  // Close modal with Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document
        .querySelectorAll(".modal-overlay.is-open")
        .forEach((modal) => {
          modal.classList.remove("is-open");
        });
    }
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
    if (input && input.value) return input.value;
    let cookieValue = "";
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue;
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

  function initCalendar() {
    const monthYearEl = document.getElementById("calendar-month-year");
    const container = document.getElementById("calendar-days-container");
    if (!container || !monthYearEl) return;

    let currentDate = new Date();
    let eventsData = [];

    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];

    async function loadCalendarEvents() {
      try {
        const response = await fetch("/calendar/?format=json", {
          headers: { "Accept": "application/json" }
        });
        if (response.ok) {
          const data = await response.json();
          eventsData = data.events || [];
          renderCalendar();
        }
      } catch (e) {
        console.error("Failed to load calendar events", e);
      }
    }

    function renderCalendar() {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();

      monthYearEl.innerHTML = `<i class="fa-solid fa-calendar-days" style="color:var(--color-primary);"></i> ${monthNames[month]} ${year}`;

      const firstDay = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const daysInPrevMonth = new Date(year, month, 0).getDate();

      const todayStr = new Date().toISOString().split("T")[0];

      let html = "";

      // Previous month trailing days
      for (let i = firstDay - 1; i >= 0; i--) {
        const pDay = daysInPrevMonth - i;
        html += `<div class="calendar-day calendar-day--other-month">
          <span class="calendar-day__number">${pDay}</span>
        </div>`;
      }

      // Current month days
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
        const isToday = dateStr === todayStr;

        const dayEvents = eventsData.filter((ev) => ev.scheduled_date === dateStr);

        html += `<div class="calendar-day ${isToday ? "calendar-day--today" : ""}" data-calendar-date="${dateStr}">
          <span class="calendar-day__number">${d}</span>
          <div class="calendar-events">`;

        dayEvents.forEach((ev) => {
          const overdueClass = ev.is_overdue ? "calendar-event--overdue" : "";
          const badgeIcon = ev.is_overdue ? '<i class="fa-solid fa-triangle-exclamation" style="color:#ef4444;"></i> ' : "";
          html += `<div class="calendar-event ${overdueClass}" data-event-id="${ev.id}">
            <span class="calendar-event__title">${badgeIcon}${ev.title}</span>
          </div>`;
        });

        html += `</div></div>`;
      }

      // Next month padding days
      const totalCells = firstDay + daysInMonth;
      const nextDays = (7 - (totalCells % 7)) % 7;
      for (let n = 1; n <= nextDays; n++) {
        html += `<div class="calendar-day calendar-day--other-month">
          <span class="calendar-day__number">${n}</span>
        </div>`;
      }

      container.innerHTML = html;
    }

    // Controls
    document.getElementById("cal-prev-btn")?.addEventListener("click", () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      renderCalendar();
    });

    document.getElementById("cal-next-btn")?.addEventListener("click", () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      renderCalendar();
    });

    document.getElementById("cal-today-btn")?.addEventListener("click", () => {
      currentDate = new Date();
      renderCalendar();
    });

    // Date Click -> Open Schedule Modal
    container.addEventListener("click", (e) => {
      const eventPill = e.target.closest(".calendar-event");
      if (eventPill) {
        e.stopPropagation();
        const evId = parseInt(eventPill.getAttribute("data-event-id"));
        const ev = eventsData.find((item) => item.id === evId);
        if (ev) openEventDetailModal(ev);
        return;
      }

      const dayCell = e.target.closest("[data-calendar-date]");
      if (dayCell) {
        const selectedDate = dayCell.getAttribute("data-calendar-date");
        openScheduleModal(selectedDate);
      }
    });

    document.getElementById("open-schedule-modal-btn")?.addEventListener("click", () => {
      const todayStr = new Date().toISOString().split("T")[0];
      openScheduleModal(todayStr);
    });

    function openScheduleModal(dateStr) {
      const modal = document.getElementById("schedule-modal");
      const dateInput = document.getElementById("cal_scheduled_date");
      if (dateInput) dateInput.value = dateStr;
      if (modal) modal.classList.add("is-open");
    }

    function openEventDetailModal(ev) {
      const modal = document.getElementById("event-detail-modal");
      const titleEl = document.getElementById("event-modal-title");
      const bodyEl = document.getElementById("event-modal-body-content");
      const idInput = document.getElementById("reschedule-event-id");
      const dateInput = document.getElementById("reschedule-new-date");
      const link = document.getElementById("event-view-detail-link");

      if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-screwdriver-wrench"></i> ${ev.title}`;
      if (idInput) idInput.value = ev.id;
      if (dateInput) dateInput.value = ev.scheduled_date || "";

      let statusBadge = `<span class="badge badge--open">${ev.status}</span>`;
      if (ev.status === "in_progress") statusBadge = `<span class="badge badge--progress">In Progress</span>`;
      if (ev.status === "repaired" || ev.status === "completed") statusBadge = `<span class="badge badge--resolved">Repaired</span>`;
      if (ev.status === "scrap") statusBadge = `<span class="badge badge--urgent">Scrap</span>`;

      let overdueHtml = ev.is_overdue ? `<span class="badge badge--overdue"><i class="fa-solid fa-triangle-exclamation"></i> Overdue</span>` : "";

      if (bodyEl) {
        bodyEl.innerHTML = `
          <div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.75rem;">
            <span class="badge badge--ghost">Preventive</span>
            <span class="badge badge--${ev.priority}">${ev.priority.toUpperCase()}</span>
            ${statusBadge}
            ${overdueHtml}
          </div>
          <p style="margin-bottom:0.5rem;"><strong>Equipment:</strong> ${ev.equipment_name} (${ev.equipment_serial})</p>
          <p style="margin-bottom:0.5rem;"><strong>Assigned:</strong> ${ev.technician_name || ev.team_name || "Unassigned"}</p>
          <p style="margin-bottom:0.5rem;"><strong>Scheduled Date:</strong> ${ev.scheduled_date || "N/A"}</p>
          ${ev.duration_display ? `<p style="margin-bottom:0.5rem;"><strong>Duration:</strong> ${ev.duration_display}</p>` : ""}
          <p style="margin-bottom:0.5rem;"><strong>Description:</strong> ${ev.description || "N/A"}</p>
        `;
      }

      if (modal) modal.classList.add("is-open");
    }

    // Schedule Preventive Form Submit
    const scheduleForm = document.getElementById("schedule-preventive-form");
    if (scheduleForm) {
      scheduleForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(scheduleForm);
        const data = Object.fromEntries(formData.entries());

        try {
          const response = await fetch("/requests/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify({
              title: data.title,
              description: data.description,
              equipment: data.equipment,
              priority: data.priority,
              request_type: "preventive",
              scheduled_date: data.scheduled_date,
              duration_value: data.duration_value || null,
              duration_unit: data.duration_unit || "minutes",
              assigned_team: data.assigned_team || null,
              assigned_technician: data.assigned_technician || null
            })
          });

          const result = await response.json();
          if (!response.ok) {
            let msg = "Failed to schedule preventive maintenance.";
            if (typeof result.error === "string") msg = result.error;
            else if (typeof result.error === "object") msg = Object.values(result.error).flat().join(" ");
            throw new Error(msg);
          }

          document.getElementById("schedule-modal")?.classList.remove("is-open");
          scheduleForm.reset();
          await loadCalendarEvents();
        } catch (err) {
          showToast(err.message);
        }
      });
    }

    // Reschedule Form Submit
    const rescheduleForm = document.getElementById("reschedule-event-form");
    if (rescheduleForm) {
      rescheduleForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const evId = document.getElementById("reschedule-event-id")?.value;
        const newDate = document.getElementById("reschedule-new-date")?.value;

        if (!evId || !newDate) return;

        try {
          const response = await fetch(`/requests/${evId}/`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify({ scheduled_date: newDate })
          });

          const result = await response.json();
          if (!response.ok) {
            let msg = "Failed to reschedule maintenance.";
            if (typeof result.error === "string") msg = result.error;
            else if (typeof result.error === "object") msg = Object.values(result.error).flat().join(" ");
            throw new Error(msg);
          }

          document.getElementById("event-detail-modal")?.classList.remove("is-open");
          await loadCalendarEvents();
        } catch (err) {
          showToast(err.message);
        }
      });
    }

    loadCalendarEvents();
  }

  function initJoinRequestActions() {
    document.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-join-request-btn]");
      if (!btn) return;

      e.preventDefault();
      const ticketId = btn.getAttribute("data-ticket-id");
      if (!ticketId) return;

      const originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Joining...`;

      try {
        const response = await fetch(`/requests/${ticketId}/join/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          credentials: "same-origin"
        });

        const data = await response.json();
        if (!response.ok || data.success === false) {
          let msg = "Failed to join request.";
          if (typeof data.error === "string") msg = data.error;
          else if (typeof data.error === "object") msg = Object.values(data.error).flat().join(" ");
          throw new Error(msg);
        }

        showToast(data.message || "Request accepted. You are now assigned to this maintenance request.");

        const techName = data.assigned_technician_name || (data.request && data.request.assigned_technician_name) || "Assigned Technician";

        // Check if currently on ticket detail page
        if (document.querySelector("[data-ticket-detail-view]")) {
          window.location.reload();
          return;
        }

        // 1. Update Kanban card if present
        const card = document.querySelector(`.kanban-card[data-ticket-id="${ticketId}"]`);
        if (card) {
          card.setAttribute("data-status", "in_progress");
          const techLabel = card.querySelector("[data-card-tech-label]");
          if (techLabel) {
            techLabel.textContent = techName;
          }

          const actionsContainer = card.querySelector("[data-card-actions]");
          if (actionsContainer) {
            actionsContainer.innerHTML = `
              <div style="display:flex;gap:0.4rem;flex-direction:column;width:100%;">
                <a href="/requests/${ticketId}/" class="btn btn--sm btn--secondary" data-open-ticket-btn style="width:100%;text-align:center;">
                  <i class="fa-solid fa-arrow-up-right-from-square"></i> Open / Continue Work
                </a>
                <button type="button" class="btn btn--sm btn--success" data-complete-request-btn data-ticket-id="${ticketId}" style="width:100%;">
                  <i class="fa-solid fa-check"></i> Mark as Repaired
                </button>
              </div>
            `;
          }

          const select = card.querySelector("[data-card-status-select]");
          if (select) select.value = "in_progress";

          const targetZone = document.querySelector(`[data-status-drop="in_progress"]`);
          if (targetZone) {
            targetZone.appendChild(card);
            updateColumnCounts();
          }
        }

        // 2. Update table row if present
        const row = document.querySelector(`tr[data-ticket-id="${ticketId}"]`);
        if (row) {
          row.setAttribute("data-status", "in_progress");
          const rowTech = row.querySelector("[data-row-tech]");
          if (rowTech) {
            rowTech.textContent = techName;
          }
          const rowStatus = row.querySelector("[data-row-status]");
          if (rowStatus) {
            rowStatus.innerHTML = `<span class="badge badge--progress">In Progress</span>`;
          }
          const rowJoinBtn = row.querySelector("[data-join-request-btn]");
          if (rowJoinBtn) {
            rowJoinBtn.outerHTML = `
              <a href="/requests/${ticketId}/" class="btn btn--sm btn--secondary" data-open-ticket-btn style="margin-left:0.5rem;padding:0.2rem 0.5rem;font-size:0.75rem;">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Open
              </a>
              <button type="button" class="btn btn--sm btn--success" data-complete-request-btn data-ticket-id="${ticketId}" style="margin-left:0.3rem;padding:0.2rem 0.5rem;font-size:0.75rem;">
                <i class="fa-solid fa-check"></i> Repaired
              </button>
            `;
          }
        }

        // 3. Fallback if button still in DOM and not yet replaced
        if (document.body.contains(btn) && btn.hasAttribute("data-join-request-btn")) {
          btn.outerHTML = `
            <a href="/requests/${ticketId}/" class="btn btn--sm btn--secondary" data-open-ticket-btn style="margin-left:0.5rem;padding:0.2rem 0.5rem;font-size:0.75rem;">
              <i class="fa-solid fa-arrow-up-right-from-square"></i> Open / Continue Work
            </a>
            <button type="button" class="btn btn--sm btn--success" data-complete-request-btn data-ticket-id="${ticketId}" style="margin-left:0.5rem;padding:0.2rem 0.5rem;font-size:0.75rem;">
              <i class="fa-solid fa-check"></i> Mark as Repaired
            </button>
          `;
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        showToast(err.message || "Failed to join request");
        if (err.message && err.message.toLowerCase().includes("already been assigned")) {
          btn.remove();
        }
      }
    });
  }

  function initCompleteRequestActions() {
    document.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-complete-request-btn]");
      if (!btn) return;

      e.preventDefault();
      const ticketId = btn.getAttribute("data-ticket-id");
      if (!ticketId) return;

      const originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Completing...`;

      try {
        const response = await fetch(`/requests/${ticketId}/complete/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          credentials: "same-origin",
          body: JSON.stringify({ status: "repaired", notes: "Marked as repaired by technician" }),
        });

        const data = await response.json();
        if (!response.ok || data.success === false) {
          let msg = "Failed to mark as repaired.";
          if (typeof data.error === "string") msg = data.error;
          else if (typeof data.error === "object") msg = Object.values(data.error).flat().join(" ");
          throw new Error(msg);
        }

        showToast(data.message || "Ticket marked as repaired.");

        if (document.querySelector("[data-ticket-detail-view]")) {
          window.location.reload();
          return;
        }

        // 1. Update Kanban card
        const card = document.querySelector(`.kanban-card[data-ticket-id="${ticketId}"]`);
        if (card) {
          card.setAttribute("data-status", "repaired");
          const actionsContainer = card.querySelector("[data-card-actions]");
          if (actionsContainer) actionsContainer.innerHTML = "";

          const select = card.querySelector("[data-card-status-select]");
          if (select) select.value = "repaired";

          const targetZone = document.querySelector(`[data-status-drop="repaired"]`);
          if (targetZone) {
            targetZone.appendChild(card);
            updateColumnCounts();
          }
        }

        // 2. Update table row
        const row = document.querySelector(`tr[data-ticket-id="${ticketId}"]`);
        if (row) {
          row.setAttribute("data-status", "repaired");
          const rowStatus = row.querySelector("[data-row-status]");
          if (rowStatus) {
            rowStatus.innerHTML = `<span class="badge badge--resolved">Repaired</span>`;
          }
          const rowCompleteBtn = row.querySelector("[data-complete-request-btn]");
          if (rowCompleteBtn) rowCompleteBtn.remove();
        }

        if (document.body.contains(btn)) {
          btn.remove();
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        showToast(err.message || "Failed to complete request");
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
    initCalendar();
    initJoinRequestActions();
    initCompleteRequestActions();
  });
})();
