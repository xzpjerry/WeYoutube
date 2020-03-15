var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var player;
var just_ready = true;
var socket = io();
socket.on('connect', function(data) {
    socket.emit('join', 'I\'m in');
});
socket.on('people_changed_response', function(data) {
    $("#roster").html(data)
});
socket.on('returning_secret', function(data) {
    $('#secret').append(data)
  });
socket.on('room_dismissed', function(data) {
    if(confirm(data)){
        window.location.href = '/'
    }
});
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '360',
        width: '640',
        videoId: '',
        playerVars: {
            enablejsapi: 1,
            loop: 1,
            cc_lang_pref: 'en',
            rel: 0,
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
        update_progress();
        window.setInterval("update_progress();", 5000);
    }
    just_ready = false
}

function update_progress() {
    console.log('Updateing progress')
    socket.emit('player_state_changed', 
        { 
            seek: player.getCurrentTime(),
            url: player.getVideoUrl(),
            playing: player.getPlayerState() == 1,
        }
    );
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

