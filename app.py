"""
Iron Ore Pelletization – Flask Application
==========================================
All existing UI, animations, and diagrams are preserved.
The "Run Pelletization Simulation" button now calls /api/predict
with the collected stageParams JSON and returns ML predictions.
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
import json
import traceback

# ── Import your ML model here ──────────────────────────────────────────────
# from ml.model import predict   # uncomment when model is ready
# ──────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "CHANGE_ME_IN_PRODUCTION"   # replace with os.urandom(32) in prod


# ─────────────────────────────────────────────────────────────────────────────
# Auth helpers  (simple session-based; swap for JWT / OAuth as needed)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_USERS = {
    "admin": "admin123",      # replace with proper hashed credentials
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Page routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if DEMO_USERS.get(username) == password:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard_page1"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard/page1")
@login_required
def dashboard_page1():
    return render_template("dashboard_page1.html")


@app.route("/dashboard/page2")
@login_required
def dashboard_page2():
    return render_template("dashboard_page2.html")


@app.route("/dashboard/page3")
@login_required
def dashboard_page3():
    return render_template("dashboard_page3.html")


# ─────────────────────────────────────────────────────────────────────────────
# API – prediction endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    """
    Accepts the full stageParams JSON from the frontend and returns ML predictions.

    Request body (JSON):
    {
      "plantName":     string,
      "plantCapacity": number,
      "stageParams": {
        "feed":      { ore, orePercent, feedRate, fluxes, fuels, zone, location,
                       loi, chemMoisture, chemFe, chemSio2, chemAl2o3,
                       chemBlain, chemMic45, chemBentonite, chemOb1205,
                       chemCcs, chemTi, chemAi },
        "grind":     { rawFeedMoisture, blain, millSpeed, retentionTime },
        "thickner":  { underflowDensity, vacuumPressure },
        "filter":    { cakeMoisture, vacuumPressure },
        "mix":       { binder, bentonite, bentoniteType, bentoniteDosageValue,
                       bentoniteDosageUnit, dosageValue, dosageUnit,
                       fluxes, mixMoisture, waterAddition },
        "ball":      { angle, motorRpm, discRpm, greenBallMoisture, waterSprayRate },
        "greenball": { moisture, dropNumber, gcs, greenBallSize, porosity },
        "screen":    { s8_10, s10_12, s12_14, s14_16, recycled, recycledUnit },
        "indu":      { mode, rpm, btt, drm, exhaust,
                       tgRpm, mcTemp, tgDischarge, tgExhaust },
        "cool":      { zone1, zone2, zone3, zone4, zoneCount },
        "pellet":    { size8_10, size10_12, size12_14, size14_16, cracked,
                       ccs, tumbler, abrasion, fe }
      }
    }

    Response (JSON):
    {
      "status":  "ok" | "error",
      "predictions": {
        "pelletQuality": {
          "ccs":      number,   // Cold Crushing Strength (kg/pellet)
          "tumbler":  number,   // Tumbler Index (%)
          "abrasion": number,   // Abrasion Index (%)
          "fe":       number,   // Fe content (%)
          "porosity": number    // Porosity (%)
        },
        "sizeDistribution": {
          "size8_10":  number,  // % in 8-10 mm
          "size10_12": number,  // % in 10-12 mm
          "size12_14": number,  // % in 12-14 mm
          "size14_16": number   // % in 14-16 mm
        },
        "operationalKPIs": {
          "yield":         number,   // %
          "productivity":  number,   // t/h
          "energyPerTon":  number,   // kcal/t
          "blainAchieved": number    // cm²/g
        },
        "recommendations": [string]  // optional list of text suggestions
      },
      "error": string   // only present when status == "error"
    }
    """
    try:
        body = request.get_json(force=True)
        if not body:
            return jsonify({"status": "error", "error": "Empty request body"}), 400

        stage_params  = body.get("stageParams", {})
        plant_name    = body.get("plantName", "")
        plant_capacity = body.get("plantCapacity", 0)

        # ── Validate minimum required inputs ──────────────────────────────
        missing = _check_required_fields(stage_params)
        if missing:
            return jsonify({
                "status": "error",
                "error":  f"Missing required fields: {', '.join(missing)}"
            }), 422

        # ── Prepare feature vector for ML model ───────────────────────────
        features = _build_feature_vector(stage_params, plant_capacity)

        # ── Call ML model ─────────────────────────────────────────────────
        #
        # Replace the stub below with your actual model call:
        #
        #   predictions = predict(features)
        #
        predictions = _stub_predict(features, stage_params)

        return jsonify({"status": "ok", "predictions": predictions})

    except Exception:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": "error", "error": "Internal server error"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# API – save / load state  (optional persistence layer)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/state", methods=["POST"])
@login_required
def save_state():
    """Persist operator-entered state server-side (optional)."""
    data = request.get_json(force=True)
    # TODO: store `data` in a database keyed by session["username"]
    return jsonify({"status": "ok"})


@app.route("/api/state", methods=["GET"])
@login_required
def load_state():
    """Load previously saved state (optional)."""
    # TODO: retrieve from database
    return jsonify({"status": "ok", "state": {}})


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _check_required_fields(sp: dict) -> list:
    """Return a list of human-readable missing required fields."""
    required = {
        "feed.ore":               sp.get("feed", {}).get("ore"),
        "grind.blain":            sp.get("grind", {}).get("blain"),
        "filter.cakeMoisture":    sp.get("filter", {}).get("cakeMoisture"),
        "ball.angle":             sp.get("ball", {}).get("angle"),
        "indu.mode":              sp.get("indu", {}).get("mode"),
    }
    return [k for k, v in required.items() if not v]


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_feature_vector(sp: dict, capacity) -> dict:
    """
    Flatten stageParams into a dict of floats for the ML model.
    Extend / modify this mapping to match your model's expected input.
    """
    feed      = sp.get("feed", {})
    grind     = sp.get("grind", {})
    thickner  = sp.get("thickner", {})
    filt      = sp.get("filter", {})
    mix       = sp.get("mix", {})
    ball      = sp.get("ball", {})
    gb        = sp.get("greenball", {})
    screen    = sp.get("screen", {})
    indu      = sp.get("indu", {})
    cool      = sp.get("cool", {})

    ore_map = {"Hematite": 0, "Magnetite": 1, "Limonite": 2, "Goethite": 3}

    return {
        # Plant
        "plant_capacity":         _safe_float(capacity),
        # Feed
        "ore_type":               ore_map.get(feed.get("ore", ""), -1),
        "ore_percent":            _safe_float(feed.get("orePercent")),
        "feed_rate":              _safe_float(feed.get("feedRate")),
        "loi":                    _safe_float(feed.get("loi")),
        "chem_moisture":          _safe_float(feed.get("chemMoisture")),
        "chem_fe":                _safe_float(feed.get("chemFe")),
        "chem_sio2":              _safe_float(feed.get("chemSio2")),
        "chem_al2o3":             _safe_float(feed.get("chemAl2o3")),
        "chem_blain":             _safe_float(feed.get("chemBlain")),
        "chem_mic45":             _safe_float(feed.get("chemMic45")),
        # Grinding
        "raw_feed_moisture":      _safe_float(grind.get("rawFeedMoisture")),
        "blain":                  _safe_float(grind.get("blain")),
        "mill_speed":             _safe_float(grind.get("millSpeed")),
        "retention_time":         _safe_float(grind.get("retentionTime")),
        # Thickener
        "underflow_density":      _safe_float(thickner.get("underflowDensity")),
        "thickner_vacuum":        _safe_float(thickner.get("vacuumPressure")),
        # Filter
        "cake_moisture":          _safe_float(filt.get("cakeMoisture")),
        "filter_vacuum":          _safe_float(filt.get("vacuumPressure")),
        # Mixing / Binder
        "bentonite_dosage":       _safe_float(mix.get("bentoniteDosageValue")),
        "ob_dosage":              _safe_float(mix.get("dosageValue")),
        "mix_moisture":           _safe_float(mix.get("mixMoisture")),
        "water_addition":         _safe_float(mix.get("waterAddition")),
        # Balling disc
        "disc_angle":             _safe_float(ball.get("angle")),
        "motor_rpm":              _safe_float(ball.get("motorRpm")),
        "disc_rpm":               _safe_float(ball.get("discRpm")),
        "green_ball_moisture":    _safe_float(ball.get("greenBallMoisture")),
        "water_spray_rate":       _safe_float(ball.get("waterSprayRate")),
        # Green ball properties
        "gb_moisture":            _safe_float(gb.get("moisture")),
        "gb_drop_number":         _safe_float(gb.get("dropNumber")),
        "gb_gcs":                 _safe_float(gb.get("gcs")),
        "gb_size":                _safe_float(gb.get("greenBallSize")),
        "gb_porosity":            _safe_float(gb.get("porosity")),
        # Screen
        "screen_s8_10":           _safe_float(screen.get("s8_10")),
        "screen_s10_12":          _safe_float(screen.get("s10_12")),
        "screen_s12_14":          _safe_float(screen.get("s12_14")),
        "screen_s14_16":          _safe_float(screen.get("s14_16")),
        "recycled":               _safe_float(screen.get("recycled")),
        # Induration
        "indu_mode":              1 if indu.get("mode") == "grate" else 0,
        "indu_rpm":               _safe_float(indu.get("rpm")),
        "indu_btt":               _safe_float(indu.get("btt")),
        "indu_drm":               _safe_float(indu.get("drm")),
        "indu_exhaust":           _safe_float(indu.get("exhaust")),
        "tg_rpm":                 _safe_float(indu.get("tgRpm")),
        "mc_temp":                _safe_float(indu.get("mcTemp")),
        "tg_discharge":           _safe_float(indu.get("tgDischarge")),
        "tg_exhaust":             _safe_float(indu.get("tgExhaust")),
        # Cooling
        "cool_zone1":             _safe_float(cool.get("zone1")),
        "cool_zone2":             _safe_float(cool.get("zone2")),
        "cool_zone3":             _safe_float(cool.get("zone3")),
        "cool_zone4":             _safe_float(cool.get("zone4")),
    }


def _stub_predict(features: dict, sp: dict) -> dict:
    """
    STUB – replace this entire function body with your real ML model call.

    The stub derives plausible-looking values from the input features so
    that the frontend can be developed / tested before the model is ready.
    """
    blain       = features.get("blain", 2000)
    cake_moist  = features.get("cake_moisture", 10)
    disc_angle  = features.get("disc_angle", 45)
    gb_gcs      = features.get("gb_gcs", 1.2)
    mc_temp     = features.get("mc_temp", 1250)

    # Simulated outputs
    ccs      = round(max(200, min(400, 150 + blain * 0.06 + mc_temp * 0.03)), 1)
    tumbler  = round(max(88, min(98, 82 + blain * 0.002)), 1)
    abrasion = round(max(3, min(10, 12 - blain * 0.003)), 2)
    fe_out   = round(features.get("chem_fe", 63.5), 2)
    porosity = round(max(18, min(28, 25 - cake_moist * 0.4)), 1)
    yield_pct = round(max(70, min(95, 70 + (blain - 1800) * 0.008)), 1)

    return {
        "pelletQuality": {
            "ccs":      ccs,
            "tumbler":  tumbler,
            "abrasion": abrasion,
            "fe":       fe_out,
            "porosity": porosity,
        },
        "sizeDistribution": {
            "size8_10":  round(_safe_float(sp.get("pellet", {}).get("size8_10"), 5), 1),
            "size10_12": round(_safe_float(sp.get("pellet", {}).get("size10_12"), 45), 1),
            "size12_14": round(_safe_float(sp.get("pellet", {}).get("size12_14"), 40), 1),
            "size14_16": round(_safe_float(sp.get("pellet", {}).get("size14_16"), 10), 1),
        },
        "operationalKPIs": {
            "yield":         yield_pct,
            "productivity":  round(features.get("plant_capacity", 120) * yield_pct / 100, 1),
            "energyPerTon":  round(max(400, 700 - blain * 0.05), 0),
            "blainAchieved": blain,
        },
        "recommendations": _generate_recommendations(features),
    }


def _generate_recommendations(f: dict) -> list:
    tips = []
    if f["blain"] < 1900:
        tips.append("Increase grinding time — Blain below 1900 cm²/g may reduce pellet strength.")
    if f["cake_moisture"] > 12:
        tips.append("Filter cake moisture is high (>12%). Check vacuum pressure.")
    if f["disc_angle"] < 40:
        tips.append("Disc angle below 40° may lead to oversized green balls.")
    if f["mc_temp"] > 1280:
        tips.append("Machine cooler temperature is high. Monitor refractory wear.")
    if not tips:
        tips.append("Parameters are within optimal ranges.")
    return tips


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
