"use client";

import { useEffect, useState } from "react";

interface DomainFilterProps {
  value: string | null;
  onChange: (domain: string | null) => void;
}

/**
 * Bộ lọc lĩnh vực. Danh sách lấy động từ /api/domains → tự mở rộng khi thêm lĩnh vực
 * mới (không sửa UI). "Tất cả" (null) = không lọc.
 */
export function DomainFilter({ value, onChange }: DomainFilterProps) {
  // null = đang tải (giữ chỗ để tránh layout shift); [] = không có lĩnh vực.
  const [domains, setDomains] = useState<string[] | null>(null);

  useEffect(() => {
    fetch("/api/domains")
      .then((r) => r.json())
      .then((d: { domains?: string[] }) => setDomains(d.domains ?? []))
      .catch(() => setDomains([]));
  }, []);

  // Đã tải xong mà rỗng → không hiển thị.
  if (domains !== null && domains.length === 0) return null;

  // Giữ chiều cao tối thiểu để không đẩy nội dung dưới khi chip xuất hiện (CLS).
  if (domains === null) {
    return (
      <div className="mt-4 flex min-h-[34px] justify-center" aria-hidden>
        <div className="h-[30px] w-40 animate-pulse rounded-full bg-slate-100" />
      </div>
    );
  }

  const options: { label: string; val: string | null }[] = [
    { label: "Tất cả", val: null },
    ...domains.map((d) => ({ label: d, val: d })),
  ];

  return (
    <div
      className="mt-4 flex min-h-[34px] flex-wrap justify-center gap-2"
      role="group"
      aria-label="Lọc theo lĩnh vực"
    >
      {options.map((o) => {
        const active = value === o.val;
        return (
          <button
            key={o.label}
            type="button"
            onClick={() => onChange(o.val)}
            aria-pressed={active}
            className={`rounded-full border px-3 py-1 text-sm transition-colors ${
              active
                ? "border-primary bg-primary text-white"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
