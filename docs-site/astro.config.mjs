// kunji documentation — https://testwithsuraj.github.io/kunji/docs/
// Build: python scripts/gen_docs.py && npm run build   (see docs-site/README.md)
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightLinksValidator from "starlight-links-validator";

const SITE = "https://testwithsuraj.github.io";
const BASE = "/kunji/docs";
const OG_IMAGE = `${SITE}/kunji/og.png`;

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: "always",
  telemetry: false,
  integrations: [
    starlight({
      title: "kunji docs",
      description:
        "Documentation for kunji, the free open-source terminal app for chatting with any AI model using your own API keys.",
      logo: { src: "./src/assets/logo.svg", alt: "kunji" },
      favicon: "/favicon.svg",
      social: [
        { icon: "github", label: "GitHub", href: "https://github.com/testwithsuraj/kunji" },
      ],
      editLink: { baseUrl: "https://github.com/testwithsuraj/kunji/edit/main/docs-site/" },
      lastUpdated: true,
      credits: false,
      customCss: [
        "@fontsource/ibm-plex-sans/400.css",
        "@fontsource/ibm-plex-sans/500.css",
        "@fontsource/ibm-plex-sans/600.css",
        "@fontsource/ibm-plex-mono/400.css",
        "@fontsource/ibm-plex-mono/500.css",
        "@fontsource/martian-mono/500.css",
        "@fontsource/martian-mono/700.css",
        "./src/styles/kunji.css",
      ],
      head: [
        { tag: "meta", attrs: { property: "og:image", content: OG_IMAGE } },
        { tag: "meta", attrs: { property: "og:image:width", content: "1200" } },
        { tag: "meta", attrs: { property: "og:image:height", content: "630" } },
        { tag: "meta", attrs: { name: "twitter:image", content: OG_IMAGE } },
        { tag: "meta", attrs: { name: "theme-color", content: "#14201A" } },
      ],
      plugins: [starlightLinksValidator({ errorOnLocalLinks: false })],
      sidebar: [
        {
          label: "Start here",
          items: [
            { label: "Introduction", slug: "introduction" },
            { label: "Install", slug: "getting-started/installation" },
            { label: "Quick start", slug: "getting-started/quickstart" },
            { label: "The menu", slug: "getting-started/menu" },
          ],
        },
        {
          label: "Guides",
          items: [
            { label: "Chatting", slug: "guides/chatting" },
            { label: "Switch and pick models", slug: "guides/models" },
            { label: "Saved prompts", slug: "guides/saved-prompts" },
            { label: "Chat history", slug: "guides/chat-history" },
            { label: "Attach files", slug: "guides/attach-files" },
            { label: "Compare models", slug: "guides/compare-models" },
            { label: "Costs and budgets", slug: "guides/costs-and-budgets" },
            { label: "Pipes and scripts", slug: "guides/pipes-and-scripts" },
            { label: "Free local models (Ollama)", slug: "guides/local-models-ollama" },
            { label: "Custom servers", slug: "guides/custom-servers" },
            { label: "Fallback models", slug: "guides/fallback" },
            { label: "Upgrade kunji", slug: "guides/upgrading" },
          ],
        },
        {
          label: "Providers",
          collapsed: true,
          items: [{ autogenerate: { directory: "providers" } }],
        },
        {
          label: "Reference",
          items: [
            {
              label: "Commands",
              collapsed: true,
              items: [{ autogenerate: { directory: "reference/cli" } }],
            },
            { label: "Chat commands", slug: "reference/chat-commands" },
            { label: "Configuration", slug: "reference/configuration" },
            { label: "Environment variables", slug: "reference/environment-variables" },
            { label: "Files and folders", slug: "reference/files" },
          ],
        },
        {
          label: "How it works",
          items: [
            { label: "Privacy and security", slug: "concepts/privacy-and-security" },
            { label: "How costs are calculated", slug: "concepts/costs" },
          ],
        },
        {
          label: "Help",
          items: [
            { label: "Troubleshooting", slug: "help/troubleshooting" },
            { label: "FAQ", slug: "help/faq" },
            { label: "Changelog", slug: "releases/changelog" },
            { label: "Contributing", slug: "help/contributing" },
          ],
        },
      ],
    }),
  ],
});
