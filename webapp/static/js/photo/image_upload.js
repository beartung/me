function ImageUpload(opt) {
    var eid = opt && opt.eid,
        isBasic = opt && opt.isBasic,
        upload_photo_url = opt && opt.upload_photo_url,
        container = opt && opt.container;

    var IMAGE_ITEM_TMPL = $.template(null, $('#image_item_tmpl').html()),
        IMAGE_DLG_TMPL = $.template(null, $('#image_dlg_tmpl').html()),
        SLOT_TMPL = $.template(null, $('#image_slot').html()),
        SLOT_TMPL_LOADING = $.template(null, $('#image_slot_loading').html()),
        SLOT_TMPL_ERROR = $.template(null, $('#image_slot_error').html());

    var parseSize = function(size) {
        var suffix = ['B', 'KB', 'MB', 'GB'],
            tier = 0;
        while (size > 1024) {
            size = size / 1024;
            tier++;
        }

        return Math.round(size*10) / 10 + "" + suffix[tier];
    };

    // for comparison of array of objects
    var by = function(name) {
        return function(o, p) {
            var a, b;
            if (typeof o === 'object' &&
                typeof p === 'object' &&
                o &&
                p) {
                a = o[name];
                b = p[name];
                if (a === b) {
                    return 0;
                }
                if (typeof a === typeof b) {
                    return a < b ? -1 : 1;
                }
                return typeof a < typeof b ? -1 : 1;
            } else {
                throw {
                    name: 'Error',
                    message: 'Expected an object when sorting by ' + name
                };
            }
        };
    }


    /*
     * ## WIDGET
     * 1. imageTable 下面的图片列表
     * 2. uploadArea 上方的上传区域，根据浏览器初始化
     */
    var imageTable = function() {
        var slots, imageList, self, footer, image_num, total_size;

        var list =  [],
            picQueue = {},
            id = 0;

        return {
            init: function() {
                self = $('.upload-info');
                slots = $('#image-slots');
                imageList = $('.images');
                footer = $('.footer', document.getElementById('image_upload'));
                image_num = footer.find('.image-num');
                total_size = footer.find('.image-total-size');

                // event binding
                imageList.delegate('a.delete-image', 'click', function(e) {
                    e.preventDefault();
                    var item = $(this).parent('.image-item'),
                        PID = item.data('id');
                    $.post(this.href, {eid: eid, pid:PID}, function(e) {
                        if (e.r > 0) {
                            return;
                        }
                        item.remove();
                        if ($('.image-item').length == 0) {
                            $('.submit-item').hide();
                        }
                    });
                });
            },
            addSlot: function(name, size, ID) {
                if (list.length >= 20) {
                    footer.find('.total-num').find('.num-warning').show();
                    return undefined;
                }
                //每个文件有唯一的id，uploadify用它自己的，而其他则用累加器
                var ID = ID || id++;
                var isBasic = !size;
                var slot;
                if (isBasic) {
                    slot = $.tmpl(SLOT_TMPL_LOADING, {
                        isBasic: isBasic,
                        name: name,
                        ID: ID
                    }).appendTo(slots);
                } else {
                    slot = $.tmpl(SLOT_TMPL_LOADING, {
                        isBasic: isBasic,
                        name: name,
                        sizeText: parseSize(size),
                        ID: ID
                    }).appendTo(slots);
                }

                picQueue[ID] = slot;

                list.push({
                    ID: ID,
                    unfinished: true
                });
                self.show();

                imageList.trigger('image:select');

                return ID;
            },

            isInQueue: function(ID) {
                return picQueue[ID];
            },

            removeSlot: function(ID) {
                if (ID === undefined) {
                    return;
                }
                slots.find('[data-id="' + ID + '"]').remove();
                for (var i=list.length-1; i>=0; i--) {
                    if (list[i].ID == ID) {
                        list.splice(i, 1);
                        break;
                    }
                }
                if (list.length === 0) {
                    self.hide();
                }
                delete picQueue[ID];
                this.updateInfo();
            },
            finishSlot: function(real, ID) {
                if (!real) return;
                var slot = slots.find('[data-id="' + ID + '"]');
                if (slot.length < 1) {
                    $.tmpl(SLOT_TMPL, real).appendTo(slots);
                } else {
                    $.tmpl(SLOT_TMPL, real).insertAfter(slot);
                    slot.remove();
                }
                for (var i=list.length-1; i>=0; i--) {
                    if (list[i].ID === ID) {
                        list.splice(i, 1, real);
                        break;
                    }
                }
                this.updateInfo();
                this.saveImages(real);
            },
            errorSlot: function(error, ID) {
                var slot = slots.find('[data-id="' + ID + '"]');
                if (!error.isBasic) {
                    error.isBasic = false;
                }
                if (error.cb) {
                    error.retry = true;
                }
                if (slot.length < 1) {
                    $.tmpl(SLOT_TMPL_ERROR, error).appendTo(slots);
                } else {
                    $.tmpl(SLOT_TMPL_ERROR, error).insertAfter(slot);
                    slot.remove();
                }
                self.show();

                if (error.cb) {
                    slot = slots.find('[data-id="' + ID + '"]');
                    slot.find('a.image-retry').click(function(e) {
                        e.preventDefault();
                        error.cb();
                    });
                }

                error.unfinished = true;

                for (var i=list.length-1; i>=0; i--) {
                    if (list[i].ID === ID) {
                        list.splice(i, 1, error);
                        break;
                    }
                }
            },
            progressSlot: function(percentage, ID) {
                var ID = ID || id;
                var slot = slots.find('.slot[data-id="' + ID + '"]');
                slot.find('.percentage').text(percentage + '%');
                slot.find('.progress').css({
                    width: percentage + '%'
                });
            },
            updateInfo: function() {
                var num = 0, size = 0,
                    i, slot;

                for (i = list.length - 1; i>=0; i--) {
                    slot = list[i];
                    if (!slot.unfinished){
                        num += 1;
                        //size += slot.size;
                    }
                }

                if (num === list.length) {
                    imageList.trigger('image:uploadCompleted');
                }

                image_num.text(num);
                //total_size.text(parseSize(size));
            },
            saveImages: function(obj) {
                $.tmpl(IMAGE_ITEM_TMPL, obj).appendTo(imageList);
                imageList.show().trigger('image:saved');
                $('.submit-item').show();
                this.removeSlot(obj.ID);
            }
        };
    }();

    var sizeLimit = 1024 * 1000 * 5;
    var uploadArea = {
        // init function
        initDnd: function() {
            var that = this;
            var droppable = $('.drag-drop', document.getElementById('upload-area'));
            droppable[0].addEventListener('dragover', function(e) {
                e.stopPropagation();
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
            }, false);
            droppable[0].addEventListener('drop', function(e) {
                e.stopPropagation();
                e.preventDefault();

                var files = e.dataTransfer.files;
                for (var i=0, f; f=files[i]; i++) {
                    if (f.type.match(/image.*/)) {
                        that.dndUploadFile(f);
                    }
                }
            }, false);

            SI.Files.stylizeById('image_file');

            $('body').on('change','#image_file',function(e){
                var files = e.currentTarget.files;
                for (var i=0, f; f=files[i]; i++) {
                    if (f.type.match(/image.*/)) {
                        that.dndUploadFile(f);
                    }
                }
            });
        },
        initUploadify: function() {
            var data = {
                eid: eid
            };
            //data[postParams.siteCookie.name] = postParams.siteCookie.value;
            $('#image_file').uploadify({
                queueID: null,
                uploader: '/static/swf/uploadify.swf',
                expressInstall: '/static/swf/expressInstall.swf',
                script: upload_photo_url,
                fileDataName: 'upload_file',
                scriptData: data,
                auto: true,
                multi: true,
                buttonText: '',
                buttonImg: '/static/img/upload-pic-btn.png',
                width: 90,
                height: 22,
                rollover: true,
                sizeLimit: sizeLimit,
                fileExt: '*.jpeg;*.gif;*.jpg;*.png;',
                fileDesc: '图片文件',
                onError: function(e, ID, fileObj, errorObj) {
                    var error = {
                        name: fileObj.name,
                        sizeText: parseSize(fileObj.size),
                        size: fileObj.size,
                        ID: ID
                    };
                    if (errorObj.type == 'HTTP' || errorObj.type === 'IO') {
                        error.msg = '网络错误';
                        imageTable.errorSlot(error, ID);
                    }
                    if (errorObj.type == 'File Size') {
                        error.msg = '图片太大';
                        imageTable.errorSlot(error, ID);
                    }
                },
                onSelect: function(e, ID, fileObj) {
                    imageTable.addSlot(fileObj.name, fileObj.size, ID);
                },
                onOpen: function(e, ID, fileObj) {
                    if (!imageTable.isInQueue(ID)) {
                        $('#image_file').uploadifyCancel(ID);
                    }
                },
                onCancel: function(e, ID, fileObj, data) {
                    return false;
                },
                onComplete: function(e, ID, fileObj, response, data) {
                    var response = $.parseJSON(response);
                    if (response.err !== 'ok') {
                        var error = {
                            name: fileObj.name,
                            sizeText: parseSize(fileObj.size),
                            size: fileObj.size,
                            ID: ID,
                            msg: response.err
                        };
                        imageTable.errorSlot(error, ID);
                    }

                    console.log(response.err);
                    //var photo = response.photo;
                    var real = {
                        name: fileObj.name,
                        /*
                        sizeText: parseSize(photo.file_size),
                        size: photo.file_size,*/
                        thumb: response.url,
                        ID: response.id
                    };
                    imageTable.finishSlot(real, ID);
                },
                onProgress: function(e, ID, fileObj, data) {
                    imageTable.progressSlot(data.percentage, ID);
                    return false;
                },
                onSWFReady: function() {
                }
            });
        },
        initBasic: function() {
            var that = this;
            Do('iframe-post-form', function() {
                var fileInput = $('#image_file'),
                    form = $('#upload-area');

                fileInput.change(function(e) {
                    var name = (/([^[\\\/]*)$/.exec(fileInput[0].value) || [])[1],
                        new_id = imageTable.addSlot(name); // basic

                    if (new_id === undefined) {
                        return;
                    }
                    that.basicUploadFile(new_id, form, fileInput);
                });
            });
        },
        basicUploadFile: function(new_id, form, fileInput) {
            var suffix = /\.([^\.]+)$/,
                fileName = /([^\\\/]*)$/,
                options = {
                json: true,
                iframeID: 'iframe-post-' + new_id,
                post: function() {
                    var hash = {
                            'jpeg': 1,
                            'png': 1,
                            'jpg': 1,
                            'gif': 1
                        };
                    var path = fileInput[0].value;
                    if (!hash[(suffix.exec(path) || [])[1]]) {
                        var error = {
                            name: (fileName.exec(path) || [])[1],
                            ID: new_id,
                            sizeText: '',
                            msg: '请选择图片文件(JPG/JPEG, PNG,或GIF)'
                        };
                        imageTable.errorSlot(error, new_id);
                        fileInput.val('');
                        return false;
                    }
                },
                complete: function(response) {
                    var path = fileInput[0].value,
                        name = (fileName.exec(path) || [])[1];
                    if (response === null) {
                        var error = {
                            name: name,
                            ID: new_id,
                            sizeText: '',
                            msg: '网络错误',
                            cb: function() {
                                var returnNewId;
                                imageTable.removeSlot(new_id);
                                returnNewId = imageTable.addSlot(name, undefined, new_id);
                                if (returnNewId === undefined) {
                                    return;
                                }
                                form.trigger('submit');
                            }
                        };
                        imageTable.errorSlot(error, new_id);
                        return;
                    }
                    if (response.r !== 0) {
                        var error = {
                            name: name,
                            ID: new_id,
                            sizeText: '',
                            msg: response.err
                        };
                        imageTable.errorSlot(error, new_id);
                        fileInput.val('');
                        return;
                    }
                    //var photo = response.photo;
                    var real = {
                        name: name,
                        /*
                        sizeText: parseSize(photo.file_size),
                        size: photo.file_size,
                        seq: photo.seq,*/
                        thumb: response.url,
                        ID: response.id 
                    };
                    imageTable.finishSlot(real, new_id);
                }
            };
            form.unbind('submit');
            form.iframePostForm(options);
            form.trigger('submit');
        },
        // upload function
        dndUploadFile: function(file) {
            var new_id = imageTable.addSlot(file.fileName, file.fileSize);

            if (new_id === undefined) {
                return;
            }

            if (file.fileSize > sizeLimit) {
                var error = {
                    name: file.fileName,
                    sizeText: parseSize(file.fileSize),
                    size: file.fileSize,
                    ID: new_id,
                    msg: '图片不超过5M'
                };
                imageTable.errorSlot(error, new_id);
                return;
            }
            var formData = new FormData();
            formData.append('upload_file', file);
            formData.append('eid', eid);
            var xhr = new XMLHttpRequest();

            xhr.open('POST', upload_photo_url, true);
            xhr.onreadystatechange = function(e) {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) { // success
                        var response = $.parseJSON(xhr.responseText);
                        if (response.err !== 'ok') {
                            var error = {
                                name: file.fileName,
                                sizeText: parseSize(file.fileSize),
                                size: file.fileSize,
                                ID: new_id,
                                msg: response.err
                            };
                            imageTable.errorSlot(error, new_id);
                            return;
                        }
                        //var photo = response.photo;
                        var real = {
                            name: file.fileName,
                            thumb: response.url,
                            ID: response.id
                        }
                        imageTable.finishSlot(real, new_id);
                    } else { // error
                        var error = {
                            name: file.fileName,
                            sizeText: parseSize(file.fileSize),
                            size: file.fileSize,
                            ID: new_id,
                            msg: '网络错误',
                            cb: function() {
                                xhr.open('POST', upload_photo_url, true);
                                xhr.send(formData);
                            }
                        };
                        imageTable.errorSlot(error, new_id);
                    }
                }
            };
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    var percentage = parseInt((e.loaded/e.total)*100, 10);
                    imageTable.progressSlot(percentage, new_id);
                }
            };
            xhr.send(formData);
        }
    };

    var app = {
        tmplData: {},
        init: function(isBasic) {
            var tmplData = this.tmplData;
            tmplData.eid = eid;
            if (Modernizr.draganddrop && (typeof FormData !== 'undefined')) {
                tmplData.dnd = true;
            } else {
                tmplData.dnd = false;
            }

            var flashVersion = swfobject.getFlashPlayerVersion();
            if (flashVersion.major > 9) {
                tmplData.flash = true;
            } else {
                tmplData.flash = false;
            }
            
            if (isBasic) {
                tmplData.dnd = false;
                tmplData.flash = false;
                tmplData.basic = true;
            } else {
                tmplData.basic = false;
            }
            
            $(container).html($.tmpl(IMAGE_DLG_TMPL, tmplData));
            if (!$('html').hasClass('ua-mac')) {
                $('.upload-tip i').text('ctrl');
            }
            return this;
        },
        initWidgets: function() {
            var tmplData = this.tmplData;
            if (tmplData.dnd) {
                uploadArea.initDnd();
            }/*
            if (tmplData.flash) {
                uploadArea.initUploadify();
            }
            if (!tmplData.flash) {
                uploadArea.initBasic();
            }
            */
            imageTable.init();

            return this;
        },
        bindEvents: function() {
            var uploadAlter = $('.upload-alternative', document.getElementById('image_upload'));

            uploadAlter.delegate('.upload-basic', 'click', function(e) {
                e.preventDefault();
                ImageUpload({
                    container: container,
                    isBasic: true,
                    upload_photo_url: upload_photo_url,
                    eid: eid
                });
            });
            uploadAlter.delegate('.upload-multi', 'click', function(e) {
                e.preventDefault();
                ImageUpload({
                    container: container,
                    upload_photo_url: upload_photo_url,
                    eid: eid
                });
            });
            return this;
        }
    };

    app.init(isBasic).initWidgets().bindEvents();
}

