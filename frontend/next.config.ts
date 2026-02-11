import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://invoices.bluehawana.com/api",
  },
  /* config options here */
};

export default nextConfig;
