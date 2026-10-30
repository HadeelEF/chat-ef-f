#!/bin/sh
# Builds the LibreChat web client for EF AI Workspace (ADR-0013). Runs in the `client` stage of
# infrastructure/railway/librechat.Dockerfile, in the pinned and already patched upstream checkout (current
# directory) after `npm ci`, with this directory at /efaiw. Output: client/dist, a drop-in replacement for
# /app/client/dist of the same release.
#   1. merges ar.json into the Arabic locale (merge-locale.mjs fails on stale keys, broken placeholders or <100%);
#   2. applies the EF brand (brand/, owner decision D-04, #7): logo and icons replace the upstream files of the same
#      name (the build fails if upstream renamed one), the fonts go next to Inter, brand.css is appended to style.css;
#   3. builds exactly as upstream's `npm run frontend` does for the client (data-provider, client package, client), then
#      puts favicon.ico at the site root.
set -eu
node /efaiw/merge-locale.mjs client/src/locales /efaiw/ar.json

for f in logo.svg favicon-16x16.png favicon-32x32.png apple-touch-icon-180x180.png icon-192x192.png maskable-icon.png; do
  test -f "client/public/assets/$f" || { echo "efaiw: upstream asset client/public/assets/$f is gone; update brand/" >&2; exit 1; }
done
test -d client/public/fonts
cp /efaiw/brand/assets/* client/public/assets/
cp /efaiw/brand/fonts/* client/public/fonts/
cat /efaiw/brand/brand.css >> client/src/style.css
echo "efaiw: EF brand applied ($(ls /efaiw/brand/assets | wc -l) assets, $(ls /efaiw/brand/fonts | wc -l) fonts)"
npm run build:data-provider
npm run build:client-package
cd client
npm run build
# /favicon.ico at the site root, where browsers and bookmark tools ask for it (the production build copies only
# public/assets and robots.txt into dist/).
cp /efaiw/brand/favicon.ico dist/favicon.ico
test -s dist/index.html
