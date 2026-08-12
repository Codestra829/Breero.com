import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const config = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  { ignores: [".next/**", "next-env.d.ts", "test-results/**", "playwright-report/**"] },
  { files: ["app/account/**/*.tsx", "components/account/**/*.tsx"], rules: { "@next/next/no-html-link-for-pages": "off" } },
];
export default config;
