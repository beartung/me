/* Modernizr 2.0.6 (Custom Build) | MIT & BSD
 * Build: http://www.modernizr.com/download/#-draganddrop-hasevent
 */
;window.Modernizr=function(a,b,c){function x(a,b){return!!~(""+a).indexOf(b)}function w(a,b){return typeof a===b}function v(a,b){return u(prefixes.join(a+";")+(b||""))}function u(a){j.cssText=a}var d="2.0.6",e={},f=b.documentElement,g=b.head||b.getElementsByTagName("head")[0],h="modernizr",i=b.createElement(h),j=i.style,k,l=Object.prototype.toString,m={},n={},o={},p=[],q=function(){function d(d,e){e=e||b.createElement(a[d]||"div"),d="on"+d;var f=d in e;f||(e.setAttribute||(e=b.createElement("div")),e.setAttribute&&e.removeAttribute&&(e.setAttribute(d,""),f=w(e[d],"function"),w(e[d],c)||(e[d]=c),e.removeAttribute(d))),e=null;return f}var a={select:"input",change:"input",submit:"form",reset:"form",error:"img",load:"img",abort:"img"};return d}(),r,s={}.hasOwnProperty,t;!w(s,c)&&!w(s.call,c)?t=function(a,b){return s.call(a,b)}:t=function(a,b){return b in a&&w(a.constructor.prototype[b],c)},m.draganddrop=function(){return q("dragstart")&&q("drop")};for(var y in m)t(m,y)&&(r=y.toLowerCase(),e[r]=m[y](),p.push((e[r]?"":"no-")+r));u(""),i=k=null,e._version=d,e.hasEvent=q;return e}(this,this.document);
