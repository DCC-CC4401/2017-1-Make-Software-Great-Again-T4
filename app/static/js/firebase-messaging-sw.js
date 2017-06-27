importScripts('https://www.gstatic.com/firebasejs/3.9.0/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.9.0/firebase-messaging.js');
importScripts('https://www.gstatic.com/firebasejs/3.9.0/firebase.js');


firebase.initializeApp({
    'messagingSenderId': "746470197160"
});

const messaging = firebase.messaging();


messaging.setBackgroundMessageHandler(function (payload) {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);
    // Customize notification here
    const notificationTitle = 'Background Message Title';
    const notificationOptions = {
        body: 'Background Message body.',
        icon: '/static/img/Notificacion.png'
    };

    return self.registration.showNotification(notificationTitle,
        notificationOptions);
});
