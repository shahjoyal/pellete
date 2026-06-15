/**
 * api_bridge.js
 * =============
 * Replaces the original client-side localStorage persistence and
 * the fake runSimulation() animation-only flow with real Flask API calls.
 *
 * Include this file AFTER the dashboard HTML's own <script> block.
 * It patches window functions in-place so the rest of the UI is untouched.
 */

(function () {
  "use strict";

  // ── State save / load via Flask ──────────────────────────────────────────

  async function saveStateToServer() {
    try {
      const plantNameEl = document.getElementById("plantName");
      const plantCapEl  = document.getElementById("plantCapacity");
      const payload = {
        plantName:     plantNameEl ? plantNameEl.value : "",
        plantCapacity: plantCapEl  ? plantCapEl.value  : "",
        stageParams:   typeof stageParams !== "undefined" ? stageParams : {},
      };
      await fetch("/api/state", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });
    } catch (e) {
      console.warn("[api_bridge] saveStateToServer failed:", e);
    }
  }

  async function loadStateFromServer() {
    try {
      const res  = await fetch("/api/state");
      const data = await res.json();
      if (data.status === "ok" && data.state && Object.keys(data.state).length) {
        const s = data.state;
        const plantNameEl = document.getElementById("plantName");
        const plantCapEl  = document.getElementById("plantCapacity");
        if (plantNameEl && s.plantName)     plantNameEl.value = s.plantName;
        if (plantCapEl  && s.plantCapacity) plantCapEl.value  = s.plantCapacity;
        if (s.stageParams && typeof stageParams !== "undefined") {
          Object.keys(s.stageParams).forEach(function (key) {
            if (stageParams[key] !== undefined) {
              Object.assign(stageParams[key], s.stageParams[key]);
            }
          });
        }
      }
    } catch (e) {
      console.warn("[api_bridge] loadStateFromServer failed:", e);
    }
  }

  // Patch the original saveStateToStorage / loadStateFromStorage
  window.saveStateToStorage  = saveStateToServer;
  window.loadStateFromStorage = loadStateFromServer;


  // ── Prediction call & result rendering ──────────────────────────────────

  async function callPredict() {
    const plantNameEl = document.getElementById("plantName");
    const plantCapEl  = document.getElementById("plantCapacity");

    const payload = {
      plantName:     plantNameEl ? plantNameEl.value : "",
      plantCapacity: plantCapEl  ? Number(plantCapEl.value) || 0 : 0,
      stageParams:   typeof stageParams !== "undefined" ? stageParams : {},
    };

    try {
      const res  = await fetch("/api/predict", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.status === "ok") {
        renderPredictions(data.predictions);
      } else {
        showPredictError(data.error || "Prediction failed");
      }
    } catch (e) {
      showPredictError("Network error: " + e.message);
    }
  }

  function renderPredictions(p) {
    if (!p) return;

    // ── Helper: update any element by id ────────────────────────────────
    function setText(id, val, suffix) {
      const el = document.getElementById(id);
      if (el) el.textContent = (val !== undefined && val !== null) ? val + (suffix || "") : "—";
    }

    // Pellet Quality
    const q = p.pelletQuality || {};
    setText("pred-ccs",      q.ccs,      " kg");
    setText("pred-tumbler",  q.tumbler,  "%");
    setText("pred-abrasion", q.abrasion, "%");
    setText("pred-fe",       q.fe,       "%");
    setText("pred-porosity", q.porosity, "%");

    // Size distribution
    const sd = p.sizeDistribution || {};
    setText("pred-size8",  sd.size8_10,  "%");
    setText("pred-size10", sd.size10_12, "%");
    setText("pred-size12", sd.size12_14, "%");
    setText("pred-size14", sd.size14_16, "%");

    // Operational KPIs – reuse the existing summary param boxes if present
    const kpi = p.operationalKPIs || {};
    setText("p-yield",       kpi.yield,         "%");
    setText("pred-energy",   kpi.energyPerTon,  " kcal/t");
    setText("pred-blain",    kpi.blainAchieved, " cm²/g");
    setText("pred-prod",     kpi.productivity,  " t/h");

    // Recommendations
    const recEl = document.getElementById("pred-recommendations");
    if (recEl && p.recommendations) {
      recEl.innerHTML = p.recommendations
        .map(function (r) { return "<li>" + r + "</li>"; })
        .join("");
    }

    // Show result panel if present
    const panel = document.getElementById("predictions-panel");
    if (panel) panel.style.display = "block";
  }

  function showPredictError(msg) {
    console.error("[api_bridge] Predict error:", msg);
    const el = document.getElementById("pred-error");
    if (el) {
      el.textContent = "⚠ " + msg;
      el.style.display = "block";
    } else {
      alert("Prediction error: " + msg);
    }
  }


  // ── Patch runSimulation to also call the ML API ──────────────────────────

  var _origRunSimulation = window.runSimulation;

  window.runSimulation = function () {
    // Run original UI animation
    if (typeof _origRunSimulation === "function") {
      _origRunSimulation.apply(this, arguments);
    }
    // Also hit the Flask prediction endpoint
    callPredict();
  };


  // ── Auto-load state on page load ────────────────────────────────────────

  window.addEventListener("load", function () {
    loadStateFromServer();
  });

})();
