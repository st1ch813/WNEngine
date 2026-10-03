import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Твой API-ключ OpenRouter (при деплое на Render лучше добавить его в Environment Variables)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Актуальная бесплатная модель без жестких гео-блокировок
MODEL_NAME = "nvidia/nemotron-3.5-lightning:free"

IC_SYSTEM_INSTRUCTION = """
Ты — профессиональный журналист издания Weazel News в штате Сан-Андреас (GTA RP).
Твоя задача — писать интересные, подробные и реалистичные IC-статьи, репортажи и интервью.

СТРОГИЕ ПРАВИЛА (ONLY IC):
1. ПРАВИЛО OOC: Категорически запрещено использовать OOC-термины: Majestic, Las-Vegas, сервер, фракция, крайм, госс, статик, админ, бан, РП, OOC, Discord, форум.
2. ТЕРМИНОЛОГИЯ:
   - Вместо "Las-Vegas / Сервер" -> "Штат Сан-Андреас", "город Лос-Сантос" или "округ Блейн".
   - Вместо "Фракция" -> "Организация", "Департамент", "Компания".
   - Вместо "Полиция / LSPD / FIB" -> "Правоохранительные органы", "Департамент полиции".
   - Вместо "Крайм" -> "Синдикаты", "Уличные группировки", "Подозрительные лица".
3. БЕЗ НЕЛЕГАЛА: Никакой рекламы оружия, наркотиков и призывов к нарушению закона.
4. ЯЗЫК: Русский.
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    topic = data.get("topic", "").strip()
    fmt = data.get("format", "Новости штата")
    refine = data.get("refine", "").strip()
    current_text = data.get("current_text", "").strip()

    if refine and current_text:
        prompt = f"Вот текущий текст статьи:\n---\n{current_text}\n---\n\nЗадание: Внеси следующие правки:\n{refine}\n\nСохрани стиль Weazel News и строгий IC."
    else:
        prompt = f"Задание: Напиши подробную IC-статью для Weazel News.\nФормат: {fmt}\nТема и детали: {topic}\n\nТребования: Заголовок, вступление, основная часть, подпись 'Weazel News — Главный источник новостей штата.'"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://weazelnews-studio.onrender.com",
        "X-Title": "Weazel News Studio",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    payload = {
        "model": MODEL_NAME,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": IC_SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=45)
        
        try:
            res_json = res.json()
        except Exception:
            return jsonify({"success": False, "error": f"Ошибка ответа OpenRouter: {res.text[:200]}"})

        if isinstance(res_json, dict) and "choices" in res_json and len(res_json["choices"]) > 0:
            return jsonify({"success": True, "text": res_json["choices"][0]["message"]["content"]})
        elif isinstance(res_json, dict) and "error" in res_json:
            err_msg = res_json["error"].get("message", "Неизвестная ошибка") if isinstance(res_json["error"], dict) else res_json["error"]
            return jsonify({"success": False, "error": f"OpenRouter Error: {err_msg}"})
        else:
            return jsonify({"success": False, "error": "Неизвестный формат ответа от OpenRouter."})

    except Exception as e:
        return jsonify({"success": False, "error": f"Ошибка сервера: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
