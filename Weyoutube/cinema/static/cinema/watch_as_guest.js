var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var ua = window.navigator.userAgent;
var iOS = !!ua.match(/iPad/i) || !!ua.match(/iPhone/i);
var webkit = !!ua.match(/WebKit/i);
var iOSSafari = iOS && webkit && !ua.match(/CriOS/i);

var player;
var player_is_ready = false;
var socket = io();
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '360',
        width: '640',
        videoId: '',
        playerVars: {
            enablejsapi: 1,
            controls: 0,
            loop: 1,
            cc_lang_pref: 'en',
            rel: 0,
        },
        events: {
            'onReady': onPlayerReady,
        }
    });
}

function onPlayerReady(event) {
    $.ajax({
        url: "/get_play_detail",
        type: 'GET',
        success: function(res) {
            player.loadVideoById({
                'videoId': res['vid'],
                'startSeconds': res['seek'],
                'suggestedQuality': 'large'
            })
            if(res['playing']) {
                player.playVideo()
            } else {
                player.pauseVideo()
            }
            player_is_ready = true
        }
    });
}
function isString(o) {
    return typeof o == "string" || (typeof o == "object" && o.constructor === String);
}
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
async function until(fn){
    while(!fn()){
        await sleep(0)
    }
}
async function apply_update(data) {
    await until(() => isString(player.getVideoUrl()) == true)
    if(player.getVideoUrl().includes(data['vid'])){
        if(Math.abs(data['seek'] - player.getCurrentTime()) > 5){
            player.seekTo(data['seek'], true)    
        }
        if(data['playing'] && player.getPlayerState() != 1) {
            player.playVideo()
        } else if(!data['playing'] && player.getPlayerState() == 1) {
            player.pauseVideo()
        }
    } else {
        if(!iOSSafari){
            player.loadVideoById({
                'videoId': data['vid'],
                'startSeconds': data['seek'],
                'suggestedQuality': 'large'
            })
        } else {
            alert('Video changed. Because of the iOS restriction, website cannot play the video automatically, you would need to press the video to play it.')
            location.reload()
        }
    }
}

socket.on('connect', function(data) {
    socket.emit('join', 'I\'m in');
});
socket.on('people_changed_response', function(data) {
    $("#roster").html(data)
});
socket.on('room_dismissed', function(data) {
    alert(data)
    window.location.href = '/'
});
socket.on('player_state_changed_response', async (data) => {
    apply_update(data);
})