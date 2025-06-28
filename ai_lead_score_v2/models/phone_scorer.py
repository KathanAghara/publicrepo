from odoo import models, api
import requests
import json


class PhoneScorer(models.AbstractModel):
    _name = 'phone.scorer'
    _description = 'Phone Field Scorer'

    def score_field(self, field_value, api_key):
        """Score phone field using AI"""
        if not field_value:
            return {'score': 0.0, 'reason': 'No phone number provided'}

        prompt = f"""
        Analyze this phone number for business credibility and score out of 100:
        Phone: {field_value}

        Consider:
        - Number format professionalism
        - Business line indicators
        - Geographic relevance
        - Contact availability

        Respond in JSON format:
        {{"score": <number>, "reason": "<explanation>"}}
        """

        return self._call_groq_api(prompt, api_key)

    def _call_groq_api(self, prompt, api_key):
        """Call Groq API"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1000
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            try:
                parsed = json.loads(content)
                return {
                    'score': float(parsed.get('score', 0)),
                    'reason': parsed.get('reason', 'No reason provided')
                }
            except:
                return {'score': 50.0, 'reason': 'Unable to parse AI response'}

        except Exception as e:
            return {'score': 0.0, 'reason': f'API Error: {str(e)}'}