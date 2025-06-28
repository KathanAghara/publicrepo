from odoo import models, api
import requests
import json


class AddressScorer(models.AbstractModel):
    _name = 'address.scorer'
    _description = 'Address Field Scorer'

    def score_field(self, field_value, api_key):
        """Score address field using AI"""
        if not field_value:
            return {'score': 0.0, 'reason': 'No address provided'}

        prompt = f"""
        Analyze this business address for lead quality and score out of 100:
        Address: {field_value}

        Consider:
        - Business district indicators
        - Professional location
        - Geographic advantages
        - Address completeness

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