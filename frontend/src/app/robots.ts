import type { MetadataRoute } from "next";

/** Keep the public landing page discoverable, but out of search indexes the console. */
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/dashboard", "/history", "/incidents", "/backend"],
      },
    ],
  };
}
