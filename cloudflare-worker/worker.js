const REPO_RAW_BASE = "https://raw.githubusercontent.com/christopherseaman/shark-repellent/main";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Root: serve install.sh with shell-script content type
    if (path === "/" || path === "") {
      const upstream = await fetch(`${REPO_RAW_BASE}/install.sh`);
      if (!upstream.ok) {
        return new Response(`Upstream returned ${upstream.status}`, { status: 502 });
      }
      return new Response(upstream.body, {
        status: 200,
        headers: {
          "Content-Type": "text/x-shellscript; charset=utf-8",
          "Cache-Control": "no-cache",
        },
      });
    }

    // Any other path: 302 to raw.githubusercontent.com
    return Response.redirect(`${REPO_RAW_BASE}${path}`, 302);
  },
};
