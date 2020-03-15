var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var player;
var just_ready = true;
var socket = io();

function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '360',
        width: '640',
        videoId: '',
        playerVars: {
            enablejsapi: 1,
            loop: 1,
            cc_lang_pref: 'en',
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    $.ajax({
        url: "/get_play_detail",
        type: 'GET',
        success: function(res) {
            event.target.loadVideoById({
                'videoId': res['vid'],
                'startSeconds': res['seek'],
                'suggestedQuality': 'large'
            })
            if(!res['playing']){
                event.target.pauseVideo()
            } else {
                event.target.playVideo()
            }
        }
    });
}
function onPlayerStateChange(event) {
    if(!just_ready) {
        socket.emit('player_state_changed', 
        { 
            seek: player.getCurrentTime(),
            url: player.getVideoUrl(),
            playing: event.data == YT.PlayerState.PLAYING,
        }
    );
    }
    just_ready = false
}

function matchYoutubeUrl(url) {
    var p = /^(?:https?:\/\/)?(?:m\.|www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$/;
    if(url.match(p)){
        return url.match(p)[1];
    }
    return false;
}

function check_and_apply(sender){
    var url = $('#txt').val();
    var id = matchYoutubeUrl(url);
    if(id!=false){
        player.loadVideoById(id, 0, "large")
    }else{
        alert('Incorrect URL');
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
