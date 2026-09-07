// Service worker: recebe as notificações push mesmo com o site fechado.
self.addEventListener("push", function (event) {
  let data = { title: "NutriApp", body: "", url: "/" };
  try {
    if (event.data) data = event.data.json();
  } catch (e) {
    /* ignora */
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "NutriApp", {
      body: data.body || "",
      icon: "/static/icon-192.png",
      badge: "/static/icon-192.png",
      data: { url: data.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(clients.openWindow(url));
});
