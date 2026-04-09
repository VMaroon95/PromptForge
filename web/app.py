"""
PromptForge Web — mobile-friendly Flask interface.
Run: python web/app.py  (then open http://localhost:5000)
"""

import sys
import os

# Make promptforge importable when running from /web
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, render_template
from promptforge.optimizer import optimize
from promptforge.scorer import score_prompt
from promptforge.models import list_models, get_model
from promptforge.tokenizer import token_delta

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    model  = data.get("model") or None
    skip   = data.get("skip_passes") or []

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    if len(prompt) > 20_000:
        return jsonify({"error": "Prompt too long (max 20,000 characters)"}), 400

    try:
        result = optimize(prompt, model=model, skip_passes=skip)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    passes_detail = [
        {
            "name": p.name,
            "changed": p.changed,
            "before_len": len(p.before),
            "after_len": len(p.after),
        }
        for p in result.passes
    ]

    return jsonify({
        "original":       result.original,
        "optimized":      result.optimized,
        "changed":        result.original != result.optimized,
        "model":          model,
        "passes_applied": result.passes_applied,
        "passes_detail":  passes_detail,
        "score_before":   result.score_before.breakdown(),
        "score_after":    result.score_after.breakdown(),
        "quality_delta":  result.quality_delta,
        "token_stats":    result.token_stats,
    })


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data   = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        score = score_prompt(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"score": score.breakdown()})


@app.route("/api/models")
def api_models():
    models = []
    for name in list_models():
        cfg = get_model(name)
        models.append({
            "name":         name,
            "family":       cfg.family,
            "context":      cfg.context_window,
            "prefers_xml":  cfg.prefers_xml,
            "notes":        cfg.notes,
        })
    return jsonify({"models": models})


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "1") == "1"
    print(f"\n  PromptForge Web  →  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
