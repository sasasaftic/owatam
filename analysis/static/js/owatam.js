// Create the XHR object.

var timer = 0;
var element_id = "body";
var cookie_id;

function createCORSRequest(method, url) {
    var xhr = new XMLHttpRequest();

    if ("withCredentials" in xhr) {
        // XHR for Chrome/Firefox/Opera/Safari.
        xhr.open(method, url, true);
    } else if (typeof XDomainRequest != "undefined") {
        // XDomainRequest for IE.
        xhr = new XDomainRequest();
        xhr.open(method, url, true);
    } else {
        // CORS not supported.
        xhr = null;
    }
    //xhr.withCredentials = true;
    return xhr;
}

// Helper method to parse the title tag from the response.
function getTitle(text) {
    return text.match('<title>(.*)?</title>')[1];
}

// Make the actual CORS request.
function makeCorsRequest(data) {
    // All HTML5 Rocks properties support CORS.
    var url = 'http://cashiermobile.com:8080/send_data';

    var xhr = createCORSRequest('POST', url);

    if (!xhr) {
        alert('CORS not supported');
        return;
    }

    // Response handlers.
    xhr.onload = function () {
        var text = xhr.responseText;
        //alert('Response from CORS request to ' + url + ': ' + text);
    };

    xhr.onerror = function () {
        alert('Woops, there was an error making the request.');
    };
    xhr.send(data);
}

// cookie functions

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toGMTString();
    document.cookie = cname + "=" + cvalue + "; expires=" + expires + "; path=" + "/;";
}


function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i].trim();
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}

function UserTrack(){

    var active_elements = (document.querySelectorAll( ":hover" ));
    var curr_element_id = element_id;
    for (var i=active_elements.length; i>=0; i--){
        var active_element = active_elements[i];
        if(typeof active_element != 'undefined'){
            if(active_elements.tagName == "BODY"){
                curr_element_id = "body";
                break;
            }
            if(active_element.id){
                curr_element_id = active_element.id;
                break;
            }

            if(active_element.class){
                curr_element_id = active_element.class;
                break;
            }
        }
    }
    if (curr_element_id != element_id){
        element_id = curr_element_id;
        var d = new Date();
        if(getCookie(page_id)){
            cookie_id = getCookie(page_id);
        }else{
            cookie_id = d.getTime().toString() + page_id;
            setCookie(page_id, cookie_id, 365)
        }
        var call = new FormData();
        call.append("name_id","scroll_call");
        call.append("hostname", location.hostname);
        call.append("title", document.title);
        call.append("element", element_id);
        call.append("host", window.location.pathname);
        call.append("cookie_id", cookie_id);
        call.append("date", d.getTime());
        makeCorsRequest(call);
    }
}

window.onload=function(){
    //cookie exists, this is not user's first visit
    var d = new Date();
    if(getCookie(page_id)){
        cookie_id = getCookie(page_id);
    }else{
        cookie_id = d.getTime().toString() + page_id;
        setCookie(page_id, cookie_id, 365);
    }
    var call = new FormData();
    call.append("name_id","first_call");
    call.append("hostname", location.hostname);
    call.append("title", document.title);
    call.append("host", window.location.pathname);
    call.append("cookie_id", cookie_id);
    call.append("date", d.getTime());
    makeCorsRequest(call);
};

window.onscroll = function(){
    if (timer){
        clearTimeout(timer);
    }
    timer = setTimeout(UserTrack, 1000);
}

window.onunload=function(){
    var d = new Date();
    var call = new FormData();
    call.append("name_id","end_call");
    call.append("hostname", location.hostname);
    call.append("title", document.title);
    call.append("host", window.location.pathname);
    call.append("cookie_id", cookie_id);
    call.append("date", d.getTime());
    makeCorsRequest(call);
}
