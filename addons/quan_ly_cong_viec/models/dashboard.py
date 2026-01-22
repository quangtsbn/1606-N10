
from odoo import models, fields, api


class Dashboard(models.Model):
    _name = 'dashboard'
    _description = 'Thống Kê Tổng Quan'


    so_luong_nhan_vien = fields.Integer(string="Số lượng nhân viên", compute="_compute_tong_quan", store=False)
    so_luong_du_an = fields.Integer(string="Số lượng dự án", compute="_compute_tong_quan", store=False)
    so_luong_cong_viec = fields.Integer(string="Số lượng công việc", compute="_compute_tong_quan", store=False)
    phan_tram_hoan_thanh = fields.Float(string="Tiến độ trung bình dự án (%)", compute="_compute_tong_quan", store=False)
    so_luong_danh_gia = fields.Integer(string="Số lượng đánh giá", compute="_compute_tong_quan", store=False)

    du_an_hoan_thanh = fields.Integer(string="Dự án đã hoàn thành", compute="_compute_tong_quan", store=False)
    du_an_dang_thuc_hien = fields.Integer(string="Dự án đang thực hiện", compute="_compute_tong_quan", store=False)
    du_an_chua_bat_dau = fields.Integer(string="Dự án chưa bắt đầu", compute="_compute_tong_quan", store=False)
    du_an_tam_dung = fields.Integer(string="Dự án tạm dừng", compute="_compute_tong_quan", store=False)

    # Thống kê tài nguyên chi tiết
    tong_so_tai_nguyen = fields.Integer(string="Tổng số loại tài nguyên", compute="_compute_tong_quan", store=False)
    tong_so_luong_tai_nguyen = fields.Integer(string="Tổng số lượng tài nguyên", compute="_compute_tong_quan", store=False)


    @api.depends('so_luong_nhan_vien', 'so_luong_du_an', 'so_luong_cong_viec', 'du_an_hoan_thanh', 'du_an_dang_thuc_hien',
                 'du_an_chua_bat_dau','du_an_tam_dung')
    def _compute_tong_quan(self):
        for record in self:
            record.so_luong_nhan_vien = self.env['nhan_vien'].search_count([])
            record.so_luong_du_an = self.env['du_an'].search_count([])
            record.so_luong_cong_viec = self.env['cong_viec'].search_count([])
            record.so_luong_danh_gia = self.env['danh_gia_nhan_vien'].search_count([])

            du_an_records = self.env['du_an'].search([])
            record.du_an_hoan_thanh = sum(1 for d in du_an_records if d.tien_do_du_an == 'hoan_thanh')
            record.du_an_dang_thuc_hien = sum(1 for d in du_an_records if d.tien_do_du_an == 'dang_thuc_hien')
            record.du_an_chua_bat_dau = sum(1 for d in du_an_records if d.tien_do_du_an == 'chua_bat_dau')
            record.du_an_tam_dung = sum(1 for d in du_an_records if d.tien_do_du_an == 'tam_dung')

            # Thống kê tài nguyên chi tiết
            tai_nguyen_records = self.env['tai_nguyen'].search([])
            record.tong_so_tai_nguyen = len(tai_nguyen_records)
            record.tong_so_luong_tai_nguyen = sum(tn.so_luong for tn in tai_nguyen_records)
