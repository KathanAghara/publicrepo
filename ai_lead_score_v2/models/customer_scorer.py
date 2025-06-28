from odoo import models, api
import requests
import json


class CustomerScorer(models.AbstractModel):
    _name = 'customer.scorer'
    _description = 'Customer Field Scorer'

    def score_field(self, partner_id, api_key):
        """Score customer field using AI"""
        if not partner_id:
            return {'score': 0.0, 'reason': 'No customer selected'}

        partner = self.env['res.partner'].browse(partner_id.id if hasattr(partner_id, 'id') else partner_id)

        customer_info = f"""
        Company: {partner.name or 'N/A'}
        Industry: {partner.industry_id.name if partner.industry_id else 'N/A'}
        Country: {partner.country_id.name if partner.country_id else 'N/A'}
        Is Company: {partner.is_company}
        """

        prompt = f"""
        Analyze this customer information for lead quality and score out of 100:
        {customer_info}

        Consider:
        - Company size indicators
        - Industry potential
        - Geographic factors
        - Business credibility

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