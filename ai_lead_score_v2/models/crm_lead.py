from odoo import models, fields, api
import json
from odoo.exceptions import UserError
import threading
import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ai_score = fields.Float(string='AI Score', default=0.0)
    ai_score_category = fields.Selection([
        ('hot', 'Hot (80-100)'),
        ('warm', 'Warm (50-79)'),
        ('cold', 'Cold (1-49)'),
        ('not_scored', 'Not Scored')
    ], string='Score Category', default='not_scored')
    ai_scoring_details = fields.One2many('ai.scoring.detail', 'lead_id', string='AI Scoring Details')
    ai_last_scored = fields.Datetime(string='Last Scored')
    ai_score_reason = fields.Text(string='AI Score Reason')

    def action_ai_score_lead(self):
        """Single lead AI scoring action"""
        self.ensure_one()
        config = self.env['ai.scoring.config'].get_config()
        if not config.groq_api_key:
            raise UserError("Please configure Groq API key in CRM Configuration")

        self._calculate_ai_score()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Lead scored: {self.ai_score}/100 ({self.ai_score_category})',
                'type': 'success',
            }
        }

    def _calculate_ai_score(self):
        """Calculate AI score for lead"""
        config = self.env['ai.scoring.config'].get_config()
        total_score = 0.0
        scoring_details = []

        # Clear previous scoring details
        self.ai_scoring_details.unlink()

        # Score each enabled field
        field_scorers = {
            'name': self.env['name.scorer'],
            'partner_id': self.env['customer.scorer'],
            'street': self.env['address.scorer'],
            'website': self.env['website.scorer'],
            'email_from': self.env['email.scorer'],
            'function': self.env['job.position.scorer'],
            'phone': self.env['phone.scorer'],
            'mobile': self.env['mobile.scorer'],
            'description': self.env['internal.notes.scorer'],
        }

        for field_name, scorer in field_scorers.items():
            if getattr(config, 'enable_description_scoring', False) and self.description:
                clean_desc = self._get_clean_description()
                if clean_desc:
                    score_data = self.env['internal.notes.scorer'].score_field(clean_desc, config.groq_api_key)

            if getattr(config, f'enable_{field_name}_scoring', False):
                field_value = getattr(self, field_name, '')
                if field_value:
                    score_data = scorer.score_field(field_value, config.groq_api_key)
                    total_score += score_data['score']

                    # Create scoring detail record
                    self.env['ai.scoring.detail'].create({
                        'lead_id': self.id,
                        'field_name': field_name,
                        'field_value': str(field_value)[:500],  # Limit length
                        'score': score_data['score'],
                        'reason': score_data['reason'],
                    })

        # Normalize score to 100
        enabled_fields_count = sum(1 for field in field_scorers.keys()
                                   if getattr(config, f'enable_{field}_scoring', False))

        if enabled_fields_count > 0:
            normalized_score = min(100.0, total_score / enabled_fields_count)
        else:
            normalized_score = 0.0

        # Update lead
        self.write({
            'ai_score': normalized_score,
            'ai_score_category': self._get_score_category(normalized_score),
            'ai_last_scored': fields.Datetime.now(),
            'ai_score_reason': self._generate_overall_reason(),
        })

    def _get_score_category(self, score):
        """Get score category based on score value"""
        if score >= 80:
            return 'hot'
        elif score >= 50:
            return 'warm'
        elif score > 0:
            return 'cold'
        else:
            return 'not_scored'

    # AI scoring details ko single field me combine karne ke liye
    def _generate_overall_reason(self):
        """Generate comprehensive scoring reason with field-wise breakdown"""
        if not self.ai_scoring_details:
            return "No scoring details available"

        reason_parts = []
        reason_parts.append("=== AI LEAD SCORING ANALYSIS ===\n")

        for detail in self.ai_scoring_details.sorted('score', reverse=True):
            field_display = {
                'name': 'Lead Name',
                'partner_id': 'Customer/Company',
                'street': 'Address',
                'website': 'Website',
                'email_from': 'Email',
                'function': 'Job Position',
                'phone': 'Phone',
                'mobile': 'Mobile',
                'description': 'Internal Notes'
            }.get(detail.field_name, detail.field_name.replace('_', ' ').title())

            reason_parts.append(f"📊 {field_display} (Score: {detail.score}/100)")
            reason_parts.append(f"   {detail.reason}\n")

        # Overall assessment
        if self.ai_score >= 80:
            reason_parts.append("🔥 VERDICT: HOT LEAD - High potential, immediate follow-up recommended!")
        elif self.ai_score >= 50:
            reason_parts.append("⚡ VERDICT: WARM LEAD - Good potential, schedule follow-up within 2-3 days")
        elif self.ai_score > 0:
            reason_parts.append("❄️ VERDICT: COLD LEAD - Low potential, nurture campaign recommended")

        return "\n".join(reason_parts)

    # Description field se HTML strip karne ke liye
    def _get_clean_description(self):
        """Clean HTML from description field"""
        if not self.description:
            return ""

        # Remove HTML tags
        import re
        clean_text = re.sub('<[^<]+?>', '', str(self.description))
        # Remove extra whitespaces
        clean_text = ' '.join(clean_text.split())
        return clean_text

    def action_view_scoring_details(self):
        """Open scoring details view"""
        return {
            'name': 'AI Scoring Details',
            'type': 'ir.actions.act_window',
            'res_model': 'ai.scoring.detail',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }

    import threading

    @api.model
    def create(self, vals):
        """Auto-score new leads if enabled"""
        lead = super().create(vals)
        config = self.env['ai.scoring.config'].get_config()
        if config.auto_score_new_leads:
            try:
                # Background thread mein run karo
                thread = threading.Thread(target=self._score_in_background, args=(lead.id,))
                thread.daemon = True
                thread.start()
            except:
                pass
        return lead

    def _score_in_background(self, lead_id):
        """Background scoring method"""
        try:
            # New environment banao thread ke liye
            with self.env.registry.cursor() as cr:
                env = self.env(cr=cr)
                lead = env['crm.lead'].browse(lead_id)
                if lead.exists():
                    lead._calculate_ai_score()
                    env.cr.commit()
        except Exception as e:
            _logger.error(f"Background scoring failed: {e}")

    # # Score validation
    # def _validate_score_data(self, score_data):
    #     """Validate and sanitize AI response"""
    #     try:
    #         score = float(score_data.get('score', 0))
    #         score = max(0, min(100, score))  # Clamp between 0-100
    #         reason = str(score_data.get('reason', 'No analysis provided'))[:1000]
    #         return {'score': score, 'reason': reason}
    #     except:
    #         return {'score': 0, 'reason': 'Invalid AI response'}