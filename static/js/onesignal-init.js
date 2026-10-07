const appId = document.querySelector('meta[name="onesignal-app-id"]')?.content;
const userId = document.querySelector('meta[name="onesignal-user-id"]')?.content;

if (appId) {
  window.OneSignalDeferred = window.OneSignalDeferred || [];
  OneSignalDeferred.push(async OneSignal => {
    await OneSignal.init({ appId });
    if (userId) {
      await OneSignal.login(userId);
    } else {
      await OneSignal.logout();
    }
  });
}