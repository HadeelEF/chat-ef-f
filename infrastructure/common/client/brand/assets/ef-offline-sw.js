/* EF AI Workspace (#105): loaded into the generated service worker via workbox `importScripts`
 * (patch 0011). A page navigation that fails because the device is offline gets the precached EF
 * offline page instead of the browser's error page. Every other request is left to Workbox. */
self.addEventListener('fetch', (event) => {
  if (event.request.mode !== 'navigate') {
    return;
  }
  event.respondWith(
    fetch(event.request).catch(async () => {
      const page = await caches.match('assets/ef-offline.html', { ignoreSearch: true });
      return page || Response.error();
    }),
  );
});
