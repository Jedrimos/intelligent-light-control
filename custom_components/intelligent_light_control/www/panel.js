// Intelligent Light Control – Custom Lovelace Panel

const ILC_DOMAIN = "intelligent_light_control";

const ILC_VERSION = "1.1.0";

const STATE_LABELS = {
  auto_on:    "Auto – an",
  auto_off:   "Auto – aus",
  manual_on:  "Manuell – an",
  manual_off: "Manuell – aus",
  blocked:    "Blockiert",
  disabled:   "Deaktiviert",
};

const STATE_COLORS = {
  auto_on:    "#4caf50",
  auto_off:   "#9e9e9e",
  manual_on:  "#2196f3",
  manual_off: "#607d8b",
  blocked:    "#ff9800",
  disabled:   "#bdbdbd",
};

const SYS_LABELS  = { auto: "Auto", manual: "Manuell", off: "Aus" };
const MODE_LABELS = { auto: "Auto", manual: "Manuell", off: "Aus" };

const ICON_BULB   = `<svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7zm0 2a5 5 0 0 0-5 5c0 1.87 1.04 3.5 2.7 4.39L11 14.12V16h2v-1.88l1.3-.73C15.96 12.5 17 10.87 17 9a5 5 0 0 0-5-5zm-1 15h2v1h-2z"/></svg>`;
const ICON_MOTION = `<svg viewBox="0 0 24 24"><path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2M9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6z"/></svg>`;
const ICON_PERSON = `<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4m0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`;
const ICON_EDIT   = `<svg viewBox="0 0 24 24"><path d="M20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.84 1.83 3.75 3.75M3 17.25V21h3.75L17.81 9.93l-3.75-3.75z"/></svg>`;
const ICON_PLUS   = `<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z"/></svg>`;
const ICON_TRASH  = `<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12M19 4h-3.5l-1-1h-5l-1 1H5v2h14z"/></svg>`;

