
from odoo import models, fields, api
import numpy as np
from sklearn.linear_model import LinearRegression

class TaiNguyen(models.Model):
    _name = 'tai_nguyen'
    _description = 'Tài Nguyên Dự Án'

    ten_tai_nguyen = fields.Char(string='Tên Tài Nguyên', required=True)
    so_luong = fields.Integer(string='Số Lượng', required=True, default=1)
    du_an_id = fields.Many2one('du_an', string='Dự Án', ondelete='cascade')

    @api.model
    def suggest_resource_allocation(self, du_an_id, features):
        """
        Gợi ý phân bổ tài nguyên cho dự án dựa trên dữ liệu lịch sử (AI demo).
        features: dict, ví dụ {'so_nhan_vien': 5, 'so_cong_viec': 10, ...}
        """
        # Lấy dữ liệu lịch sử tài nguyên các dự án
        du_an_model = self.env['du_an']
        du_an_records = du_an_model.search([])
        X, y = [], []
        for du_an in du_an_records:
            so_nhan_vien = len(du_an.nhan_vien_ids)
            so_cong_viec = len(du_an.cong_viec_ids)
            so_tai_nguyen = sum(tn.so_luong for tn in du_an.tai_nguyen_ids)
            X.append([so_nhan_vien, so_cong_viec])
            y.append(so_tai_nguyen)
        if len(X) < 2:
            return 'Không đủ dữ liệu lịch sử để gợi ý.'
        model = LinearRegression()
        model.fit(np.array(X), np.array(y))
        input_features = np.array([[features.get('so_nhan_vien', 0), features.get('so_cong_viec', 0)]])
        prediction = model.predict(input_features)
        return max(int(prediction[0]), 1)
