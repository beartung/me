function read_notify(blog_id){
    $.post("/j/read_notify",{bid:blog_id},function(result){
        $("#notify-num").html(result.num);
        if (result.num == 0){
            $("#notify-num").removeClass('label-important');
        }
    });
    return false;
};
function add_tag(input_id, t){
    $(input_id)[0].value = $(input_id)[0].value + ' ' + t;
    return false;
};
function like_card(card_id){
    $.post("/j/like",{cid:card_id},function(result){
        if (result.err == 'ok'){
            $('#card_'+ card_id + '_likers').html(result.inner_html);
            $('#btn_' + card_id + '_like').html('<i style="color:#d14836" class="icon-heart"></i> 已收藏');
            $('#btn_' + card_id + '_like').addClass('disabled');
            $('#btn_' + card_id + '_like').removeClass('btn-danger');
            $('#num_' + card_id + '_like').html(result.like_num);
            $('#num_' + card_id + '_like').show();
        }
    });
    return false;
};
function add_tags(card_id, cate){
    $("#tag_dialog_" + card_id).modal('hide');
    ts = $("#tags_content_" + card_id)[0].value;
    $.post("/j/tag",{cid:card_id, tags:ts, cate:cate},function(result){
        if (result.err == 'ok'){
            if (cate == 'small'){
                $('#tags_small_div_' + card_id).html(result.inner_html);
            }else{
                $('#tags_div_' + card_id).html(result.inner_html);
            }
        }
    });
    return false;
};
function comment_card(card_id, comment_input_id){
    ct = $('#'+comment_input_id)[0].value;
    //$("#comment_dialog_" + card_id).modal('hide');
    $.post("/j/comment",{cid:card_id, content:ct},function(result){
        if (result.err == 'ok'){
            $('#card_comments_div').html(result.html);
        }
    });
    return false;
};

function uncomment_card(card_id, comment_id){
    $.post("/j/uncomment",{cid:card_id, comment_id:comment_id},function(result){
        if (result.err == 'ok'){
            $('#card_comments_div').html(result.html);
        }
    });
    return false;
};

function vote_card(card_id, award_id){
    $("#vote_dialog_" + card_id).modal('hide');
    $.post("/j/vote",{cid:card_id, aid:award_id},function(result){
        if (result.err == 'ok'){
            $('#btn_' + card_id + '_vote').addClass('disabled');
            $('#btn_' + card_id + '_vote').html('<i style="color:#FFF" class="icon-star"></i> 已投票');
        }
    });
    return false;
};

function comment_photo(photo_id, comment_input_id){
    ct = $('#'+comment_input_id)[0].value;
    //$("#comment_dialog_" + card_id).modal('hide');
    $.post("/j/event/comment_photo",{pid:photo_id, content:ct},function(result){
        if (result.err == 'ok'){
            $('#photo_comments_div').html(result.html);
        }
    });
    return false;
};

function like_photo(photo_id){
    $.post("/j/event/like_photo",{pid:photo_id},function(result){
        if (result.err == 'ok'){
            $('#photo_likers_div').html(result.html);
            $('#photo-plus-button').removeClass('btn-primary').addClass('disabled');
            $('#photo-plus-button')[0].value = '已+ 1';
        }
    });
    return false;
};

function request_card_photo(card_id){
    $.post("/j/request_photo",{cid:card_id},function(result){
        if (result.err == 'ok'){
            alert('请求已经发送，静候佳音吧！  <(￣︶￣)>');
        }
    });
    return false;
};
function request_card_change_photo(card_id){
    $.post("/j/request_change_photo",{cid:card_id},function(result){
        if (result.err == 'ok'){
            alert('请求已经发送，静候佳音吧！  <(￣︶￣)>');
        }
    });
    return false;
};

function like_blog(blog_id, single){
    $.post("/j/blog/like",{bid:blog_id, single:single},function(result){
        if (result.err == 'ok'){
            $('#blog-line-' + blog_id).html(result.inner_html);
        }
    });
    return false;
};

function unlike_blog(blog_id, single){
    $.post("/j/blog/unlike",{bid:blog_id, single:single},function(result){
        if (result.err == 'ok'){
            $('#blog-line-' + blog_id).html(result.inner_html);
        }
    });
    return false;
};

function comment_blog(blog_id){
    var formData = new FormData($('#comment_form_'+blog_id)[0]);
    console.log(formData)
    $.ajax({
        url:"/j/blog/comment",
        type:"POST",
        success: function(result){
            if (result.err == 'ok'){
                $('#blog-line-' + blog_id).html(result.inner_html);
            }
        },
        data: formData,
        cache: false,
        contentType: false,
        processData: false
    });
    return false;
};

function uncomment_blog(blog_id, comment_id, single){
    var c = confirm("真的要删除这条回复吗？");
    if (c){
        $.post("/j/blog/uncomment",{bid:blog_id, single:single, comment_id:comment_id},function(result){
            if (result.err == 'ok'){
                $('#blog-line-' + blog_id).html(result.inner_html);
            }
        });
    }
    return false;
};

function show_blog_content(blog_id){
    $('#blog-content-'+blog_id).show();
    $('#btn-hided-'+blog_id).hide();
    return false;
};
 
/*
$('.blog-comment-input').bind("keyup", function(e){
    if(e.keyCode == 13){
        single = window.location.href.split('/')[3] == 'update';
        blog_id = this.id.split('_')[1];
        return comment_blog(blog_id, this.id, single);
    }
    return false;
});
*/

function ask_card(card_id, question_input_id){
    ct = $('#'+question_input_id)[0].value;
    ay = $("#anonymous")[0].checked ? '1' : '';
    $.post("/j/ask",{cid:card_id, content:ct, anonymous:ay},function(result){
        if (result.err == 'ok'){
            $('#card_answers_div').html(result.html);
        }
    });
    return false;
};

function add_emoticon(input_id, t){
    $(input_id)[0].value = $(input_id)[0].value + ' ' + t;
    return false;
};

function uncomment_photo(photo_id, comment_id){
    var c = confirm("真的要删除这条回复吗？");
    if (c){
        $.post("/j/event/uncomment_photo",{pid:photo_id, comment_id:comment_id},function(result){
            if (result.err == 'ok'){
                $('#photo_comments_div').html(result.html);
            }
        });
    }
    return false;
};

function rec(type, id){
    $.post("/j/rec",{type:type, id:id},function(result){
        alert("已经成功推荐到广播〜");
    });
    return false;
};
