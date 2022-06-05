var CACHE_NAME = 'django-mdict-caches'
var urls_to_cache = [
    "/",
    "/mynav",
    "/mdict",
    "/mdict/shelf",
    "/mdict/shelf2",
    "/mdict/bujian"
]

var cache_first_url=[
    "/static",
    "/media",
    "/mdict/getexfile",
    "/mdict/doc"
]

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(function(cache){
        return cache.addAll(urls_to_cache);
    }))
});

self.addEventListener('activate', event => {
    var cacheWhitelist=['django-mdict-caches'];
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

    let cache_first=false;
    for(let i=0;i<urls_to_cache.length;i++){
        if(requestURL.pathname==urls_to_cache[i]||requestURL.pathname==urls_to_cache[i]+'/'){
            cache_first=true;
            break;
        }
    }
    if(!cache_first){
        for(let i=0;i<cache_first_url.length;i++){
            if(requestURL.pathname.startsWith(cache_first_url[i])){
                cache_first=true;
                break;
            }
        }
    }
    if(cache_first){
        //优先缓存，然后网络
        event.respondWith(caches.match(event.request).then(function (cache) {
                if(typeof(cache)!='undefined'){
                    return cache;
                }else{
                    return fetch(event.request).then(function(res){
                        return caches.open(CACHE_NAME).then(function(cache){
                            if(typeof(res)!='undefined'){
                                cache.put(event.request, res.clone());
                            }
                            return res;
                        })
                    });
                }

            }).catch(function(err){
                return fetch(event.request).then(function(res){
                        return caches.open(CACHE_NAME).then(function(cache){
                            if(typeof(res)!='undefined'){
                                cache.put(event.request, res.clone());
                            }
                            return res;
                        })
                    });
                }));
    }else{
        //优先网络，然后缓存
        event.respondWith(fetch(event.request).then(function(res){
            return caches.open(CACHE_NAME).then(function(cache){
                if(typeof(res)!='undefined'){
                    cache.put(event.request, res.clone());
                }
                return res;
            })
        }).catch(function(err){
            return caches.match(event.request);
        }));
    }
})