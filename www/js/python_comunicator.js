function load_document(doc){
    eel.load_document(doc)
}

function next_word(){
    eel.next_word()
}

function prev_word(){
    eel.prev_word()
}

function select_transcript(transcript, ind){
    eel.stop_previousword_timer() // STOP from_prevword timer clicking on list
    //console.log(transcript, ind)
    //transcript = transcript.textContent

    //var transcript_area = document.getElementById("transcript_textarea")
    //var full_transcript = transcript_area.innerHTML
    
    var text_input = document.getElementById("text_input")

    // if (full_transcript == "")
    //     full_transcript += transcript
    // else
    //     full_transcript += " " + transcript
    
    // transcript_area.innerHTML = full_transcript

    text_input.value = ""
    $("#text_input").focus();

    eel.set_current_word_transcription(transcript, "LIST_"+ind)

}

function send_transcript_by_ok(mode){
    //var transcript_area = document.getElementById("transcript_textarea")
    var transcript = document.getElementById("text_input")
    

    //var full_transcript = transcript_area.innerHTML
    var word = transcript.value

    if (word.length>0){
        //full_transcript = full_transcript + " " + word
        //full_transcript = full_transcript.trimStart()
        
        //transcript_area.innerHTML = full_transcript

        transcript.value = ""
        $("#text_input").focus();

        //console.log(full_transcript)
        //eel.set_current_line_transcription(full_transcript)
        eel.set_current_word_transcription(word, mode)
    }
}

eel.expose(show_transcripts_list)
function show_transcripts_list(transcripts_list){
    var inscreen_keywords = document.getElementById("keyword_list");
    $(inscreen_keywords).empty();

    var max_iter = transcripts_list.length
    if (max_iter > max_transcripts_options)
        max_iter = max_transcripts_options

    for (i=0; i<max_iter; i++) {
        text = transcripts_list[i]
        $("<li onclick=\"select_transcript('"+text+"', '"+(i+1)+"')\">"+text+"</li>").appendTo(inscreen_keywords)
   }
}


eel.expose(update_transcription_area)
function update_transcription_area(transcription){
    var transcript_area = document.getElementById("transcript_textarea");

    transcript_area.innerHTML = transcription

}

eel.expose(show_current_word_img)
function show_current_word_img(img_path){
    var timestamp = new Date().getTime();
    document.getElementById("img_word").src=img_path+"?t="+timestamp;

    //set_focus_on_textinput();
    window.new_transcriptiKCon = true;
}

eel.expose(show_current_line_img)
function show_current_line_img(img_path){
    var timestamp = new Date().getTime();
    document.getElementById("img_row").src=img_path+"?t="+timestamp;
}

function set_focus_on_textinput(){
    text_input = document.getElementById("text_input");
    text_input.focus();
    text_input.select();
}

function start_instert_transcription(){
    transcript = document.getElementById("text_input").value;
    
    if (transcript == "" ){
        eel.stop_previousword_timer()
    }

}

document.addEventListener('keydown', function(event) {
    if(event.key == "ArrowLeft") {
        //alert('Left was pressed');
        prev_word();
    }
    else if(event.key == "ArrowRight") {
        next_word();
    }
});