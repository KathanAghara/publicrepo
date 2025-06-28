from odoo import models, fields, api
from odoo.exceptions import UserError


class BulkScoringWizard(models.TransientModel):
    _name = 'bulk.scoring.wizard'
    _description = 'Bulk Lead Scoring Wizard'

    lead_ids = fields.Many2many('crm.lead', string='Leads to Score')
    score_filter = fields.Selection([
        ('all', 'All Leads'),
        ('not_scored', 'Not Scored Only'),
        ('rescore', 'Re-score All')
    ], string='Scoring Filter', default='not_scored', required=True)

    progress = fields.Float(string='Progress', default=0.0)
    status = fields.Text(string='Status', default='Ready to start')

    @api.model
    def default_get(self, fields):
        """Set default leads from context"""
        res = super().default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['lead_ids'] = [(6, 0, active_ids)]
        return res

    def action_bulk_score(self):
        """Perform bulk scoring"""
        config = self.env['ai.scoring.config'].get_config()
        if not config.groq_api_key:
            raise UserError("Please configure Groq API key in CRM Configuration")

        # Get leads to score
        leads_to_score = self.lead_ids
        if self.score_filter == 'not_scored':
            leads_to_score = leads_to_score.filtered(lambda l: l.ai_score_category == 'not_scored')

        if not leads_to_score:
            raise UserError("No leads found to score with the selected filter")

        # Process leads
        total_leads = len(leads_to_score)
        processed = 0

        for lead in leads_to_score:
            try:
                lead._calculate_ai_score()
                processed += 1

                # Update progress
                progress = (processed / total_leads) * 100
                self.write({
                    'progress': progress,
                    'status': f'Processed {processed}/{total_leads} leads'
                })

                # Commit every 10 leads to show progress
                if processed % 10 == 0:
                    self.env.cr.commit()

            except Exception as e:
                # Log error but continue with other leads
                self.env['ir.logging'].sudo().create({
                    'name': 'AI Lead Scoring',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': f'Error scoring lead {lead.id}: {str(e)}',
                    'path': 'bulk_scoring_wizard',
                    'line': '1',
                    'func': 'action_bulk_score'
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Successfully scored {processed}/{total_leads} leads',
                'type': 'success',
            }
        }