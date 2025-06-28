from odoo import models, fields, api
from odoo.exceptions import UserError


class AiScoringConfig(models.Model):
    _name = 'ai.scoring.config'
    _description = 'AI Scoring Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', default='AI Scoring Config')
    groq_api_key = fields.Char(string='Groq API Key', required=True)

    # Field enabling options
    enable_name_scoring = fields.Boolean(string='Enable Name Scoring', default=True)
    enable_partner_id_scoring = fields.Boolean(string='Enable Customer Scoring', default=True)
    enable_street_scoring = fields.Boolean(string='Enable Address Scoring', default=True)
    enable_website_scoring = fields.Boolean(string='Enable Website Scoring', default=True)
    enable_email_from_scoring = fields.Boolean(string='Enable Email Scoring', default=True)
    enable_function_scoring = fields.Boolean(string='Enable Job Position Scoring', default=True)
    enable_phone_scoring = fields.Boolean(string='Enable Phone Scoring', default=True)
    enable_mobile_scoring = fields.Boolean(string='Enable Mobile Scoring', default=True)
    enable_description_scoring = fields.Boolean(string='Enable Internal Notes Scoring', default=True)

    # API Configuration
    api_timeout = fields.Integer(string='API Timeout (seconds)', default=30)
    max_retries = fields.Integer(string='Max Retries', default=3)

    @api.model
    def get_config(self):
        """Get or create configuration"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({'name': 'Default AI Scoring Config'})
        return config

    def test_api_connection(self):
        """Test Groq API connection"""
        if not self.groq_api_key:
            raise UserError("Please enter Groq API Key")

        try:
            # Test with a simple prompt
            test_scorer = self.env['name.scorer']
            result = test_scorer.score_field("Test Name", self.groq_api_key)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'API connection successful!',
                    'type': 'success',
                }
            }
        except Exception as e:
            raise UserError(f"API connection failed: {str(e)}")