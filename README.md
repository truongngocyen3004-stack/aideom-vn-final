# AIDEOM-VN — Bài 12

Đồ án tích hợp hỗ trợ ra quyết định phát triển kinh tế Việt Nam trong kỷ nguyên AI.

## Cấu trúc

```text
AIDEOM_VN_Bai12/
├── app.py
├── requirements.txt
├── README.md
├── modules/
│   ├── scenarios.py
│   ├── m1_forecast.py
│   ├── m2_readiness.py
│   ├── m3_allocation.py
│   ├── m4_labor.py
│   └── m5_risk.py
└── tests/
    └── test_modules.py
```

## Sáu module

- M1: Dự báo kinh tế đến 2030.
- M2: Đánh giá sẵn sàng số của sáu vùng.
- M3: Phân bổ ngân sách vùng × hạng mục.
- M4: Mô phỏng việc làm và đào tạo lại.
- M5: Đánh giá rủi ro.
- M6: Dashboard Streamlit.

## Cài đặt

```bash
python -m pip install -r requirements.txt
```

## Chạy kiểm thử

```bash
pytest -q
```

## Chạy dashboard

```bash
streamlit run app.py
```

## Năm kịch bản

- S1: Truyền thống.
- S2: Số hóa nhanh.
- S3: AI dẫn dắt.
- S4: Bao trùm số.
- S5: Tối ưu cân bằng.

## Lưu ý phương pháp

Đây là mô hình mô phỏng phục vụ học tập. Kết quả phụ thuộc vào hệ số và giả định trong mã nguồn, không phải dự báo chính thức.
