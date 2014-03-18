
var loader = function(url, type, charset, cb, timeout, timeoutCallBack) {
    if (!url) {
        return;
    }

    if (typeof type === 'function') {
      cb = type;
      type = '';
    }

    if (typeof charset === 'function') {
      cb = charset;
      charset = '';
    }

    var done = function() {
      loader.loaded[url] = 1;
      cb && cb(url);
      cb = null;
      clearTimeout(wait);
    };


    if (loader.loaded[url]) {
      if (loader.loading[url]) {
        // 等待结束，已经触发过done
        loader.loading[url] = 0;
      } else {
        cb && cb(url);
      }
      return;
    }

    if (loader.loading[url]) {
      setTimeout(function() {
        loader(url, type, charset, cb, timeout, timeoutCallBack);
      }, 10);
      return;
    }

    loader.loading[url] = 1;

    var wait = setTimeout(function() {
      if (timeoutCallback) {
        try {
          timeoutCallback(url); 
        } catch(ex) {}
      }
    }, timeout || 6000);

    var t = type || url.toLowerCase().split(/\./).pop().replace(/[\?#].*/, '');
    var n;

    if (t === 'js') {
      n = document.createElement('script');
      n.setAttribute('type', 'text/javascript');
      n.setAttribute('src', url);
      n.setAttribute('async', true);
    } else if (t === 'css') {
      n = document.createElement('link');
      n.setAttribute('type', 'text/css');
      n.setAttribute('rel', 'stylesheet');
      n.setAttribute('href', url);
    }

    if (charset) {
      n.charset = charset;
    }

    if (t === 'css') {
      setTimeout(function(){
        done();
      },0);
    } else {
      n.onerror = function() {
        done();
        n.onerror = null;
      };

      n.onload = n.onreadystatechange = function() {
        var url;
        if (!this.readyState ||
            this.readyState === 'loaded' ||
            this.readyState === 'complete') {
          setTimeout(function(){
            done();
          },0);
          n.onload = n.onreadystatechange = null;
        }
      };
    }

    var anchorFile = (function() { 
      var files = document.getElementsByTagName('script'); 
      return files[files.length - 1];
    })();

    anchorFile.parentNode.insertBefore(n, anchorFile);
};

loader.loaded = {};

loader.loading = {};

loader.batch = function(urls) {
  if (!urls) {
    return;
  }
  var defer = deferred();
  var queue = [];
  var oneloaded = function() {
    queue.pop();
    if (queue.length === 0) {
      defer.resolve();
    }
  };
  for (var i = 0, url; url = urls[i++];) {
    queue.push(url);
    loader(url, oneloaded);
  }
  return defer.promise;
};