if (!window.SI) { var SI = {}; };
SI.Files =
{
    htmlClass : 'SI-FILES-STYLIZED',
    fileClass : 'file',
    wrapClass : 'cabinet',
    
    fini : false,
    able : false,
    init : function()
    {
        this.fini = true;
        
        var ie = 0 //@cc_on + @_jscript_version
        if (window.opera || (ie && ie < 5.5) || !document.getElementsByTagName) { return; } // no support for opacity or the DOM
        this.able = true;
        
        var html = document.getElementsByTagName('html')[0];
        html.className += (html.className != '' ? ' ' : '') + this.htmlClass;
    },
    
    stylize : function(elem)
    {
        if (!this.fini) { this.init(); };
        if (!this.able) { return; };
        
        elem.parentNode.file = elem;
        elem.parentNode.onmousemove = function(e)
        {
            if (typeof e == 'undefined') e = window.event;
            if (typeof e.pageY == 'undefined' &&  typeof e.clientX == 'number' && document.documentElement)
            {
                e.pageX = e.clientX + document.documentElement.scrollLeft;
                e.pageY = e.clientY + document.documentElement.scrollTop;
            };

            var ox = oy = 0;
            var elem = this;
            if (elem.offsetParent)
            {
                ox = elem.offsetLeft;
                oy = elem.offsetTop;
                while (elem = elem.offsetParent)
                {
                    ox += elem.offsetLeft;
                    oy += elem.offsetTop;
                };
            };

            var x = e.pageX - ox;
            var y = e.pageY - oy;
            var w = this.file.offsetWidth;
            var h = this.file.offsetHeight;

            this.file.style.top     = y - (h / 2)  + 'px';
            this.file.style.left    = x - (w - 30) + 'px';
        };
    },
    
    stylizeById : function(id)
    {
        this.stylize(document.getElementById(id));
    },
    
    stylizeAll : function()
    {
        if (!this.fini) { this.init(); };
        if (!this.able) { return; };
        
        var inputs = document.getElementsByTagName('input');
        for (var i = 0; i < inputs.length; i++)
        {
            var input = inputs[i];
            if (input.type == 'file' && input.className.indexOf(this.fileClass) != -1 && input.parentNode.className.indexOf(this.wrapClass) != -1)
            {
                this.stylize(input);
            };
        };
    }
};
