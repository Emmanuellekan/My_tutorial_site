document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('#enable-push-notifications');
  const status = document.querySelector('#push-opt-in-status');
  if (!button || !status) return;

  button.addEventListener('click', () => {
    button.disabled = true;
    window.OneSignalDeferred = window.OneSignalDeferred || [];
    OneSignalDeferred.push(async OneSignal => {
      try {
        await OneSignal.Notifications.requestPermission();
        if (Notification.permission !== 'granted') {
          status.textContent = 'Browser notifications were not enabled. You can still read updates here or receive them by email.';
          return;
        }
        await OneSignal.User.PushSubscription.optIn();
        status.textContent = 'Notifications are enabled on this device.';
      } catch (error) {
        status.textContent = 'Could not enable notifications. Please try again later.';
      } finally {
        button.disabled = false;
      }
    });
  });
});