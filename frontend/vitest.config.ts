import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Unit test (Vitest) tách khỏi E2E (Playwright, *.spec.ts trong tests/e2e).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["tests/e2e/**", "node_modules/**", ".next/**"],
    coverage: {
      provider: "v8",
      include: ["lib/**", "hooks/**", "components/**"],
      // Loại: test files; supabase client (mock); auth/layout (Supabase/server —
      // phủ bởi E2E auth.spec.ts, không hợp unit).
      exclude: [
        "**/*.test.{ts,tsx}",
        "lib/supabase/**",
        "components/auth/**",
        "components/layout/**",
      ],
      reporter: ["text", "text-summary"],
      // Constitution III (NON-NEGOTIABLE): ≥80% — enforce để CI đỏ nếu tụt.
      thresholds: { statements: 80, lines: 80, functions: 80, branches: 80 },
    },
  },
});
