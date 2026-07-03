import { Info } from "lucide-react";

export function SafetyDisclaimer() {
  return (
    <div className="mt-8 p-4 rounded-lg bg-amber-50 border border-amber-200">
      <p className="text-sm text-amber-800 flex items-start gap-2">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          Đây là công cụ tra cứu tham khảo dựa trên AI, không thay thế tư vấn
          pháp lý chuyên nghiệp. Phạm vi dữ liệu hiện tại: Luật Nhà ở 2023 và
          Nghị định 95/2024/NĐ-CP.
        </span>
      </p>
    </div>
  );
}
