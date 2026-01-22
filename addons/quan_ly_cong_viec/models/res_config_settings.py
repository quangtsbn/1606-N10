from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quan_ly_cong_viec_ai_api_key = fields.Char(
        string='AI API Key',
        config_parameter='quan_ly_cong_viec.ai_api_key',
        help='API Key cho Google Gemini để sử dụng tính năng phân tích công việc.'
    )
    
    quan_ly_cong_viec_ai_model = fields.Selection([
        ('gemini-2.5-flash', 'Gemini 2.5 Flash (Khuyên dùng)'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro (Mạnh mẽ)'),
        ('gemini-2.0-flash', 'Gemini 2.0 Flash'),
        ('gemini-3-pro-preview', 'Gemini 3.0 Pro Preview'),
        ('gemini-3-flash-preview', 'Gemini 3.0 Flash Preview'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
    ], string='AI Model', config_parameter='quan_ly_cong_viec.ai_model', default='gemini-2.5-flash')
