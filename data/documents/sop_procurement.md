# SOP-PROC-01: Quy Trình Mua Hàng & Duyệt Đơn Hàng Doanh Nghiệp

## 1. Nguyên Tắc Kiểm Soát Kép (Maker-Checker)
- Tất cả các đơn hàng phát sinh từ hệ thống Copilot có giá trị vượt quá **$10,000 USD** bắt buộc phải chuyển trạng thái `PENDING_APPROVAL`.
- Nhân viên tạo đơn (`MAKER`) tuyệt đối không được tự duyệt đơn của mình.
- Kiểm soát viên (`CHECKER`) phải kiểm tra hạn ngạch tồn kho và xác thực mã PIN bảo mật `123456` trước khi phát lệnh ghi sổ cái ERPNext.

## 2. Tiêu Chuẩn Vật Tư Chuẩn Hóa
- **ALU-CNC-001**: Linh kiện nhôm đúc chuẩn hàng không, đơn giá $25.00/chiếc.
- **SCR-M4-02**: Ốc vít M4 thép không gỉ SUS304, đơn giá $0.15/chiếc.