const CSS = `
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:host {
  display: block;
  padding: 16px;
  min-height: 100%;
  background: var(--primary-background-color, #f0f2f5);
  font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
  color: var(--primary-text-color, #212121);
}

/* ── Header ── */
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -.01em;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title svg { width: 26px; height: 26px; fill: var(--primary-color, #fdd835); }

.add-zone-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: none;
  background: var(--primary-color, #03a9f4);
  color: #fff;
  font-size: .82rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .15s;
}
.add-zone-btn:hover { opacity: .85; }
.add-zone-btn svg { width: 16px; height: 16px; fill: #fff; }

.sys-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.sys-label {
  font-size: .82rem;
  color: var(--secondary-text-color, #757575);
}
.sys-btn {
  padding: 4px 16px;
  border-radius: 20px;
  border: 1.5px solid var(--divider-color, #d0d0d0);
  background: transparent;
  cursor: pointer;
  font-size: .82rem;
  font-weight: 500;
  color: var(--primary-text-color, #212121);
  transition: background .15s, border-color .15s, color .15s;
}
.sys-btn:hover { background: var(--secondary-background-color, #e8e8e8); }
.sys-btn.active {
  background: var(--primary-color, #03a9f4);
  border-color: transparent;
  color: #fff;
}

/* ── Zone grid ── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(288px, 1fr));
  gap: 14px;
}

/* ── Zone card ── */
.card {
  background: var(--card-background-color, #fff);
  border-radius: 14px;
  padding: 14px 16px 12px;
  box-shadow: 0 1px 5px rgba(0,0,0,.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.zone-name {
  font-size: 1rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.badge {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: .68rem;
  font-weight: 700;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.icon-btn {
  flex-shrink: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  color: var(--secondary-text-color, #888);
  transition: background .15s, color .15s;
}
.icon-btn:hover { background: var(--secondary-background-color, #f0f0f0); color: var(--primary-text-color, #212121); }
.icon-btn.danger:hover { background: rgba(239,83,80,.1); color: #ef5350; }
.icon-btn svg { width: 16px; height: 16px; fill: currentColor; }

/* ── Indicators ── */
.indicators {
  display: flex;
  gap: 12px;
}
.ind {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: .75rem;
  color: var(--disabled-text-color, #c0c0c0);
  transition: color .2s;
}
.ind.on { color: #4caf50; }
.ind svg { width: 14px; height: 14px; fill: currentColor; flex-shrink: 0; }

/* ── Active scene ── */
.scene-row {
  font-size: .75rem;
  color: var(--secondary-text-color, #757575);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 1em;
}

/* ── Action buttons ── */
.actions {
  display: flex;
  gap: 6px;
}
.btn {
  flex: 1;
  padding: 6px 0;
  border-radius: 8px;
  border: 1px solid var(--divider-color, #e0e0e0);
  background: transparent;
  cursor: pointer;
  font-size: .82rem;
  font-weight: 500;
  color: var(--primary-text-color, #212121);
  transition: background .15s;
}
.btn:hover { background: var(--secondary-background-color, #f5f5f5); }
.btn.primary {
  background: var(--primary-color, #03a9f4);
  border-color: transparent;
  color: #fff;
}
.btn.primary:hover { opacity: .88; }

/* ── Mode pills ── */
.mode-pills { display: flex; gap: 5px; }
.pill {
  flex: 1;
  padding: 4px 0;
  border-radius: 10px;
  border: 1.5px solid var(--divider-color, #e0e0e0);
  background: transparent;
  cursor: pointer;
  font-size: .74rem;
  font-weight: 500;
  color: var(--secondary-text-color, #666);
  transition: border-color .15s, color .15s;
}
.pill.active {
  border-color: var(--primary-color, #03a9f4);
  color: var(--primary-color, #03a9f4);
  font-weight: 700;
}

/* ── Brightness slider ── */
.brightness-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.brightness-row input[type=range] {
  flex: 1;
  height: 4px;
  accent-color: var(--primary-color, #03a9f4);
  cursor: pointer;
}
.brightness-label {
  font-size: .75rem;
  color: var(--secondary-text-color, #888);
  min-width: 36px;
  text-align: right;
}

/* ── Confirm overlay ── */
.confirm-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .8rem;
  color: #ef5350;
  margin-top: 2px;
}
.confirm-row button {
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid #ef5350;
  background: transparent;
  color: #ef5350;
  cursor: pointer;
  font-size: .78rem;
}
.confirm-row button.yes {
  background: #ef5350;
  color: #fff;
  border-color: transparent;
}

/* ── Empty state ── */
.empty {
  text-align: center;
  padding: 64px 20px;
  color: var(--secondary-text-color, #757575);
  line-height: 1.7;
}
.empty svg { width: 72px; height: 72px; fill: var(--disabled-text-color, #ccc); display: block; margin: 0 auto 16px; }
.empty b { color: var(--primary-text-color, #212121); }
`;

class ILCPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._rafPending = false;
    this._entryId = null;
    this._confirmDelete = null; // zone_id pending confirmation
  }

  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  _scheduleRender() {
    if (this._rafPending) return;
    this._rafPending = true;
    requestAnimationFrame(() => {
      this._rafPending = false;
      this._render();
    });
  }

  // ── Data helpers ──────────────────────────────────────────────────────────

  _getZones() {
    if (!this._hass) return [];
    const zones = [];
    for (const [entityId, state] of Object.entries(this._hass.states)) {
      if (!entityId.startsWith("sensor.")) continue;
      const a = state.attributes;
      if (!a || typeof a.zone_id !== "string") continue;
      zones.push({
        entityId,
        zoneId:           a.zone_id,
        zoneName:         a.zone_name || a.zone_id,
        state:            state.state,
        mode:             a.mode || "auto",
        lightsOn:         !!a.lights_on,
        activeScene:      a.active_scene || null,
        motionDetected:   !!a.motion_detected,
        presenceDetected: !!a.presence_detected,
        brightnessPct:    a.brightness_pct != null ? a.brightness_pct : 100,
      });
    }
    zones.sort((a, b) => a.zoneName.localeCompare(b.zoneName));
    return zones;
  }

  _getSystemMode() {
    if (!this._hass) return "auto";
    for (const state of Object.values(this._hass.states)) {
      const fn = (state.attributes.friendly_name || "").toLowerCase();
      if (fn.includes("systemmodus") || fn.includes("system mode")) return state.state;
    }
    return "auto";
  }

  async _getEntryId() {
    if (this._entryId) return this._entryId;
    try {
      const entries = await this._hass.callWS({ type: "config_entries/get", domain: ILC_DOMAIN });
      if (entries && entries.length > 0) {
        this._entryId = entries[0].entry_id;
        return this._entryId;
      }
    } catch (e) {
      console.error("[ILC Panel] Could not get entry ID:", e);
    }
    return null;
  }

  async _navigate(path) {
    history.pushState(null, "", path);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
  }

  async _openOptions() {
    const entryId = await this._getEntryId();
    if (entryId) {
      this._navigate(`/config/integrations/integration/${ILC_DOMAIN}`);
    }
  }

  async _call(service, data) {
    if (!this._hass) return;
    try {
      await this._hass.callService(ILC_DOMAIN, service, data);
    } catch (err) {
      console.error("[ILC Panel] Service call failed:", service, err);
    }
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── Card template ─────────────────────────────────────────────────────────

  _renderCard(z) {
    const label     = STATE_LABELS[z.state] || z.state;
    const color     = STATE_COLORS[z.state] || "#9e9e9e";
    const sceneName = z.activeScene
      ? z.activeScene.replace(/^scene\./, "").replace(/_/g, " ")
      : "";
    const confirmingDelete = this._confirmDelete === z.zoneId;

    const modeRow = ["auto", "manual", "off"].map((m) => `
      <button class="pill${z.mode === m ? " active" : ""}"
        data-action="mode" data-zone="${this._esc(z.zoneId)}" data-mode="${m}">
        ${MODE_LABELS[m]}
      </button>`).join("");

    const deleteRow = confirmingDelete
      ? `<div class="confirm-row">
          Wirklich löschen?
          <button class="yes" data-action="delete-confirm" data-zone="${this._esc(z.zoneId)}">Ja</button>
          <button data-action="delete-cancel">Abbrechen</button>
         </div>`
      : "";

    return `
      <div class="card">
        <div class="card-header">
          <span class="zone-name">${this._esc(z.zoneName)}</span>
          <span class="badge" style="background:${color}">${label}</span>
          <button class="icon-btn" data-action="edit" data-zone="${this._esc(z.zoneId)}" title="Zone bearbeiten">
            ${ICON_EDIT}
          </button>
          <button class="icon-btn danger" data-action="delete" data-zone="${this._esc(z.zoneId)}" title="Zone löschen">
            ${ICON_TRASH}
          </button>
        </div>
        <div class="indicators">
          <span class="ind${z.lightsOn ? " on" : ""}">
            ${ICON_BULB} Licht
          </span>
          <span class="ind${z.motionDetected ? " on" : ""}">
            ${ICON_MOTION} Bewegung
          </span>
          <span class="ind${z.presenceDetected ? " on" : ""}">
            ${ICON_PERSON} Präsenz
          </span>
        </div>
        <div class="scene-row">${sceneName ? "▶ " + this._esc(sceneName) : ""}</div>
        <div class="actions">
          <button class="btn primary" data-action="on"     data-zone="${this._esc(z.zoneId)}">An</button>
          <button class="btn"         data-action="off"    data-zone="${this._esc(z.zoneId)}">Aus</button>
          <button class="btn"         data-action="toggle" data-zone="${this._esc(z.zoneId)}">Toggle</button>
        </div>
        <div class="brightness-row">
          <input type="range" min="0" max="100" step="5"
            value="${z.brightnessPct}"
            data-action="brightness" data-zone="${this._esc(z.zoneId)}">
          <span class="brightness-label">${z.brightnessPct}%</span>
        </div>
        <div class="mode-pills">${modeRow}</div>
        ${deleteRow}
      </div>`;
  }

  // ── Full render ───────────────────────────────────────────────────────────

  _render() {
    if (!this.shadowRoot) return;
    if (!this._hass) {
      this.shadowRoot.innerHTML = `<style>${CSS}</style><div style="padding:20px">Lädt…</div>`;
      return;
    }

    const zones   = this._getZones();
    const sysMode = this._getSystemMode();

    const sysButtons = ["auto", "manual", "off"].map((m) => `
      <button class="sys-btn${sysMode === m ? " active" : ""}"
        data-action="sysmode" data-mode="${m}">${SYS_LABELS[m]}</button>`).join("");

    const content = zones.length === 0
      ? `<div class="empty">
          <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7zm0 2a5 5 0 0 0-5 5c0 1.87 1.04 3.5 2.7 4.39L11 14.12V16h2v-1.88l1.3-.73C15.96 12.5 17 10.87 17 9a5 5 0 0 0-5-5zm-1 15h2v1h-2z"/></svg>
          <p><b>Keine Zonen konfiguriert</b></p>
          <p>Klicke auf <b>+ Zone hinzufügen</b> oben links.</p>
         </div>`
      : `<div class="grid">${zones.map((z) => this._renderCard(z)).join("")}</div>`;

    this.shadowRoot.innerHTML = `
      <style>${CSS}</style>
      <div class="header">
        <div class="header-left">
          <div class="title">
            <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7zm0 2a5 5 0 0 0-5 5c0 1.87 1.04 3.5 2.7 4.39L11 14.12V16h2v-1.88l1.3-.73C15.96 12.5 17 10.87 17 9a5 5 0 0 0-5-5zm-1 15h2v1h-2z"/></svg>
            Intelligent Light Control
          </div>
          <button class="add-zone-btn" data-action="add-zone">
            ${ICON_PLUS} Zone hinzufügen
          </button>
        </div>
        <div class="sys-row">
          <span class="sys-label">Systemmodus:</span>
          ${sysButtons}
        </div>
      </div>
      ${content}`;

    this.shadowRoot.querySelectorAll("[data-action]").forEach((el) => {
      if (el.type === "range") {
        el.addEventListener("change", (e) => {
          e.stopPropagation();
          this._handleBrightness(el);
        });
        // Live label update while dragging (no service call yet)
        el.addEventListener("input", (e) => {
          const label = el.closest(".brightness-row").querySelector(".brightness-label");
          if (label) label.textContent = el.value + "%";
        });
      } else {
        el.addEventListener("click", (e) => {
          e.stopPropagation();
          this._handleClick(el);
        });
      }
    });
  }

  _handleBrightness(el) {
    const pct = parseInt(el.value, 10);
    this._call("set_brightness", { zone_id: el.dataset.zone, brightness_pct: pct });
  }

  async _handleClick(el) {
    const { action, zone, mode } = el.dataset;
    switch (action) {
      case "on":      this._call("turn_on_zone",    { zone_id: zone }); break;
      case "off":     this._call("turn_off_zone",   { zone_id: zone }); break;
      case "toggle":  this._call("toggle_zone",     { zone_id: zone }); break;
      case "mode":    this._call("set_zone_mode",   { zone_id: zone, mode }); break;
      case "sysmode": this._call("set_system_mode", { mode }); break;

      case "add-zone":
        this._openOptions();
        break;

      case "edit":
        // Navigate to the options flow; user picks the zone there
        this._openOptions();
        break;

      case "delete":
        // Show inline confirm
        this._confirmDelete = zone;
        this._render();
        break;

      case "delete-confirm":
        this._confirmDelete = null;
        await this._call("remove_zone", { zone_id: zone });
        break;

      case "delete-cancel":
        this._confirmDelete = null;
        this._render();
        break;
    }
  }
}

customElements.define("ilc-panel", ILCPanel);
