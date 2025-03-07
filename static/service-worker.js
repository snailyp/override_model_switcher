const CACHE_NAME = 'model-switcher-cache-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/script.js',
  '/static/manifest.json',
  '/static/icons/icon.png',
  '/static/icons/icon.png'
];

// 安装 Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// 激活 Service Worker
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 拦截请求并提供缓存响应
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 如果找到缓存的响应，则返回缓存
        if (response) {
          return response;
        }
        
        // 否则，获取新的响应
        return fetch(event.request).then(
          response => {
            // 检查响应是否有效
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // 克隆响应，因为响应是流，只能使用一次
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                // 将响应添加到缓存
                cache.put(event.request, responseToCache);
              });
            
            return response;
          }
        );
      })
  );
});
