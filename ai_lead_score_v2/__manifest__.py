{
    'name': 'AI Lead Scoring V2',
    'version': '1.0.0',
    'category': 'CRM',
    'summary': 'AI-powered lead scoring using Groq LLaMA',
    'description': '''
        AI Lead Scoring Module
        - Score leads out of 100 using AI
        - Hot, Cold, Warm, Not Scored filters
        - Bulk scoring wizard
        - Configurable field-wise scoring
        - Groq LLaMA integration
    ''',
    'author': 'Your Company',
    'depends': ['base', 'crm'],
    'data': [
        'data/ai_scoring_data.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/ai_scoring_config_views.xml',
        'views/ai_scoring_detail_views.xml',
        'wizard/bulk_scoring_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}