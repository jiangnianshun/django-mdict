var CACHE_NAME = 'django-mdict-caches'

var urls_to_cache = [
    "/",
    "/simple/",
    "/getindexsites/",
    "/mynav/",
    "/mynav/getsite/",
    "/mdict/shelf/",
    "/mdict/shelf2/",
    "/mdict/bujian/",
    "/mdict/getdicgroup/",
    "/mdict/getmdictlist/",
    "/mdict/retrieveconfig/",
    "/mdict/es/",
    "/api/mdictonline/",
    "/mdict/doc/",
    "/mdict/doc/readme.md",
    "/mdict/doc/doc/doc_func.md",
    "/mdict/doc/doc/doc_op.md",
    "/mdict/doc/doc/doc_index.md",
    "/mdict/doc/doc/doc_deploy.md",
    "/mdict/doc/doc/doc_update.md",
    "/mdict/doc/doc/doc_style.md",
    "/mdict/doc/doc/doc_question.md",
    "/static/bootstrap/css/bootstrap.min.css",
    "/static/bootstrap/font/bootstrap-icons.css",
    "/static/bootstrap/js/bootstrap.bundle.min.js",
    "/static/bootstrap/font/fonts/bootstrap-icons.woff2?08efbba7c53d8c5413793eecb19b20bb",
    "/static/jquery/jquery.min.js",
    "/static/jquery-ui/jquery-ui.min.js",
    "/static/img/background.jpg",
    "/static/mynav/css/mynav.css",
    "/static/mynav/js/mynav.js",
    "/static/mdict/js/base_func.js",
    "/static/mdict/transform/transform.js",
    "/static/mdict/iframe-resizer/js/iframeResizer.min.js",
    "/static/mdict/ckeditor5/ckeditor.js",
    "/static/mdict/js/mdict_base.js",
    "/static/mdict/js/mdict.js",
    "/static/mdict/mark/mark.min.js",
    "/static/mdict/img/book.png",
    "/static/mdict/img/book152.png"
]

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(function(cache){
        return cache.addAll(urls_to_cache);
    }))
});

self.addEventListener('activate', event => {
    var cacheWhitelist=[CACHE_NAME];
    event.waitUntil(caches.keys().then(cacheNames=>{
        return Promise.all(cacheNames.map(cacheName=>{
            if(cacheWhitelist.indexOf(cacheName)===-1){
                return caches.delete(cacheName);
            }
        }))
    }))
});

self.addEventListener('fetch', event => {
    if(!event.request.url.startsWith('http')){
        return;
    }
    let requestURL=new URL(event.request.url);
    if(requestURL.pathname.endsWith('.ttf')){
        //全宋体优先缓存，然后网络
        event.respondWith(caches.match(event.request).then(function (cache) {
            if(cache){
                return cache;
            }else{
                return fetch(event.request).then(function(res){
                    return caches.open(CACHE_NAME).then(function(cache){
                        if(res){
                            cache.put(event.request, res.clone());
                        }
                        return res;
                    })
                });
            }
        }).catch(function(err){
            return fetch(event.request).then(function(res){
                return caches.open(CACHE_NAME).then(function(cache){
                    if(res){
                        cache.put(event.request, res.clone());
                    }
                    return res;
                })
            });
        }));
    }else if(!requestURL.pathname.startsWith('/admin/')&&requestURL.pathname!='/mdict/'){
        //admin不缓存
        //mdict缓存会导致csrf token被缓存
        //Stale-while-revalidate
        event.respondWith(
            caches.open(CACHE_NAME).then(function(cache) {
                return cache.match(event.request).then(function(cacheResponse) {
                        var fetchPromise = fetch(event.request).then(function(networkResponse) {
                                if(networkResponse){
                                    cache.put(event.request, networkResponse.clone())
                                }
                                return networkResponse
                            })
                         return cacheResponse || fetchPromise;
                    })
                })
        )
    }
})