import requests
import json
from odoo import models, fields, api
from odoo.exceptions import UserError

class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Công Việc Dự Án'
    _rec_name = 'ten_cong_viec'

    ten_cong_viec = fields.Char(string='Tên Công Việc', required=True)
    mo_ta = fields.Text(string='Mô Tả')
    du_an_id = fields.Many2one('du_an', string='Dự Án', required=True, ondelete='cascade')

    nhan_vien_ids = fields.Many2many('nhan_vien', 'cong_viec_nhan_vien_rel', 'cong_viec_id', 'nhan_vien_id', string='Nhân Viên Tham Gia')

    han_chot = fields.Datetime(string='Hạn Chót')
    deadline = fields.Date(string='Hạn Hoàn Thành')
    uu_tien = fields.Selection([
        ('high', 'Cao'),
        ('medium', 'Trung bình'),
        ('low', 'Thấp')
    ], default='medium', string='Ưu Tiên')
    
    do_kho = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao')
    ], default='trung_binh', string='Độ Khó')

    thoi_gian_du_kien = fields.Float('Thời Gian Dự Kiến (giờ)')
    giai_doan_id = fields.Many2one('giai_doan_cong_viec', string='Giai Đoạn')

    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'cong_viec_id', string='Nhật Ký Công Việc')

    thoi_gian_con_lai = fields.Char(string="Thời Gian Còn Lại", compute="_compute_thoi_gian_con_lai", store=True)
    
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'cong_viec_id', string='Đánh Giá Nhân Viên')
    
    nhan_vien_display = fields.Char(string="Nhân Viên Tham Gia (Tên + Mã Định Danh)", compute="_compute_nhan_vien_display")

    phan_tram_cong_viec = fields.Float(
        string="Phần Trăm Hoàn Thành", 
        compute="_compute_phan_tram_cong_viec", 
        store=True
    )

    ly_do_ai = fields.Text(string="Đánh giá của AI")

    @api.depends('nhat_ky_cong_viec_ids.muc_do')
    def _compute_phan_tram_cong_viec(self):
        for record in self:
            if record.nhat_ky_cong_viec_ids:
                total_progress = sum(record.nhat_ky_cong_viec_ids.mapped('muc_do'))
                record.phan_tram_cong_viec = total_progress / len(record.nhat_ky_cong_viec_ids)
            else:
                record.phan_tram_cong_viec = 0.0

    @api.depends('nhan_vien_ids')
    def _compute_nhan_vien_display(self):
        for record in self:
            record.nhan_vien_display = ', '.join(record.nhan_vien_ids.mapped('display_name'))

    @api.depends('deadline')
    def _compute_thoi_gian_con_lai(self):
        for record in self:
            if record.deadline:
                delta = record.deadline - fields.Date.today()
                if delta.days < 0:
                    record.thoi_gian_con_lai = f"Quá hạn {abs(delta.days)} ngày"
                else:
                    record.thoi_gian_con_lai = f"Còn {delta.days} ngày"
            else:
                record.thoi_gian_con_lai = "Chưa có deadline"

    def action_ai_analyze_task(self):
        """Phân tích công việc bằng AI (Gemini)"""
        self.ensure_one()
        # Lấy API Key từ System Parameters hoặc fallback
        api_key = self.env['ir.config_parameter'].sudo().get_param('quan_ly_cong_viec.ai_api_key', 'AIzaSyApK0XofIg7V7zJgfdBpqYywA0RyJ8AONU')
        
        if not api_key:
             raise UserError("Vui lòng cấu hình API Key trong System Parameters (quan_ly_cong_viec.ai_api_key).")

        # Lấy model từ cấu hình (fallback mặc định mới là 2.5 flash)
        config_model = self.env['ir.config_parameter'].sudo().get_param('quan_ly_cong_viec.ai_model', 'gemini-2.5-flash')
        
        # Danh sách model để thử: [Model cấu hình, 2.5 Flash, 2.0 Flash, 3.0 Preview]
        models_to_try = []
        if config_model:
            models_to_try.append(config_model)
            
        candidates = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-3-flash-preview', 'gemini-1.5-flash']
        for cand in candidates:
            if cand not in models_to_try:
                models_to_try.append(cand)
            
        final_error = None

        prompt = f"""
        Bạn là một trợ lý quản lý dự án AI. Hãy phân tích công việc sau đây và trả về định dạng JSON (chỉ JSON, không markdowns).
        
        Thông tin công việc:
        - Tên: {self.ten_cong_viec}
        - Mô tả: {self.mo_ta or 'Không có'}
        - Thời gian dự kiến: {self.thoi_gian_du_kien} giờ
        - Deadline: {self.deadline or 'Chưa có'}
        - Số lượng nhân viên: {len(self.nhan_vien_ids)}
        
        Yêu cầu phân tích:
        1. "do_tre": Dự đoán khả năng trễ hạn (boolean). Dựa trên độ phức tạp và thời gian.
        2. "uu_tien": Đề xuất mức ưu tiên ("high", "medium", "low").
        3. "do_kho": Đánh giá độ khó ("thap", "trung_binh", "cao").
        4. "ly_do": Giải thích ngắn gọn bằng tiếng Việt tại sao bạn đánh giá như vậy (dưới 50 từ).

        JSON Output schema:
        {{
            "do_tre": boolean,
            "uu_tien": "string",
            "do_kho": "string",
            "ly_do": "string"
        }}
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        headers = {'Content-Type': 'application/json'}

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Thành công!
                    result = response.json()
                    text_content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
                    text_content = text_content.replace('```json', '').replace('```', '').strip()
                    ai_data = json.loads(text_content)
                    
                    vals = {
                        'ly_do_ai': ai_data.get('ly_do', ''),
                        'uu_tien': ai_data.get('uu_tien', 'medium'),
                        'do_kho': ai_data.get('do_kho', 'trung_binh')
                    }
                    
                    if ai_data.get('do_tre'):
                        vals['ly_do_ai'] += " [CẢNH BÁO: CÓ NGUY CƠ TRỄ HẠN]"
                    
                    # Nếu đang dùng fallback, note lại vào lý do
                    if model_name != config_model:
                        vals['ly_do_ai'] += f"\n(Lưu ý: Model {config_model} lỗi, đã tự động chuyển sang {model_name})"

                    self.write(vals)
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Hoàn thành',
                            'message': f'Đã phân tích xong bằng {model_name}!',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    # Lưu lỗi để raise nếu tất cả đều fail
                    final_error = response.json().get('error', {}).get('message', str(response.status_code))
                    continue # Thử model tiếp theo
                    
            except Exception as e:
                final_error = str(e)
                continue

        # Nếu chạy hết vòng lặp mà không return -> Lỗi toàn bộ
        # Thử gọi API list models để xem key này có quyền truy cập model nào không
        available_models = []
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            list_response = requests.get(list_url, timeout=10)
            if list_response.status_code == 200:
                data = list_response.json()
                for m in data.get('models', []):
                    # Chỉ lấy model hỗ trợ generateContent
                    if 'generateContent' in m.get('supportedGenerationMethods', []):
                        # Tên trả về có dạng models/gemini-pro -> lấy phần sau dấu /
                        m_name = m.get('name', '').replace('models/', '')
                        available_models.append(m_name)
        except Exception:
            pass

        debug_msg = f"Không thể gọi AI. Lỗi cuối cùng: {final_error}\n"
        if available_models:
            debug_msg += f"KIỂM TRA THÀNH CÔNG: Key của bạn hợp lệ và thấy các model sau: {', '.join(available_models)}.\n"
            debug_msg += "Vui lòng chọn đúng một trong các model trên trong phần Cài Đặt."
        else:
            debug_msg += "KIỂM TRA THẤT BẠI: Không tìm thấy model nào. Khả năng cao API Key không đúng hoặc chưa kích hoạt dịch vụ Generative Language API."

        raise UserError(debug_msg)

