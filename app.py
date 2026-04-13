"""
EcoSphere - AI-Based Waste Detection and Recycling Recommendation System
Backend: Flask API

To run:
  pip install -r requirements.txt
  python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import time
import io
import math
from PIL import Image

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# Waste Metadata
# ─────────────────────────────────────────────────────────────
WASTE_METADATA = {
    "Plastic": {
        "color": "#B8D4F5",
        "icon": "bottle",
        "pricePerKg": 10,
        "recommendation": "Clean and sort plastic items. Remove caps and labels. Crush bottles to save space. Take to your nearest plastic recycling center. Avoid mixing different plastic types."
    },
    "Metal": {
        "color": "#D4C5F5",
        "icon": "wrench",
        "pricePerKg": 25,
        "recommendation": "Separate ferrous (iron/steel) from non-ferrous metals (aluminum, copper). Clean off food residues. Metal cans can be crushed. Metal scraps fetch the highest prices at recycling centers."
    },
    "Paper": {
        "color": "#F5E6B8",
        "icon": "file",
        "pricePerKg": 8,
        "recommendation": "Keep paper dry and clean. Remove plastic covers and staples. Bundle newspapers together. Shred sensitive documents before recycling. Avoid recycling wax-coated or food-soiled paper."
    },
    "Glass": {
        "color": "#B8F5D4",
        "icon": "cup",
        "pricePerKg": 5,
        "recommendation": "Separate glass by color (clear, green, brown). Rinse containers. Remove metal lids. Do not mix broken glass — wrap it safely. Glass is 100% recyclable."
    },
    "Organic": {
        "color": "#C5F5B8",
        "icon": "leaf",
        "pricePerKg": 3,
        "recommendation": "Compost fruit peels, vegetable scraps, and garden waste. Use a compost bin or pit. Avoid adding meat or dairy. Composted organic waste becomes nutrient-rich fertilizer."
    },
    "E-Waste": {
        "color": "#F5C5B8",
        "icon": "cpu",
        "pricePerKg": 50,
        "recommendation": "Never throw electronics in regular trash. Take to authorized e-waste collection centers. Many manufacturers offer take-back programs. Data should be wiped before disposal."
    },
    "Cardboard": {
        "color": "#F5D4B8",
        "icon": "package",
        "pricePerKg": 6,
        "recommendation": "Flatten cardboard boxes to save space. Remove tape and staples. Keep dry — wet cardboard has lower recycling value. Pizza boxes with grease should be composted."
    },
    "Textile": {
        "color": "#F5B8E6",
        "icon": "shirt",
        "pricePerKg": 12,
        "recommendation": "Donate wearable clothes to charity. Damaged textiles can be repurposed as rags. Some brands offer textile take-back programs."
    },
    "Rubber": {
        "color": "#C5C5F5",
        "icon": "circle",
        "pricePerKg": 7,
        "recommendation": "Old tires can be retreaded or recycled into rubber mats. Never burn rubber — it releases toxic gases. Check with local tire dealers for recycling options."
    },
    "Wood": {
        "color": "#F5D8B8",
        "icon": "tree",
        "pricePerKg": 4,
        "recommendation": "Untreated wood can be composted or chipped for mulch. Treated or painted wood requires special disposal. Wood offcuts can be donated to community workshops."
    }
}

# ─────────────────────────────────────────────────────────────
# 10 Predefined Recycling Centers
# ─────────────────────────────────────────────────────────────
RECYCLING_CENTERS = [
    {
        "id": "rc001",
        "name": "GreenEarth Recycling Hub",
        "address": "Plot 14, Industrial Area Phase 2",
        "city": "Mumbai",
        "phone": "+91 98765 43210",
        "supportedTypes": ["Plastic", "Metal", "Paper", "Glass", "Cardboard"],
        "operatingHours": "Mon-Sat: 9 AM - 6 PM",
        "rating": 4.5
    },
    {
        "id": "rc002",
        "name": "EcoRevive Center",
        "address": "Sector 15, Near Metro Station",
        "city": "Delhi",
        "phone": "+91 87654 32109",
        "supportedTypes": ["Plastic", "Paper", "Cardboard", "Textile", "Glass"],
        "operatingHours": "Mon-Sun: 8 AM - 7 PM",
        "rating": 4.7
    },
    {
        "id": "rc003",
        "name": "ScrapMasters Ltd",
        "address": "127, Old Market Road",
        "city": "Bangalore",
        "phone": "+91 76543 21098",
        "supportedTypes": ["Metal", "E-Waste", "Rubber", "Plastic"],
        "operatingHours": "Mon-Sat: 10 AM - 5 PM",
        "rating": 4.2
    },
    {
        "id": "rc004",
        "name": "TechWaste Solutions",
        "address": "IT Park, Tower B, Floor 1",
        "city": "Hyderabad",
        "phone": "+91 65432 10987",
        "supportedTypes": ["E-Waste", "Metal", "Plastic"],
        "operatingHours": "Mon-Fri: 9 AM - 5 PM",
        "rating": 4.8
    },
    {
        "id": "rc005",
        "name": "PaperPulp Recyclers",
        "address": "Mill Road, Industrial Estate",
        "city": "Chennai",
        "phone": "+91 54321 09876",
        "supportedTypes": ["Paper", "Cardboard", "Wood"],
        "operatingHours": "Mon-Sat: 8 AM - 4 PM",
        "rating": 4.1
    },
    {
        "id": "rc006",
        "name": "GlassCycle India",
        "address": "23, Glass Factory Road",
        "city": "Pune",
        "phone": "+91 43210 98765",
        "supportedTypes": ["Glass", "Plastic", "Metal"],
        "operatingHours": "Mon-Sun: 9 AM - 6 PM",
        "rating": 4.4
    },
    {
        "id": "rc007",
        "name": "Organic Composting Hub",
        "address": "Farm Lane, Near Agricultural University",
        "city": "Ahmedabad",
        "phone": "+91 32109 87654",
        "supportedTypes": ["Organic", "Wood", "Paper", "Cardboard"],
        "operatingHours": "Mon-Sat: 7 AM - 2 PM",
        "rating": 4.6
    },
    {
        "id": "rc008",
        "name": "TextileRenew Initiative",
        "address": "Garment District, Block C",
        "city": "Surat",
        "phone": "+91 21098 76543",
        "supportedTypes": ["Textile", "Rubber", "Plastic"],
        "operatingHours": "Mon-Fri: 10 AM - 6 PM",
        "rating": 4.3
    },
    {
        "id": "rc009",
        "name": "MetalWorld Scrapyard",
        "address": "Heavy Industrial Zone, Gate 3",
        "city": "Kolkata",
        "phone": "+91 10987 65432",
        "supportedTypes": ["Metal", "E-Waste", "Rubber", "Wood"],
        "operatingHours": "Mon-Sat: 8 AM - 5 PM",
        "rating": 4.0
    },
    {
        "id": "rc010",
        "name": "CleanCity Recycling Co.",
        "address": "Municipal Complex, Ward 7",
        "city": "Jaipur",
        "phone": "+91 09876 54321",
        "supportedTypes": ["Plastic", "Glass", "Paper", "Metal", "Cardboard", "Organic", "Textile"],
        "operatingHours": "Mon-Sun: 8 AM - 8 PM",
        "rating": 4.9
    }
]

# ─────────────────────────────────────────────────────────────
# Detection Stats (in-memory)
# ─────────────────────────────────────────────────────────────
detection_stats = {
    "totalDetections": 247,
    "wasteTypeCounts": {
        "Plastic": 89, "Metal": 45, "Paper": 38, "Glass": 27,
        "Organic": 21, "E-Waste": 14, "Cardboard": 8, "Textile": 3, "Rubber": 2
    },
    "totalEarnings": 4823.0
}


# ─────────────────────────────────────────────────────────────
# AI Detection Logic — Color Histogram Analysis
# ─────────────────────────────────────────────────────────────

def rgb_to_hsl(r, g, b):
    rn, gn, bn = r / 255, g / 255, b / 255
    mx, mn = max(rn, gn, bn), min(rn, gn, bn)
    l = (mx + mn) / 2
    if mx == mn:
        return 0, 0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == rn:
        h = ((gn - bn) / d + (6 if gn < bn else 0)) / 6
    elif mx == gn:
        h = ((bn - rn) / d + 2) / 6
    else:
        h = ((rn - gn) / d + 4) / 6
    return h * 360, s, l


def analyze_color_profile(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA").resize((50, 50))
    pixels = list(img.getdata())

    total = 0
    sum_l = sum_s = 0
    grey = metallic = white = dark = vivid = 0
    green = brown = blue = warm = 0
    hues = []

    for r, g, b, a in pixels:
        if a < 128:
            continue
        h, s, l = rgb_to_hsl(r, g, b)
        total += 1
        sum_l += l
        sum_s += s
        hues.append(h)

        if s < 0.18 and 0.25 < l < 0.88:
            grey += 1
        if s < 0.12 and 0.40 < l < 0.88:
            metallic += 1
        if l > 0.82 and s < 0.15:
            white += 1
        if l < 0.18:
            dark += 1
        if s > 0.45:
            vivid += 1
        if s > 0.20 and 88 <= h <= 168:
            green += 1
        if 10 <= h <= 42 and 0.18 <= s <= 0.70 and 0.22 <= l <= 0.65:
            brown += 1
        if s > 0.20 and 195 <= h <= 265:
            blue += 1
        if s > 0.25 and (h <= 75 or h >= 340):
            warm += 1

    if total == 0:
        return {}

    avg_l = sum_l / total
    avg_s = sum_s / total
    mean_h = sum(hues) / len(hues)
    hue_sd = math.sqrt(sum((h - mean_h) ** 2 for h in hues) / len(hues))
    hue_diversity = min(hue_sd / 120, 1.0)

    return {
        "avg_l": avg_l, "avg_s": avg_s,
        "grey": grey / total, "metallic": metallic / total,
        "white": white / total, "dark": dark / total,
        "vivid": vivid / total, "green": green / total,
        "brown": brown / total, "blue": blue / total,
        "warm": warm / total, "hue_div": hue_diversity,
    }


def score_waste_types(cp, filename=""):
    scores = {}
    m = cp.get

    scores["Metal"] = (
        m("metallic", 0) * 3.5 + m("grey", 0) * 2.0 +
        (1 - m("avg_s", 0.5)) * 1.0 +
        (0.8 if 0.35 < m("avg_l", 0) < 0.80 else 0) +
        (0.5 if m("hue_div", 1) < 0.3 else 0) +
        (0.4 if m("vivid", 1) < 0.1 else 0)
    )
    scores["Plastic"] = (
        m("vivid", 0) * 2.5 + m("hue_div", 0) * 1.5 +
        m("warm", 0) * 1.2 +
        (1.0 if m("avg_s", 0) > 0.25 else 0) +
        (0.5 if m("metallic", 1) < 0.25 else 0) +
        (0.3 if m("dark", 1) < 0.3 else 0)
    )
    scores["Paper"] = (
        m("white", 0) * 3.5 +
        (1.5 if m("avg_l", 0) > 0.75 else 0) +
        (1.0 if m("avg_s", 1) < 0.12 else 0)
    )
    scores["Glass"] = (
        m("white", 0) * 1.5 + m("green", 0) * 1.0 +
        (0.8 if m("avg_l", 0) > 0.60 else 0) +
        (1.0 if m("avg_s", 1) < 0.20 and m("avg_l", 0) > 0.55 else 0)
    )
    scores["Organic"] = (
        m("green", 0) * 3.0 + m("brown", 0) * 1.5 +
        (0.3 if m("metallic", 1) < 0.10 else 0)
    )
    scores["E-Waste"] = (
        (m("dark", 0) * 2.0 if m("dark", 0) > 0.25 else 0) +
        (1.2 if m("avg_l", 1) < 0.35 else 0) +
        (0.8 if m("hue_div", 0) > 0.4 and m("avg_l", 1) < 0.40 else 0)
    )
    scores["Cardboard"] = (
        m("brown", 0) * 3.5 +
        (0.8 if 0.30 < m("avg_l", 0) < 0.65 else 0) +
        (0.7 if 0.12 < m("avg_s", 0) < 0.45 else 0) +
        (0.5 if m("hue_div", 1) < 0.35 else 0) +
        (0.4 if m("metallic", 1) < 0.15 else 0)
    )
    scores["Textile"] = (
        (m("hue_div", 0) * 1.5 if m("hue_div", 0) > 0.5 else 0) +
        (0.8 if m("vivid", 0) > 0.20 else 0) +
        (0.5 if m("dark", 0) > 0.15 else 0)
    )
    scores["Rubber"] = (
        (m("dark", 0) * 2.5 if m("dark", 0) > 0.40 else 0) +
        (1.5 if m("avg_l", 1) < 0.25 else 0) +
        (0.8 if m("avg_s", 1) < 0.15 else 0)
    )
    scores["Wood"] = (
        m("brown", 0) * 2.5 +
        (0.6 if 0.10 < m("avg_s", 0) < 0.40 else 0) +
        (0.5 if 0.25 < m("avg_l", 0) < 0.60 else 0)
    )

    # Filename hints give a strong boost
    fn = (filename or "").lower()
    filename_hints = {
        "Plastic": ["plastic", "bottle", "bag", "poly", "pvc", "pet"],
        "Metal": ["metal", "iron", "steel", "aluminum", "aluminium", "tin", "copper", "can", "scrap", "foil"],
        "Paper": ["paper", "newspaper", "document", "book", "magazine"],
        "Glass": ["glass", "jar", "window"],
        "Organic": ["organic", "food", "vegetable", "fruit", "leaf", "garden", "compost"],
        "E-Waste": ["electronic", "phone", "computer", "laptop", "circuit", "battery", "ewaste", "e-waste", "pcb"],
        "Cardboard": ["cardboard", "box", "carton", "packaging"],
        "Textile": ["cloth", "textile", "fabric", "shirt", "dress", "garment"],
        "Rubber": ["rubber", "tire", "tyre", "boot"],
        "Wood": ["wood", "timber", "furniture", "plank"],
    }
    for waste_type, hints in filename_hints.items():
        if any(h in fn for h in hints):
            scores[waste_type] = scores.get(waste_type, 0) + 4.0

    return scores


def analyze_image_for_waste(image_base64: str, filename: str = "image.jpg"):
    """
    Smart waste detection using pixel color histogram analysis.
    In production, replace with YOLOv8 + MobileNetV3 inference.
    """
    img_bytes = base64.b64decode(image_base64)
    cp = analyze_color_profile(img_bytes)

    if not cp:
        return [{"type": "Plastic", "confidence": 1.0}]

    scores = score_waste_types(cp, filename)
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if not sorted_types:
        return [{"type": "Plastic", "confidence": 1.0}]

    top_score = sorted_types[0][1]
    threshold = top_score * 0.40
    selected = [(t, s) for t, s in sorted_types if s >= threshold][:4]

    # Softmax-style normalization
    exp_scores = [(t, math.exp(s * 0.6)) for t, s in selected]
    total_exp = sum(e for _, e in exp_scores)
    detections = [
        {"type": t, "confidence": round(e / total_exp, 3)}
        for t, e in exp_scores
    ]
    return sorted(detections, key=lambda x: x["confidence"], reverse=True)


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
@app.route("/api/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


@app.route("/api/predict", methods=["POST"])
def predict_waste():
    start_time = time.time()

    try:
        data = request.get_json()
        if not data or "imageBase64" not in data:
            return jsonify({"error": "Bad Request", "message": "imageBase64 is required"}), 400

        image_base64 = data["imageBase64"]
        filename = data.get("filename", "image.jpg")

        # Strip data URL prefix if present
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]

        # Analyze image
        raw_detections = analyze_image_for_waste(image_base64, filename)

        # Enrich detections
        detections = []
        for d in raw_detections:
            meta = WASTE_METADATA.get(d["type"], {
                "color": "#E0E0E0", "icon": "trash", "pricePerKg": 5,
                "recommendation": "Dispose at a designated recycling center."
            })
            detections.append({
                "type": d["type"],
                "confidence": d["confidence"],
                "color": meta["color"],
                "icon": meta["icon"],
                "pricePerKg": meta["pricePerKg"]
            })

        # Combine recommendations
        recommendation_parts = []
        for d in detections:
            meta = WASTE_METADATA.get(d["type"], {})
            pct = round(d["confidence"] * 100)
            rec = meta.get("recommendation", "Take to a recycling center.")
            recommendation_parts.append(f"{d['type']} ({pct}%): {rec}")
        recommendation = "\n\n".join(recommendation_parts)

        # Filter relevant centers
        detected_types = [d["type"] for d in detections]
        relevant_centers = [
            c for c in RECYCLING_CENTERS
            if any(t in detected_types for t in c["supportedTypes"])
        ][:5]

        # Calculate earnings (assume 1 kg per type, weighted by confidence)
        total_earning = sum(
            WASTE_METADATA.get(d["type"], {}).get("pricePerKg", 5) * d["confidence"]
            for d in detections
        )
        estimated_earning_value = round(total_earning, 2)
        estimated_earning = f"₹{int(estimated_earning_value)}"

        # Return original image as bounding box image (in production: draw actual boxes)
        bounding_box_image = f"data:image/jpeg;base64,{image_base64}"

        # Update stats
        detection_stats["totalDetections"] += 1
        detection_stats["totalEarnings"] += estimated_earning_value
        for d in detections:
            detection_stats["wasteTypeCounts"][d["type"]] = \
                detection_stats["wasteTypeCounts"].get(d["type"], 0) + 1

        analysis_time = round(time.time() - start_time, 2)

        return jsonify({
            "detections": detections,
            "recommendation": recommendation,
            "recyclingCenters": relevant_centers,
            "estimatedEarning": estimated_earning,
            "estimatedEarningValue": estimated_earning_value,
            "totalDetected": len(detections),
            "analysisTime": analysis_time,
            "boundingBoxImage": bounding_box_image
        })

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route("/api/recycling-centers", methods=["GET"])
def get_recycling_centers():
    waste_type = request.args.get("wasteType", "").strip()
    centers = RECYCLING_CENTERS
    if waste_type:
        centers = [
            c for c in RECYCLING_CENTERS
            if waste_type.lower() in [t.lower() for t in c["supportedTypes"]]
        ]
    return jsonify({"centers": centers, "total": len(centers)})


@app.route("/api/waste-stats", methods=["GET"])
def get_waste_stats():
    counts = detection_stats["wasteTypeCounts"]
    total_count = sum(counts.values())
    popular = sorted(
        [{"type": t, "count": c, "percentage": round(c / total_count * 100, 1) if total_count else 0}
         for t, c in counts.items()],
        key=lambda x: x["count"], reverse=True
    )
    top_earning = max(WASTE_METADATA.items(), key=lambda x: x[1]["pricePerKg"])[0]
    avg_earning = round(
        detection_stats["totalEarnings"] / detection_stats["totalDetections"], 2
    ) if detection_stats["totalDetections"] else 0

    return jsonify({
        "totalDetections": detection_stats["totalDetections"],
        "popularWasteTypes": popular,
        "averageEarning": avg_earning,
        "topEarningWaste": top_earning
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  EcoSphere AI Waste Detection System")
    print("  Backend running at http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
