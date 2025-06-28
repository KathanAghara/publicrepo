from odoo import models, fields

class AiScoringDetail(models.Model):
    _name = 'ai.scoring.detail'
    _description = 'AI Scoring Detail'
    _order = 'create_date desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    field_name = fields.Char(string='Field Name', required=True)
    field_value = fields.Text(string='Field Value')
    score = fields.Float(string='Score')
    reason = fields.Text(string='Scoring Reason')
    create_date = fields.Datetime(string='Scored Date', default=fields.Datetime.now)

    def score_field(self, field_value, api_key):
        """Enhanced scoring with better analysis"""
        prompt = f"""
        Analyze these lead notes and provide detailed business intelligence scoring:

        NOTES: {field_value}

        Evaluate based on:
        🎯 BUYING SIGNALS (40%):
        - Budget mentions, urgency indicators
        - Decision timeline, approval process
        - Pain points and solution needs

        📞 ENGAGEMENT QUALITY (30%):
        - Response quality, interest level  
        - Meeting requests, follow-up willingness
        - Question quality and depth

        💼 BUSINESS FIT (30%):
        - Company size and industry relevance
        - Use case alignment
        - Implementation readiness

        Provide actionable insights and specific recommendations.

        Respond in JSON format:
        {{"score": <0-100>, "reason": "<detailed_analysis_with_specific_observations>"}}
        """

        return self._call_groq_api(prompt, api_key)